"""
Microsoft Entra ID (Azure AD) SSO Authentication
Implements OpenID Connect (OIDC) authentication with group-based RBAC
"""
import os
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, status
from msal import ConfidentialClientApplication
import httpx

logger = logging.getLogger(__name__)


class EntraIDAuth:
    """
    Microsoft Entra ID authentication handler
    """
    
    def __init__(self):
        self.client_id = os.getenv("ENTRA_CLIENT_ID")
        self.client_secret = os.getenv("ENTRA_CLIENT_SECRET")
        self.tenant_id = os.getenv("ENTRA_TENANT_ID")
        self.redirect_uri = os.getenv("ENTRA_REDIRECT_URI", "http://localhost:8000/auth/callback")
        
        # Check if we're in development mode and should bypass auth
        # Auth is enabled if: (1) not in development mode, OR (2) all credentials are provided
        env = os.getenv("ENV", "development")
        has_credentials = all([self.client_id, self.client_secret, self.tenant_id])
        self.enabled = env != "development" or has_credentials
        
        if not self.enabled:
            logger.warning("Entra ID authentication disabled - running in development mode without credentials")
            self.app = None
            self.jwks_client = None
            self.authority = None
            self.scopes = []
            self.admin_groups = os.getenv("ENTRA_ADMIN_GROUPS", "").split(",")
            self.issuer_groups = os.getenv("ENTRA_ISSUER_GROUPS", "Issuers").split(",")
            return
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["User.Read", "GroupMember.Read.All"]
        
        # MSAL confidential client
        self.app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )
        
        # JWKS endpoint for token validation
        self.jwks_uri = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        self.jwks_client = PyJWKClient(self.jwks_uri)
        
        # Admin groups (users in these groups can access /admin endpoints)
        self.admin_groups = os.getenv("ENTRA_ADMIN_GROUPS", "").split(",")
        self.issuer_groups = os.getenv("ENTRA_ISSUER_GROUPS", "Issuers").split(",")
    
    def get_auth_url(self) -> str:
        """
        Generate authorization URL for login redirect
        """
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication is disabled in development mode"
            )
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state="badge_engine_state"
        )
        return auth_url
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        """
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication is disabled in development mode"
            )
        try:
            result = self.app.acquire_token_by_authorization_code(
                code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if "error" in result:
                logger.error(f"Token exchange error: {result.get('error_description')}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.get('error_description', 'Authentication failed')
                )
            
            return result
        except Exception as e:
            logger.exception(f"Token exchange failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange authorization code"
            )
    
    def validate_token(self, token: str) -> Dict:
        """
        Validate JWT access token from Entra ID
        In development mode without credentials, returns a mock token payload
        """
        if not self.enabled:
            # Return mock token payload for development
            logger.debug("Authentication disabled - returning mock token payload")
            return {
                "oid": "00000000-0000-0000-0000-000000000001",
                "preferred_username": "dev@badgeengine.local",
                "email": "dev@badgeengine.local",
                "name": "Development User",
                "groups": ["Issuers", "Badge Admins"],
                "roles": []
            }
        
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and validate token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"https://login.microsoftonline.com/{self.tenant_id}/v2.0",
                options={"verify_exp": True}
            )
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.exception(f"Token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
    
    async def get_user_groups(self, access_token: str) -> List[str]:
        """
        Retrieve user's group memberships from Microsoft Graph API
        """
        if not self.enabled:
            # Return mock groups for development
            return ["Issuers", "Badge Admins"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me/memberOf",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch user groups: {response.text}")
                    return []
                
                data = response.json()
                groups = [
                    group.get("displayName", "")
                    for group in data.get("value", [])
                    if group.get("@odata.type") == "#microsoft.graph.group"
                ]
                
                return groups
        except Exception as e:
            logger.exception(f"Failed to fetch user groups: {str(e)}")
            return []
    
    def extract_groups_from_token(self, token_payload: Dict) -> List[str]:
        """
        Extract group claims from token payload
        Requires group claims to be included in the token (configured in Entra ID)
        """
        # Groups can be in 'groups' claim (as IDs) or 'roles' claim
        groups = token_payload.get("groups", [])
        roles = token_payload.get("roles", [])
        
        return groups + roles
    
    def check_admin_access(self, groups: List[str]) -> bool:
        """
        Check if user has admin access based on group membership
        In development mode without credentials, always returns True
        """
        if not self.enabled:
            return True  # Allow all access in dev mode
        
        if not self.admin_groups or not self.admin_groups[0]:
            # No admin groups configured, allow all authenticated users
            return True
        
        return any(group in groups for group in self.admin_groups)
    
    def check_issuer_access(self, groups: List[str]) -> bool:
        """
        Check if user has issuer access based on group membership
        In development mode without credentials, always returns True
        """
        if not self.enabled:
            return True  # Allow all access in dev mode
        
        if not self.issuer_groups or not self.issuer_groups[0]:
            # No issuer groups configured, allow all authenticated users
            return True
        
        return any(group in groups for group in self.issuer_groups)
    
    async def get_user_info(self, access_token: str) -> Dict:
        """
        Get user information from Microsoft Graph API
        """
        if not self.enabled:
            # Return mock user info for development
            return {
                "id": "00000000-0000-0000-0000-000000000001",
                "mail": "dev@badgeengine.local",
                "userPrincipalName": "dev@badgeengine.local",
                "displayName": "Development User"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch user info: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to fetch user information"
                    )
                
                return response.json()
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to fetch user info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user information"
            )


# Singleton instance
entra_auth = EntraIDAuth()


def require_admin(user_groups: List[str]):
    """
    Dependency to check admin access
    Raises HTTPException if user doesn't have admin access
    """
    if not entra_auth.check_admin_access(user_groups):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. User must be in one of the admin groups."
        )


def require_issuer(user_groups: List[str]):
    """
    Dependency to check issuer access
    Raises HTTPException if user doesn't have issuer access
    """
    if not entra_auth.check_issuer_access(user_groups):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Issuer access required. User must be in the 'Issuers' group."
        )

