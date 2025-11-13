"""
Service Description Document schemas for Open Badges v3.0
Reference: https://www.imsglobal.org/spec/ob/v3p0/#servicedescriptiondocument
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any


class OpenApiOAuth2SecurityScheme(BaseModel):
    """OAuth2 security scheme definition"""
    type: str = Field(default="oauth2", description="MUST be the string `oauth2`.")
    description: Optional[str] = Field(None, description="A short description for the security scheme.")
    x_imssf_registrationUrl: HttpUrl = Field(
        ...,
        alias="x-imssf-registrationUrl",
        description="A fully qualified URL to the Client Registration endpoint."
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "type": "oauth2",
                "description": "OAuth2 Authorization Code Grant",
                "x-imssf-registrationUrl": "https://example.org/register"
            }
        }


class OpenApiSecuritySchemes(BaseModel):
    """Map of security scheme objects"""
    OAuth2ACG: OpenApiOAuth2SecurityScheme

    class Config:
        json_schema_extra = {
            "example": {
                "OAuth2ACG": {
                    "type": "oauth2",
                    "x-imssf-registrationUrl": "https://example.org/register"
                }
            }
        }


class OpenApiComponents(BaseModel):
    """OpenAPI components object"""
    securitySchemes: OpenApiSecuritySchemes

    class Config:
        json_schema_extra = {
            "example": {
                "securitySchemes": {
                    "OAuth2ACG": {
                        "type": "oauth2",
                        "x-imssf-registrationUrl": "https://example.org/register"
                    }
                }
            }
        }


class OpenApiInfo(BaseModel):
    """OpenAPI info object with required extensions"""
    title: str = Field(..., description="The name of the [=resource server=].")
    version: str = Field(..., description="The version of the API.")
    termsOfService: HttpUrl = Field(
        ...,
        description="A fully qualified URL to the [=resource server=]'s terms of service."
    )
    x_imssf_privacyPolicyUrl: HttpUrl = Field(
        ...,
        alias="x-imssf-privacyPolicyUrl",
        description="A fully qualified URL to the [=resource server=]'s privacy policy."
    )
    x_imssf_image: Optional[HttpUrl] = Field(
        None,
        alias="x-imssf-image",
        description="An image representing the [=resource server=]. MAY be a Data URI or the URL where the image may be found."
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "title": "Badge Engine API",
                "version": "3.0",
                "termsOfService": "https://example.org/terms",
                "x-imssf-privacyPolicyUrl": "https://example.org/privacy"
            }
        }


class ServiceDescriptionDocument(BaseModel):
    """
    The Service Description Document (SDD) is a machine readable document that contains
    the description of the service features supported by the Provider/Platform.
    """
    openapi: str = Field(
        default="3.0.1",
        description="This string MUST be the semantic version number of the OpenAPI Specification version that the OpenAPI document uses."
    )
    info: OpenApiInfo
    components: OpenApiComponents

    class Config:
        json_schema_extra = {
            "example": {
                "openapi": "3.0.1",
                "info": {
                    "title": "Badge Engine API",
                    "version": "3.0",
                    "termsOfService": "https://example.org/terms",
                    "x-imssf-privacyPolicyUrl": "https://example.org/privacy"
                },
                "components": {
                    "securitySchemes": {
                        "OAuth2ACG": {
                            "type": "oauth2",
                            "x-imssf-registrationUrl": "https://example.org/register"
                        }
                    }
                }
            }
        }

