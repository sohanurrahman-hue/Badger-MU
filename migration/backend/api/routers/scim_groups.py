"""
SCIM 2.0 Groups endpoint
Implements SCIM protocol for group provisioning from Entra ID
Reference: https://datatracker.ietf.org/doc/html/rfc7644
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
import logging

from backend.db import get_db
from backend.auth import require_admin, get_current_user_groups

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# SCIM Group Models
# ============================================================================

class SCIMGroupMember(BaseModel):
    """SCIM Group Member"""
    value: str  # User ID
    ref: Optional[str] = None
    display: Optional[str] = None


class SCIMGroupResource(BaseModel):
    """SCIM Group Resource"""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
    id: Optional[str] = None
    externalId: Optional[str] = None
    displayName: str
    members: Optional[List[SCIMGroupMember]] = []
    meta: Optional[dict] = None


class SCIMGroupPatch(BaseModel):
    """SCIM Group Patch request"""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]
    Operations: List[dict]


class SCIMGroupListResponse(BaseModel):
    """SCIM Group List Response"""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    totalResults: int
    startIndex: int = 1
    itemsPerPage: int
    Resources: List[SCIMGroupResource]


# ============================================================================
# In-Memory Group Store (Replace with DB in production)
# ============================================================================
# Note: For MVP, we're using an in-memory store for groups
# In production, you should create a Groups table in the database

groups_store = {}


def create_issuer_group():
    """Create default Issuers group if it doesn't exist"""
    issuers_group_id = "issuers-group-default"
    if issuers_group_id not in groups_store:
        groups_store[issuers_group_id] = {
            "id": issuers_group_id,
            "displayName": "Issuers",
            "externalId": None,
            "members": []
        }
    return issuers_group_id


# Initialize default groups
create_issuer_group()


# ============================================================================
# Helper Functions
# ============================================================================

def group_to_scim(group_data: dict) -> SCIMGroupResource:
    """Convert group data to SCIM Group Resource"""
    return SCIMGroupResource(
        id=group_data["id"],
        externalId=group_data.get("externalId"),
        displayName=group_data["displayName"],
        members=[
            SCIMGroupMember(
                value=member["value"],
                display=member.get("display"),
                ref=f"/scim/v2/Users/{member['value']}"
            )
            for member in group_data.get("members", [])
        ],
        meta={
            "resourceType": "Group",
            "location": f"/scim/v2/Groups/{group_data['id']}"
        }
    )


# ============================================================================
# SCIM Group Endpoints
# ============================================================================

@router.get("/Groups", response_model=SCIMGroupListResponse)
async def list_groups(
    startIndex: int = Query(1, ge=1),
    count: int = Query(100, ge=1, le=100),
    filter: Optional[str] = None,
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    List groups with pagination and filtering
    
    SCIM Filters supported:
    - displayName eq "Issuers"
    - externalId eq "external-id"
    """
    # Require admin access
    require_admin(user_groups)
    
    try:
        # Get all groups
        all_groups = list(groups_store.values())
        
        # Apply filter if provided
        if filter:
            if "displayName eq" in filter:
                display_name = filter.split('"')[1]
                all_groups = [g for g in all_groups if g["displayName"] == display_name]
            elif "externalId eq" in filter:
                external_id = filter.split('"')[1]
                all_groups = [g for g in all_groups if g.get("externalId") == external_id]
        
        # Apply pagination
        total = len(all_groups)
        offset = startIndex - 1
        paginated_groups = all_groups[offset:offset + count]
        
        # Convert to SCIM resources
        resources = [group_to_scim(group) for group in paginated_groups]
        
        return SCIMGroupListResponse(
            totalResults=total,
            startIndex=startIndex,
            itemsPerPage=len(resources),
            Resources=resources
        )
    
    except Exception as e:
        logger.exception(f"SCIM list groups failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list groups"
        )


@router.get("/Groups/{group_id}", response_model=SCIMGroupResource)
async def get_group(
    group_id: str,
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Get a single group by ID
    """
    # Require admin access
    require_admin(user_groups)
    
    if group_id not in groups_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    return group_to_scim(groups_store[group_id])


@router.post("/Groups", response_model=SCIMGroupResource, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: SCIMGroupResource,
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Create a new group
    """
    # Require admin access
    require_admin(user_groups)
    
    try:
        # Generate ID
        group_id = str(uuid.uuid4())
        
        # Store group
        groups_store[group_id] = {
            "id": group_id,
            "displayName": group_data.displayName,
            "externalId": group_data.externalId,
            "members": [
                {
                    "value": member.value,
                    "display": member.display
                }
                for member in (group_data.members or [])
            ]
        }
        
        logger.info(f"SCIM: Created group '{group_data.displayName}' (ID: {group_id})")
        
        return group_to_scim(groups_store[group_id])
    
    except Exception as e:
        logger.exception(f"SCIM create group failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group"
        )


@router.put("/Groups/{group_id}", response_model=SCIMGroupResource)
async def update_group(
    group_id: str,
    group_data: SCIMGroupResource,
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Replace group (full update)
    """
    # Require admin access
    require_admin(user_groups)
    
    if group_id not in groups_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    try:
        # Update group
        groups_store[group_id] = {
            "id": group_id,
            "displayName": group_data.displayName,
            "externalId": group_data.externalId,
            "members": [
                {
                    "value": member.value,
                    "display": member.display
                }
                for member in (group_data.members or [])
            ]
        }
        
        logger.info(f"SCIM: Updated group '{group_data.displayName}' (ID: {group_id})")
        
        return group_to_scim(groups_store[group_id])
    
    except Exception as e:
        logger.exception(f"SCIM update group failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update group"
        )


@router.patch("/Groups/{group_id}", response_model=SCIMGroupResource)
async def patch_group(
    group_id: str,
    patch_data: SCIMGroupPatch,
    db: Session = Depends(get_db),
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Partial update group using SCIM PATCH operations
    Primarily used for adding/removing members
    """
    # Require admin access
    require_admin(user_groups)
    
    if group_id not in groups_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    try:
        group = groups_store[group_id]
        
        # Process PATCH operations
        for operation in patch_data.Operations:
            op = operation.get("op", "").lower()
            path = operation.get("path", "")
            value = operation.get("value")
            
            if op == "add":
                if "members" in path or not path:
                    # Add members
                    new_members = value if isinstance(value, list) else [value]
                    for member in new_members:
                        member_data = {
                            "value": member.get("value"),
                            "display": member.get("display")
                        }
                        # Check if member already exists
                        if not any(m["value"] == member_data["value"] for m in group["members"]):
                            group["members"].append(member_data)
                            logger.info(f"SCIM: Added member {member_data['value']} to group {group_id}")
            
            elif op == "remove":
                if "members" in path:
                    # Remove member(s)
                    # Path format: members[value eq "user-id"]
                    if "value eq" in path:
                        member_id = path.split('"')[1]
                        group["members"] = [m for m in group["members"] if m["value"] != member_id]
                        logger.info(f"SCIM: Removed member {member_id} from group {group_id}")
                    elif value:
                        # Value contains member to remove
                        member_id = value.get("value") if isinstance(value, dict) else value
                        group["members"] = [m for m in group["members"] if m["value"] != member_id]
            
            elif op == "replace":
                if path == "displayName":
                    group["displayName"] = value
                elif "members" in path or not path:
                    # Replace all members
                    group["members"] = [
                        {
                            "value": member.get("value"),
                            "display": member.get("display")
                        }
                        for member in (value if isinstance(value, list) else [value])
                    ]
        
        logger.info(f"SCIM: Patched group '{group['displayName']}' (ID: {group_id})")
        
        return group_to_scim(group)
    
    except Exception as e:
        logger.exception(f"SCIM patch group failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to patch group"
        )


@router.delete("/Groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    user_groups: List[str] = Depends(get_current_user_groups)
):
    """
    Delete a group
    """
    # Require admin access
    require_admin(user_groups)
    
    if group_id not in groups_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    try:
        group_name = groups_store[group_id]["displayName"]
        del groups_store[group_id]
        
        logger.info(f"SCIM: Deleted group '{group_name}' (ID: {group_id})")
        
        return None
    
    except Exception as e:
        logger.exception(f"SCIM delete group failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete group"
        )


@router.get("/ServiceProviderConfig")
async def get_service_provider_config():
    """
    SCIM Service Provider Configuration
    Describes SCIM capabilities
    """
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "documentationUri": "https://docs.badge-engine.example.com/scim",
        "patch": {
            "supported": True
        },
        "bulk": {
            "supported": False,
            "maxOperations": 0,
            "maxPayloadSize": 0
        },
        "filter": {
            "supported": True,
            "maxResults": 100
        },
        "changePassword": {
            "supported": False
        },
        "sort": {
            "supported": False
        },
        "etag": {
            "supported": False
        },
        "authenticationSchemes": [
            {
                "type": "oauthbearertoken",
                "name": "OAuth Bearer Token",
                "description": "Authentication scheme using the OAuth Bearer Token Standard",
                "specUri": "https://www.rfc-editor.org/rfc/rfc6750.html",
                "documentationUri": "https://docs.badge-engine.example.com/auth",
                "primary": True
            }
        ]
    }


@router.get("/ResourceTypes")
async def get_resource_types():
    """
    SCIM Resource Types endpoint
    """
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 2,
        "Resources": [
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "User",
                "name": "User",
                "endpoint": "/Users",
                "description": "User Account",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
            },
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "Group",
                "name": "Group",
                "endpoint": "/Groups",
                "description": "Group",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Group"
            }
        ]
    }


@router.get("/Schemas")
async def get_schemas():
    """
    SCIM Schemas endpoint
    """
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 2,
        "Resources": [
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:User",
                "name": "User",
                "description": "User Account"
            },
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
                "name": "Group",
                "description": "Group"
            }
        ]
    }

