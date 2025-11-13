"""
OAuth2 scope validation for Open Badges v3.0 API
Reference: https://purl.imsglobal.org/spec/ob/v3p0/scope/
"""
from typing import List, Optional
from fastapi import HTTPException, status, Request
from backend.auth.middleware import get_current_user
from backend.schemas.open_badges.status import (
    create_imsx_status_info,
    ImsxCodeMajorEnum,
    ImsxSeverityEnum,
    ImsxCodeMinorFieldValueEnum
)


# Open Badges v3.0 scope URIs
OB_SCOPE_CREDENTIAL_READONLY = "https://purl.imsglobal.org/spec/ob/v3p0/scope/credential.readonly"
OB_SCOPE_CREDENTIAL_UPSERT = "https://purl.imsglobal.org/spec/ob/v3p0/scope/credential.upsert"
OB_SCOPE_PROFILE_READONLY = "https://purl.imsglobal.org/spec/ob/v3p0/scope/profile.readonly"
OB_SCOPE_PROFILE_UPDATE = "https://purl.imsglobal.org/spec/ob/v3p0/scope/profile.update"


def extract_scopes_from_token(token_payload: dict) -> List[str]:
    """
    Extract OAuth2 scopes from JWT token payload.
    Scopes can be in 'scp', 'scope', or 'roles' claims.
    """
    scopes = []
    
    # Check 'scp' claim (space-separated string)
    if "scp" in token_payload:
        scopes.extend(token_payload["scp"].split())
    
    # Check 'scope' claim (space-separated string)
    if "scope" in token_payload:
        scopes.extend(token_payload["scope"].split())
    
    # Check 'roles' claim (array)
    if "roles" in token_payload and isinstance(token_payload["roles"], list):
        scopes.extend(token_payload["roles"])
    
    # Check 'wids' claim (Windows Identity) - Entra ID app roles
    if "wids" in token_payload and isinstance(token_payload["wids"], list):
        # Map Entra ID role IDs to scope URIs if configured
        # For now, we'll use a mapping approach
        pass
    
    return list(set(scopes))  # Remove duplicates


def has_scope(user: dict, required_scope: str) -> bool:
    """
    Check if user has the required scope.
    Falls back to group-based access if scopes not available.
    """
    token_payload = user.get("token_payload", {})
    scopes = extract_scopes_from_token(token_payload)
    
    # Direct scope match
    if required_scope in scopes:
        return True
    
    # Fallback: Map Entra ID groups to scopes
    # This allows using existing group-based auth while transitioning to scope-based
    groups = user.get("groups", [])
    
    # Map groups to scopes (configurable)
    scope_mapping = {
        OB_SCOPE_CREDENTIAL_READONLY: ["Issuers", "Badge Admins"],
        OB_SCOPE_CREDENTIAL_UPSERT: ["Issuers", "Badge Admins"],
        OB_SCOPE_PROFILE_READONLY: ["Issuers", "Badge Admins", "Users"],
        OB_SCOPE_PROFILE_UPDATE: ["Issuers", "Badge Admins"],
    }
    
    if required_scope in scope_mapping:
        required_groups = scope_mapping[required_scope]
        if any(group in groups for group in required_groups):
            return True
    
    return False


def require_scope(required_scope: str):
    """
    Dependency factory to require a specific OAuth2 scope.
    """
    def scope_dependency(request: Request, current_user: dict = None):
        if current_user is None:
            current_user = get_current_user(request)
        
        if not has_scope(current_user, required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_imsx_status_info(
                    ImsxCodeMajorEnum.FAILURE,
                    ImsxSeverityEnum.ERROR,
                    f"Insufficient permissions. Required scope: {required_scope}",
                    ImsxCodeMinorFieldValueEnum.FORBIDDEN
                ).model_dump()
            )
        return current_user
    
    return scope_dependency


# Convenience dependencies for each scope
def require_credential_readonly(request: Request, current_user: dict = None):
    """Require credential.readonly scope"""
    return require_scope(OB_SCOPE_CREDENTIAL_READONLY)(request, current_user)


def require_credential_upsert(request: Request, current_user: dict = None):
    """Require credential.upsert scope"""
    return require_scope(OB_SCOPE_CREDENTIAL_UPSERT)(request, current_user)


def require_profile_readonly(request: Request, current_user: dict = None):
    """Require profile.readonly scope"""
    return require_scope(OB_SCOPE_PROFILE_READONLY)(request, current_user)


def require_profile_update(request: Request, current_user: dict = None):
    """Require profile.update scope"""
    return require_scope(OB_SCOPE_PROFILE_UPDATE)(request, current_user)

