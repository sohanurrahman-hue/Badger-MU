"""
Authentication middleware for FastAPI
Validates JWT tokens from Entra ID and attaches user info to request state
"""
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.auth.sso import entra_auth

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware that validates tokens and enforces access control
    """
    
    # Public routes that don't require authentication
    PUBLIC_ROUTES = [
        "/",
        "/health",
        "/api/docs",
        "/api/redoc",
        "/openapi.json",
        "/auth/login",
        "/auth/callback",
        "/discovery",  # Open Badges discovery endpoint is public
    ]
    
    # Routes that require admin access
    ADMIN_ROUTES = [
        "/admin",
        "/scim/v2",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request and validate authentication
        """
        path = request.url.path
        
        # Skip authentication for public routes
        if any(path.startswith(route) for route in self.PUBLIC_ROUTES):
            return await call_next(request)
        
        # If auth is disabled (dev mode), attach mock user and continue
        if not entra_auth.enabled:
            request.state.user = {
                "id": "00000000-0000-0000-0000-000000000001",
                "email": "dev@badgeengine.local",
                "name": "Development User",
                "groups": ["Issuers", "Badge Admins"],
                "token_payload": {}
            }
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization header"}
            )
        
        # Parse Bearer token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme. Use 'Bearer'"}
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format"}
            )
        
        # Validate token
        try:
            token_payload = entra_auth.validate_token(token)
            
            # Get user groups (from token claims or Graph API)
            groups = entra_auth.extract_groups_from_token(token_payload)
            
            # If groups not in token, fetch from Graph API
            if not groups:
                try:
                    groups = await entra_auth.get_user_groups(token)
                except Exception as e:
                    logger.warning(f"Failed to fetch user groups: {str(e)}")
                    groups = []
            
            # Attach user info to request state
            request.state.user = {
                "id": token_payload.get("oid"),  # Object ID
                "email": token_payload.get("preferred_username") or token_payload.get("email"),
                "name": token_payload.get("name"),
                "groups": groups,
                "token_payload": token_payload
            }
            
            # Check admin access for admin routes
            if any(path.startswith(route) for route in self.ADMIN_ROUTES):
                if not entra_auth.check_admin_access(groups):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "detail": "Admin access required",
                            "required_groups": entra_auth.admin_groups
                        }
                    )
            
            # Continue to route handler
            return await call_next(request)
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.exception(f"Authentication error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Authentication error"}
            )


def get_current_user(request: Request) -> dict:
    """
    Dependency to get current authenticated user from request state
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.user


def get_current_user_groups(request: Request) -> list:
    """
    Dependency to get current user's groups
    """
    user = get_current_user(request)
    return user.get("groups", [])

