"""
Open Badges v3.0 Profile API Router
Implements GET /profile and PUT /profile per OpenAPI spec
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

from backend.db import get_db
from backend.db.models import Profile
from backend.auth.middleware import get_current_user
from backend.auth.scopes import require_profile_readonly, require_profile_update
from backend.schemas.open_badges.profile import ProfileSchema
from backend.schemas.open_badges.status import (
    ImsxStatusInfo,
    map_http_status_to_imsx
)

logger = logging.getLogger(__name__)

router = APIRouter()


def db_profile_to_schema(db_profile: Profile) -> ProfileSchema:
    """
    Convert database Profile to ProfileSchema
    TODO: Full implementation with all relationships
    """
    from backend.schemas.open_badges.image import ImageSchema
    from backend.schemas.open_badges.profile import AddressSchema
    
    # Build image if exists
    image = None
    if db_profile.image:
        image = ImageSchema(
            id=db_profile.image.iri,
            type=db_profile.image.type or "Image",
            caption=db_profile.image.caption
        )
    
    # Build address if exists
    address = None
    if db_profile.address:
        address = AddressSchema(
            type=["Address"],
            addressCountry=db_profile.address.address_country,
            addressCountryCode=db_profile.address.address_country_code,
            addressRegion=db_profile.address.address_region,
            addressLocality=db_profile.address.address_locality,
            streetAddress=db_profile.address.street_address,
            postalCode=db_profile.address.postal_code
        )
    
    return ProfileSchema(
        id=db_profile.iri,
        type=db_profile.type or ["Profile"],
        name=db_profile.name,
        email=db_profile.email,
        phone=db_profile.phone,
        description=db_profile.description,
        url=db_profile.url,
        image=image,
        address=address,
        official=db_profile.official,
        familyName=db_profile.family_name,
        givenName=db_profile.given_name,
        additionalName=db_profile.additional_name,
        patronymicName=db_profile.patronymic_name,
        honorificPrefix=db_profile.honorific_prefix,
        honorificSuffix=db_profile.honorific_suffix,
        familyNamePrefix=db_profile.family_name_prefix,
        dateOfBirth=db_profile.date_of_birth.isoformat() if db_profile.date_of_birth else None,
        endorsementJwt=db_profile.endorsement_jwt
    )


@router.get(
    "/profile",
    response_model=ProfileSchema,
    summary="Get profile",
    description="Fetch the profile from the resource server for the supplied access token.",
    tags=["OpenBadgeCredentials"]
)
async def get_profile(
    db: Session = Depends(get_db),
    email: str = Depends(get_current_user),
    #current_user: dict = Depends(require_profile_readonly)
):
    """
    Fetch the profile for the authenticated entity.
    """
    try:
        # Get profile for current user
        user_email = email
        if not user_email:
            error = map_http_status_to_imsx(401, "User email not found in token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error.model_dump()
            )
        
        # Find profile by email
        profile = db.query(Profile).filter(Profile.email == user_email).first()
        
        if not profile:
            error = map_http_status_to_imsx(404, "Profile not found for authenticated user")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error.model_dump()
            )
        
        return db_profile_to_schema(profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting profile: {str(e)}")
        error = map_http_status_to_imsx(500, f"Internal server error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump()
        )


@router.put(
    "/profile",
    response_model=ProfileSchema,
    summary="Update profile",
    description="Update the profile for the authenticate entity.",
    tags=["OpenBadgeCredentials"]
)
async def put_profile(
    profile_data: ProfileSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_profile_update)
):
    """
    Update the profile for the authenticated entity.
    """
    try:
        # Get profile for current user
        user_email = current_user.get("email")
        if not user_email:
            error = map_http_status_to_imsx(401, "User email not found in token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error.model_dump()
            )
        
        # Find or create profile
        profile = db.query(Profile).filter(Profile.email == user_email).first()
        
        if not profile:
            # Create new profile
            import uuid
            profile = Profile(
                id=uuid.uuid4(),
                iri=profile_data.id,
                email=user_email
            )
            db.add(profile)
        
        # Update profile fields
        profile.iri = profile_data.id
        profile.type = profile_data.type
        profile.name = profile_data.name
        profile.email = profile_data.email or user_email
        profile.phone = profile_data.phone
        profile.description = profile_data.description
        profile.url = profile_data.url
        profile.official = profile_data.official
        profile.family_name = profile_data.familyName
        profile.given_name = profile_data.givenName
        profile.additional_name = profile_data.additionalName
        profile.patronymic_name = profile_data.patronymicName
        profile.honorific_prefix = profile_data.honorificPrefix
        profile.honorific_suffix = profile_data.honorificSuffix
        profile.family_name_prefix = profile_data.familyNamePrefix
        profile.endorsement_jwt = profile_data.endorsementJwt
        
        # TODO: Update image and address relationships
        
        if profile_data.dateOfBirth:
            from datetime import datetime
            profile.date_of_birth = datetime.fromisoformat(profile_data.dateOfBirth).date()
        
        db.commit()
        db.refresh(profile)
        
        return db_profile_to_schema(profile)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating profile: {str(e)}")
        error = map_http_status_to_imsx(500, f"Internal server error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump()
        )

