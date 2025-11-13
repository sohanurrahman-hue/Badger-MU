"""
Open Badges v3.0 Credentials API Router
Implements GET /credentials and POST /credentials per OpenAPI spec
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging
import re

from backend.db import get_db
from backend.db.models import AchievementCredential
from backend.auth.middleware import get_current_user
from backend.auth.scopes import require_credential_readonly, require_credential_upsert
from backend.schemas.open_badges.credential import (
    AchievementCredentialSchema,
    GetOpenBadgeCredentialsResponse
)
from backend.schemas.open_badges.status import (
    ImsxStatusInfo,
    map_http_status_to_imsx,
    ImsxCodeMinorFieldValueEnum
)

logger = logging.getLogger(__name__)

router = APIRouter()


def build_pagination_links(
    request: Request,
    offset: int,
    limit: int,
    total: int
) -> List[str]:
    """
    Build Link header values for pagination (RFC 8288)
    """
    base_url = str(request.base_url).rstrip('/')
    path = request.url.path
    
    links = []
    
    # First page
    first_offset = 0
    links.append(f'<{base_url}{path}?limit={limit}&offset={first_offset}>; rel="first"')
    
    # Last page
    last_offset = max(0, ((total - 1) // limit) * limit)
    links.append(f'<{base_url}{path}?limit={limit}&offset={last_offset}>; rel="last"')
    
    # Previous page
    if offset > 0:
        prev_offset = max(0, offset - limit)
        links.append(f'<{base_url}{path}?limit={limit}&offset={prev_offset}>; rel="prev"')
    
    # Next page
    if offset + limit < total:
        next_offset = offset + limit
        links.append(f'<{base_url}{path}?limit={limit}&offset={next_offset}>; rel="next"')
    
    return links


def db_credential_to_schema(db_cred: AchievementCredential) -> AchievementCredentialSchema:
    """
    Convert database AchievementCredential to AchievementCredentialSchema
    TODO: This is a simplified version - needs full implementation with all relationships
    """
    # This is a placeholder - full implementation would load all relationships
    # and convert to the proper schema format
    from backend.schemas.open_badges.achievement import AchievementSubjectSchema
    from backend.schemas.open_badges.profile import ProfileRefSchema
    
    # Build credential subject (simplified)
    credential_subject = AchievementSubjectSchema(
        type=["AchievementSubject"],
        achievement=None  # TODO: Load achievement from relationship
    )
    
    # Build issuer (simplified)
    issuer: ProfileRefSchema = db_cred.issuer.iri if db_cred.issuer else ""
    
    return AchievementCredentialSchema(
        id=db_cred.iri,
        context=db_cred.context or [
            "https://www.w3.org/ns/credentials/v2",
            "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json"
        ],
        type=db_cred.type or ["VerifiableCredential", "AchievementCredential"],
        credentialSubject=credential_subject,
        issuer=issuer,
        validFrom=db_cred.valid_from,
        validUntil=db_cred.valid_until,
        name=db_cred.name,
        description=db_cred.description,
        awardedDate=db_cred.awarded_date
    )


@router.get(
    "/credentials",
    response_model=GetOpenBadgeCredentialsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get issued OpenBadgeCredentials",
    description="Get issued OpenBadgeCredentials from the resource server for the supplied parameters and access token.",
    tags=["OpenBadgeCredentials"]
)
async def get_credentials(
    request: Request,
    response: Response,
    limit: Optional[int] = Query(
        None,
        ge=1,
        description="The maximum number of OpenBadgeCredentials to return per page."
    ),
    offset: Optional[int] = Query(
        None,
        ge=0,
        description="The index of the first AchievementCredential to return. (zero indexed)"
    ),
    since: Optional[str] = Query(
        None,
        description="Only include OpenBadgeCredentials issued after this timestamp. An ISO8601 time using the syntax YYYY-MM-DDThh:mm:ss."
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_credential_readonly)
):
    """
    Get issued OpenBadgeCredentials from the resource server.
    
    Returns credentials in two arrays:
    - credential: Credentials not signed with VC-JWT Proof Format
    - compactJwsString: Credentials signed with VC-JWT Proof Format
    """
    try:
        # Default pagination
        limit = limit or 100
        offset = offset or 0
        
        # Build query
        query = db.query(AchievementCredential)
        
        # Filter by since parameter
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                query = query.filter(AchievementCredential.created_at >= since_dt)
            except ValueError:
                error = map_http_status_to_imsx(
                    400,
                    "Invalid 'since' parameter format. Must be ISO8601 date-time."
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error.model_dump()
                )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        credentials = query.order_by(AchievementCredential.created_at.desc()).offset(offset).limit(limit).all()
        
        # Separate credentials by proof format
        # TODO: Determine if credential uses VC-JWT format based on proof type
        credential_list = []
        compact_jws_list = []
        
        for db_cred in credentials:
            # For now, all credentials go to credential array
            # In production, check if proof type is VC-JWT and extract Compact JWS
            try:
                cred_schema = db_credential_to_schema(db_cred)
                credential_list.append(cred_schema)
            except Exception as e:
                logger.warning(f"Failed to convert credential {db_cred.id} to schema: {str(e)}")
                continue
        
        # Build response
        result = GetOpenBadgeCredentialsResponse(
            credential=credential_list,
            compactJwsString=compact_jws_list
        )
        
        # Add pagination headers
        response.headers["X-Total-Count"] = str(total)
        links = build_pagination_links(request, offset, limit, total)
        if links:
            response.headers["Link"] = ", ".join(links)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting credentials: {str(e)}")
        error = map_http_status_to_imsx(500, f"Internal server error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump()
        )


@router.post(
    "/credentials",
    summary="Create or replace an AchievementCredential",
    description="Create or replace an AchievementCredential on the resource server, appending it to the list of credentials for the subject, or replacing an existing entry in that list.",
    tags=["OpenBadgeCredentials"]
)
async def upsert_credential(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_credential_upsert)
):
    """
    Create or replace an AchievementCredential.
    
    Accepts either:
    - application/json: AchievementCredential object
    - text/plain: Compact JWS string (VC-JWT format)
    """
    try:
        # Check content type
        content_type = request.headers.get("content-type", "").lower()
        
        if "application/json" in content_type:
            # Parse JSON body
            import json
            body = await request.body()
            data = json.loads(body)
            credential_data = AchievementCredentialSchema(**data)
            
            # TODO: Implement credential upsert logic
            # - Check if credential exists (using credential equality algorithm)
            # - If exists, update (return 200)
            # - If new, create (return 201)
            
            # For now, always return 201
            response.status_code = status.HTTP_201_CREATED
            return credential_data
            
        elif "text/plain" in content_type:
            # Read Compact JWS from body
            body = await request.body()
            compact_jws = body.decode('utf-8').strip()
            
            # Validate Compact JWS format
            pattern = re.compile(r"^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]+$")
            if not pattern.match(compact_jws):
                error = map_http_status_to_imsx(
                    400,
                    "Invalid Compact JWS format. Must match pattern: ^[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]*\\.[a-zA-Z0-9_-]+$"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error.model_dump()
                )
            
            # TODO: Parse and validate JWT, extract credential
            # For now, return the Compact JWS string
            response.status_code = status.HTTP_201_CREATED
            response.headers["Content-Type"] = "text/plain"
            return compact_jws
            
        else:
            error = map_http_status_to_imsx(
                400,
                "Unsupported content type. Must be 'application/json' or 'text/plain'"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error.model_dump()
            )
            
    except HTTPException:
        raise
    except ValueError as e:
        # JSON parsing error
        error = map_http_status_to_imsx(400, f"Invalid JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.model_dump()
        )
    except Exception as e:
        logger.exception(f"Error upserting credential: {str(e)}")
        error = map_http_status_to_imsx(500, f"Internal server error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump()
        )

