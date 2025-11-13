"""
Profile schemas for Open Badges v3.0
Reference: https://www.imsglobal.org/spec/ob/v3p0#profile
"""
from pydantic import BaseModel, Field, field_validator, field_serializer, HttpUrl, EmailStr
from typing import Optional, List, Union
from datetime import date, datetime
from .image import ImageSchema
from .identifier import IdentifierEntrySchema
from .proof import CompactJWSSchema
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .credential import EndorsementCredentialSchema


class GeoCoordinatesSchema(BaseModel):
    """Geographic coordinates"""
    type: str = Field(default="GeoCoordinates")
    latitude: float
    longitude: float

    class Config:
        json_schema_extra = {
            "example": {
                "type": "GeoCoordinates",
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        }


class AddressSchema(BaseModel):
    """Address schema"""
    type: List[str] = Field(default=["Address"])
    addressCountry: Optional[str] = None
    addressCountryCode: Optional[str] = Field(None, min_length=2, max_length=2)
    addressRegion: Optional[str] = None
    addressLocality: Optional[str] = None
    streetAddress: Optional[str] = None
    postOfficeBoxNumber: Optional[str] = None
    postalCode: Optional[str] = None
    geo: Optional[GeoCoordinatesSchema] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'Address'"""
        if "Address" not in v:
            raise ValueError("One of the items MUST be the IRI 'Address'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": ["Address"],
                "addressCountry": "United States",
                "addressCountryCode": "US",
                "addressLocality": "New York",
                "streetAddress": "123 Main St"
            }
        }


class ProfileSchema(BaseModel):
    """Profile schema for issuers and organizations"""
    id: str
    type: List[str] = Field(default=["Profile"])
    name: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    endorsementJwt: Optional[List[CompactJWSSchema]] = None
    image: Optional[ImageSchema] = None
    email: Optional[EmailStr] = None
    address: Optional[AddressSchema] = None
    otherIdentifier: Optional[List[IdentifierEntrySchema]] = None
    official: Optional[str] = None
    familyName: Optional[str] = None
    givenName: Optional[str] = None
    additionalName: Optional[str] = None
    patronymicName: Optional[str] = None
    honorificPrefix: Optional[str] = None
    honorificSuffix: Optional[str] = None
    familyNamePrefix: Optional[str] = None
    dateOfBirth: Optional[date] = None
    endorsement: Optional[List["EndorsementCredentialSchema"]] = None  # type: ignore

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'Profile'"""
        if "Profile" not in v:
            raise ValueError("One of the items of type MUST be the IRI 'Profile'")
        return v

    @field_serializer("dateOfBirth")
    def serialize_date_of_birth(self, value: Optional[date], _info) -> Optional[str]:
        """Serialize date to ISO string"""
        if value is None:
            return None
        return value.isoformat()

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/issuer",
                "type": ["Profile"],
                "name": "Example Issuer",
                "email": "issuer@example.com"
            }
        }


# Forward reference for ProfileRefSchema
# This is a type alias that can be either a URL string or a ProfileSchema object
ProfileRefSchema = Union[HttpUrl, "ProfileSchema"]


# Update forward references after all classes are defined
def _update_forward_refs():
    """Update forward references to resolve circular imports"""
    from .credential import EndorsementCredentialSchema
    
    # Make EndorsementCredentialSchema available in this module's namespace for model_rebuild()
    import sys
    current_module = sys.modules[__name__]
    current_module.EndorsementCredentialSchema = EndorsementCredentialSchema
    
    ProfileSchema.model_rebuild()

# Note: _update_forward_refs() is called from __init__.py after all modules are loaded

