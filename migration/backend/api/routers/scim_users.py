"""
SCIM 2.0 Users endpoint
Implements SCIM protocol for user provisioning from Entra ID
Reference: https://datatracker.ietf.org/doc/html/rfc7644
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from backend.db import get_db
from backend.db.models import User
from backend.auth import require_admin, get_current_user_groups

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# SCIM Models
# ============================================================================

class SCIMEmail(BaseModel):
    """SCIM Email object"""
    value: EmailStr
    type: Optional[str] = "work"
    primary: bool = True


class SCIMName(BaseModel):
    """SCIM Name object"""
    formatted: Optional[str] = None
    familyName: Optional[str] = None
    givenName: Optional[str] = None


class SCIMUserResource(BaseModel):
    """SCIM User Resource"""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    id: Optional[str] = None
    externalId: Optional[str] = None
    userName: EmailStr
    name: Optional[SCIMName] = None
    displayName: Optional[str] = None
    emails: List[SCIMEmail]
    active: bool = True
    groups: Optional[List[dict]] = []
    meta: Optional[dict] = None


class SCIMUserPatch(BaseModel):
    """SCIM User Patch request"""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]
    Operations: List[dict]


class SCIMListResponse(BaseModel):
    """SCIM List Response"""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    totalResults: int
    startIndex: int = 1
    itemsPerPage: int
    Resources: List[SCIMUserResource]


class SCIMError(BaseModel):
    """SCIM Error Response"""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:Error"]
    status: str
    detail: str


# ============================================================================
# Helper Functions
# ============================================================================

def user_to_scim(user: User) -> SCIMUserResource:
    """Convert User model to SCIM User Resource"""
    return SCIMUserResource(
        id=str(user.id),
        userName=user.email,
        name=SCIMName(
            formatted=user.name,
            givenName=user.name.split()[0] if user.name else None,
            familyName=user.name.split()[-1] if user.name and len(user.name.split()) > 1 else None
        ),
        displayName=user.name,
        emails=[SCIMEmail(value=user.email, primary=True)],
        active=user.is_active,
        groups=[],
        meta={
            "resourceType": "User",
            "created": user.created_at.isoformat() if user.created_at else None,
            "lastModified": user.updated_at.isoformat() if user.updated_at else None,
            "location": f"/scim/v2/Users/{user.id}"
        }
    )


def scim_error_response(status_code: int, detail: str) -> SCIMError:
    """Create SCIM error response"""
    return SCIMError(
        status=str(status_code),
        detail=detail
    )


# ============================================================================
# SCIM Endpoints
# ============================================================================

@router.get("/Users", response_model=SCIMListResponse)
async def list_users(
    startIndex: int = Query(1, ge=1),
    count: int = Query(100, ge=1, le=100),
    filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    List users with pagination and filtering
    
    SCIM Filters supported:
    - userName eq "user@example.com"
    - externalId eq "external-id"
    """
    # Require admin access
    require_admin(user_groups)
    
    try:
        query = db.query(User)
        
        # Apply filter if provided
        if filter:
            # Simple filter parsing (userName eq "value")
            if "userName eq" in filter:
                email = filter.split('"')[1]
                query = query.filter(User.email == email)
            elif "externalId eq" in filter:
                # ExternalId not implemented in basic User model
                # Could be added as extension field
                pass
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (startIndex - 1)
        users = query.offset(offset).limit(count).all()
        
        # Convert to SCIM resources
        resources = [user_to_scim(user) for user in users]
        
        return SCIMListResponse(
            totalResults=total,
            startIndex=startIndex,
            itemsPerPage=len(resources),
            Resources=resources
        )
    
    except Exception as e:
        logger.exception(f"SCIM list users failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.get("/Users/{user_id}", response_model=SCIMUserResource)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Get a single user by ID
    """
    # Require admin access
    require_admin(user_groups)
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_to_scim(user)


@router.post("/Users", response_model=SCIMUserResource, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: SCIMUserResource,
    db: Session = Depends(get_db),
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Create a new user
    """
    # Require admin access
    require_admin(user_groups)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.userName).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    try:
        # Extract name from SCIM data
        name = user_data.displayName
        if not name and user_data.name:
            name = user_data.name.formatted
        
        # Create user
        new_user = User(
            email=user_data.userName,
            name=name,
            email_verified=True,
            is_active=user_data.active
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"SCIM: Created user {new_user.email} (ID: {new_user.id})")
        
        return user_to_scim(new_user)
    
    except Exception as e:
        db.rollback()
        logger.exception(f"SCIM create user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.put("/Users/{user_id}", response_model=SCIMUserResource)
async def update_user(
    user_id: str,
    user_data: SCIMUserResource,
    db: Session = Depends(get_db),
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Replace user (full update)
    """
    # Require admin access
    require_admin(user_groups)
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Update user fields
        user.email = user_data.userName
        user.name = user_data.displayName or (user_data.name.formatted if user_data.name else None)
        user.is_active = user_data.active
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"SCIM: Updated user {user.email} (ID: {user.id})")
        
        return user_to_scim(user)
    
    except Exception as e:
        db.rollback()
        logger.exception(f"SCIM update user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.patch("/Users/{user_id}", response_model=SCIMUserResource)
async def patch_user(
    user_id: str,
    patch_data: SCIMUserPatch,
    db: Session = Depends(get_db),
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Partial update user using SCIM PATCH operations
    """
    # Require admin access
    require_admin(user_groups)
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Process PATCH operations
        for operation in patch_data.Operations:
            op = operation.get("op", "").lower()
            path = operation.get("path", "")
            value = operation.get("value")
            
            if op == "replace":
                if path == "active" or (not path and "active" in operation):
                    user.is_active = value if value is not None else operation.get("active", user.is_active)
                elif path == "displayName":
                    user.name = value
                elif path == "userName":
                    user.email = value
            
            elif op == "add":
                # Handle add operations
                pass
            
            elif op == "remove":
                # Handle remove operations
                if path == "active":
                    user.is_active = False
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"SCIM: Patched user {user.email} (ID: {user.id})")
        
        return user_to_scim(user)
    
    except Exception as e:
        db.rollback()
        logger.exception(f"SCIM patch user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to patch user"
        )


@router.delete("/Users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Delete a user (or mark as inactive for soft delete)
    """
    # Require admin access
    require_admin(user_groups)
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Soft delete: mark as inactive
        user.is_active = False
        db.commit()
        
        logger.info(f"SCIM: Deleted (deactivated) user {user.email} (ID: {user.id})")
        
        return None
    
    except Exception as e:
        db.rollback()
        logger.exception(f"SCIM delete user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

