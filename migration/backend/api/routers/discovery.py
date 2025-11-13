"""
Open Badges v3.0 Discovery API Router
Implements GET /discovery for Service Description Document
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging
import os

from backend.schemas.open_badges.discovery import ServiceDescriptionDocument, OpenApiInfo, OpenApiComponents, OpenApiSecuritySchemes, OpenApiOAuth2SecurityScheme

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/discovery",
    response_model=ServiceDescriptionDocument,
    status_code=200,
    summary="Get Service Description Document",
    description="Fetch the Service Description Document from the resource server.",
    tags=["Discovery"]
)
async def get_service_description(request: Request):
    """
    Fetch the Service Description Document (SDD).
    
    The SDD is a machine readable document that contains the description of the
    service features supported by the Provider/Platform.
    """
    try:
        base_url = str(request.base_url).rstrip('/')
        
        # Get configuration from environment
        terms_of_service = os.getenv(
            "OB_TERMS_OF_SERVICE_URL",
            f"{base_url}/terms"
        )
        privacy_policy = os.getenv(
            "OB_PRIVACY_POLICY_URL",
            f"{base_url}/privacy"
        )
        registration_url = os.getenv(
            "OB_REGISTRATION_URL",
            f"{base_url}/register"
        )
        api_image = os.getenv("OB_API_IMAGE_URL")
        
        # Build Service Description Document
        sdd = ServiceDescriptionDocument(
            openapi="3.0.1",
            info=OpenApiInfo(
                title=os.getenv("OB_API_TITLE", "Badge Engine API"),
                version=os.getenv("OB_API_VERSION", "3.0"),
                termsOfService=terms_of_service,
                x_imssf_privacyPolicyUrl=privacy_policy,
                x_imssf_image=api_image
            ),
            components=OpenApiComponents(
                securitySchemes=OpenApiSecuritySchemes(
                    OAuth2ACG=OpenApiOAuth2SecurityScheme(
                        type="oauth2",
                        description="OAuth2 Authorization Code Grant for Open Badges v3.0",
                        x_imssf_registrationUrl=registration_url
                    )
                )
            )
        )
        
        return sdd
        
    except Exception as e:
        logger.exception(f"Error generating service description: {str(e)}")
        # Discovery endpoint should not fail - return basic document
        base_url = str(request.base_url).rstrip('/')
        return ServiceDescriptionDocument(
            openapi="3.0.1",
            info=OpenApiInfo(
                title="Badge Engine API",
                version="3.0",
                termsOfService=f"{base_url}/terms",
                x_imssf_privacyPolicyUrl=f"{base_url}/privacy"
            ),
            components=OpenApiComponents(
                securitySchemes=OpenApiSecuritySchemes(
                    OAuth2ACG=OpenApiOAuth2SecurityScheme(
                        type="oauth2",
                        x_imssf_registrationUrl=f"{base_url}/register"
                    )
                )
            )
        )

