"""
Authentication router for Entra ID SSO
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

from backend.auth.sso import entra_auth
from backend.auth.middleware import get_current_user
from backend.db import get_db
from sqlalchemy.orm import Session
from backend.db.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None


class UserInfoResponse(BaseModel):
    """User info response"""
    id: str
    email: str
    name: str
    groups: list


@router.get("/login/entra")
async def login():
    """
    Initiate Entra ID login flow
    Redirects user to Microsoft login page
    """
    try:
        auth_url = entra_auth.get_auth_url()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.exception(f"Login initiation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate login"
        )



@router.get("/callback")
async def auth_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    OAuth callback endpoint
    Exchanges authorization code for access token
    """

    if error:
        logger.error(f"Auth callback error: {error} - {error_description}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_description or error
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    try:
        # Exchange code for token
        token_result = await entra_auth.exchange_code_for_token(code)
        
        # Get user info
        access_token = token_result.get("access_token")
        user_info = await entra_auth.get_user_info(access_token)
        
        # Create or update user in database
        user_email = user_info.get("mail") or user_info.get("userPrincipalName")
        user = db.query(User).filter(User.email == user_email).first()
        
        if not user:
            user = User(
                email=user_email,
                name=user_info.get("displayName"),
                email_verified=True,
                is_active=True
            )
            db.add(user)
        else:
            user.name = user_info.get("displayName")
            user.last_login = func.now()
        
        db.commit()
        db.refresh(user)
        
        # In production, you'd redirect to frontend with token
        # For now, return token response
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=token_result.get("expires_in", 3600),
            refresh_token=token_result.get("refresh_token"),
            id_token=token_result.get("id_token")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Auth callback processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return UserInfoResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        groups=current_user["groups"]
    )


@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint
    In a real implementation, you'd invalidate the session/token
    """
    # For Entra ID, logout is typically handled client-side
    # by clearing tokens and redirecting to Microsoft logout URL
    logout_url = f"https://login.microsoftonline.com/{entra_auth.tenant_id}/oauth2/v2.0/logout"
    
    return {
        "message": "Logged out successfully",
        "logout_url": logout_url
    }

