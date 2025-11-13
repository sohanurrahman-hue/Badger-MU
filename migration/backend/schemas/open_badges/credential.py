"""
Credential schemas for Open Badges v3.0

This module implements the Open Badges v3.0 credential schemas as specified in:
- https://www.imsglobal.org/spec/ob/v3p0/#credentialschema
- https://www.imsglobal.org/spec/ob/v3p0/#verifiablecredential
- https://www.imsglobal.org/spec/ob/v3p0/#achievementcredential

All schemas comply with the Verifiable Credentials Data Model v2.0 and Open Badges v3.0 specification.
"""
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, List, Union
from datetime import datetime
from .image import ImageSchema
from .proof import ProofSchema, CompactJWSSchema
from .achievement import AchievementSubjectSchema
import re

# Forward references to avoid circular imports
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from .profile import ProfileSchema, ProfileRefSchema
else:
    # Use string annotation for ProfileRefSchema to defer resolution
    # HttpUrl is already imported above, so we can use it here
    ProfileRefSchema = Union[HttpUrl, "ProfileSchema"]  # type: ignore


class EvidenceSchema(BaseModel):
    """Evidence schema"""
    id: Optional[HttpUrl] = None
    type: List[str]
    narrative: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    audience: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'Evidence'"""
        if "Evidence" not in v:
            raise ValueError("One of the items MUST be the IRI 'Evidence'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": ["Evidence"],
                "name": "Project Portfolio",
                "description": "Collection of completed projects"
            }
        }


class CredentialSchemaSchema(BaseModel):
    """Credential schema reference"""
    id: HttpUrl
    type: str = Field(default="1EdTechJsonSchemaValidator2019")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that type is '1EdTechJsonSchemaValidator2019'"""
        if v != "1EdTechJsonSchemaValidator2019":
            raise ValueError(
                "One instance of CredentialSchema MUST have a type of '1EdTechJsonSchemaValidator2019'"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://purl.imsglobal.org/spec/ob/v3p0/schema/json/ob_v3p0_achievementcredential_schema.json",
                "type": "1EdTechJsonSchemaValidator2019"
            }
        }


class CredentialStatusSchema(BaseModel):
    """Credential status schema"""
    id: HttpUrl
    type: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/status/1",
                "type": "CredentialStatusList2020"
            }
        }


class CredentialSubjectSchema(BaseModel):
    """Generic credential subject schema"""
    id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/subject/1"
            }
        }


class RefreshServiceSchema(BaseModel):
    """Refresh service schema"""
    id: HttpUrl
    type: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/refresh/1",
                "type": "RefreshService"
            }
        }


class TermsOfUseSchema(BaseModel):
    """Terms of use schema"""
    id: Optional[str] = None
    type: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/terms/1",
                "type": "TermsOfUse"
            }
        }


class EndorsementSubjectSchema(BaseModel):
    """Endorsement subject schema"""
    id: str
    type: List[str] = Field(default=["EndorsementSubject"])
    endorsementComment: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'EndorsementSubject'"""
        if "EndorsementSubject" not in v:
            raise ValueError("One of the items MUST be the URI 'EndorsementSubject'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/endorsement/subject/1",
                "type": ["EndorsementSubject"],
                "endorsementComment": "This achievement is endorsed"
            }
        }


class BaseCredentialSchema(BaseModel):
    """Base credential schema with common fields"""
    credentialSubject: CredentialSubjectSchema
    issuer: Union[HttpUrl, "ProfileSchema"]  # Union[HttpUrl, ProfileSchema] - using string annotation to avoid circular import
    validFrom: str  # datetime string
    validUntil: Optional[str] = None  # datetime string
    proof: Optional[List[ProofSchema]] = None
    credentialSchema: Optional[List[CredentialSchemaSchema]] = None
    credentialStatus: Optional[CredentialStatusSchema] = None
    refreshService: Optional[RefreshServiceSchema] = None
    termsOfUse: Optional[List[TermsOfUseSchema]] = None


class VerifiableCredentialSchema(BaseCredentialSchema):
    """Base verifiable credential schema"""
    context: List[str]
    type: List[str]

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: List[str]) -> List[str]:
        """Validate context starts with correct URI"""
        if not v or v[0] != "https://www.w3.org/ns/credentials/v2":
            raise ValueError(
                "MUST be an ordered set where the first item is a URI with the value "
                "'https://www.w3.org/ns/credentials/v2'"
            )
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'VerifiableCredential'"""
        if "VerifiableCredential" not in v:
            raise ValueError("One of the items MUST be the URI 'VerifiableCredential'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "context": ["https://www.w3.org/ns/credentials/v2"],
                "type": ["VerifiableCredential"],
                "credentialSubject": {"id": "https://example.com/subject/1"},
                "issuer": "https://example.com/issuer",
                "validFrom": "2024-01-01T00:00:00Z"
            }
        }


class AchievementCredentialSchema(VerifiableCredentialSchema):
    """Achievement credential schema"""
    context: List[HttpUrl] = Field(
        default=[
            "https://www.w3.org/ns/credentials/v2",
            "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json"
        ]
    )
    type: List[str] = Field(
        default=[
            "VerifiableCredential",
            "AchievementCredential",
            "OpenBadgeCredential"
        ]
    )
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[ImageSchema] = None
    awardedDate: Optional[str] = None  # datetime string
    credentialSubject: AchievementSubjectSchema
    endorsement: Optional[List["EndorsementCredentialSchema"]] = None
    endorsementJwt: Optional[List[CompactJWSSchema]] = None
    evidence: Optional[List[EvidenceSchema]] = None

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: List[HttpUrl]) -> List[HttpUrl]:
        """Validate context structure"""
        if len(v) < 2:
            raise ValueError("Context must have at least 2 items")
        if str(v[0]) != "https://www.w3.org/ns/credentials/v2":
            raise ValueError(
                "The first item in @context must be a URI with the value "
                "'https://www.w3.org/ns/credentials/v2'"
            )
        if str(v[1]) != "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json":
            raise ValueError(
                "The second item in @context must be a URI with the value "
                "'https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json'"
            )
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate type includes required values"""
        if "VerifiableCredential" not in v:
            raise ValueError(
                "One of the items in type MUST be the IRI 'VerifiableCredential'"
            )
        if "AchievementCredential" not in v and "OpenBadgeCredential" not in v:
            raise ValueError(
                "One of the items in type MUST be the IRI 'AchievementCredential' or 'OpenBadgeCredential'"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/credential/1",
                "context": [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json"
                ],
                "type": [
                    "VerifiableCredential",
                    "AchievementCredential",
                    "OpenBadgeCredential"
                ],
                "name": "Python Programming Badge",
                "credentialSubject": {
                    "type": ["AchievementSubject"],
                    "achievement": {
                        "id": "https://example.com/achievement/1",
                        "type": ["Achievement"],
                        "name": "Python Badge",
                        "description": "Python proficiency",
                        "criteria": {"narrative": "Complete course"}
                    }
                },
                "issuer": "https://example.com/issuer",
                "validFrom": "2024-01-01T00:00:00Z"
            }
        }


class BaseEndorsementSchema(BaseCredentialSchema):
    """Base endorsement schema"""
    context: List[HttpUrl] = Field(
        default=[
            "https://www.w3.org/ns/credentials/v2",
            "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json"
        ]
    )
    type: List[str] = Field(
        default=["VerifiableCredential", "EndorsementCredential"]
    )
    id: str
    name: str
    description: Optional[str] = None
    credentialSubject: EndorsementSubjectSchema
    awardedDate: Optional[str] = None  # datetime string

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: List[HttpUrl]) -> List[HttpUrl]:
        """Validate context structure"""
        if len(v) < 2:
            raise ValueError("Context must have at least 2 items")
        if str(v[0]) != "https://www.w3.org/ns/credentials/v2":
            raise ValueError(
                "The first item MUST be a URI with the value "
                "'https://www.w3.org/ns/credentials/v2'"
            )
        if str(v[1]) != "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json":
            raise ValueError(
                "The second item MUST be a URI with the value "
                "'https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json'"
            )
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate type includes required values"""
        if "VerifiableCredential" not in v:
            raise ValueError(
                "One of the items MUST be the URI 'VerifiableCredential'"
            )
        if "EndorsementCredential" not in v:
            raise ValueError(
                "One of the items MUST be the URI 'EndorsementCredential'"
            )
        return v


class EndorsementCredential(BaseEndorsementSchema):
    """
    Endorsement credential schema.
    
    This schema explicitly overrides the issuer field with lazy loading
    to handle circular references (matching TypeScript behavior).
    """
    # Override issuer with explicit forward reference for circular dependency
    # This matches TypeScript's z.lazy(() => profileRefSchema)
    issuer: Union[HttpUrl, "ProfileSchema"]  # Union[HttpUrl, ProfileSchema] - using string annotation to avoid circular import

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/endorsement/1",
                "context": [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json"
                ],
                "type": ["VerifiableCredential", "EndorsementCredential"],
                "name": "Endorsement of Python Badge",
                "credentialSubject": {
                    "id": "https://example.com/endorsement/subject/1",
                    "type": ["EndorsementSubject"],
                    "endorsementComment": "This achievement is endorsed"
                },
                "issuer": "https://example.com/endorser",
                "validFrom": "2024-01-01T00:00:00Z"
            }
        }


# Alias for consistency with other schema naming (EndorsementCredentialSchema)
EndorsementCredentialSchema = EndorsementCredential


# Update forward references after all classes are defined
def _update_forward_refs():
    """Update forward references to resolve circular imports"""
    from .profile import ProfileSchema
    
    # Make ProfileSchema available in this module's namespace for model_rebuild()
    import sys
    current_module = sys.modules[__name__]
    current_module.ProfileSchema = ProfileSchema
    
    # Rebuild models to resolve forward references
    # Note: Rebuild in dependency order - ProfileSchema first, then schemas that use it
    ProfileSchema.model_rebuild()
    BaseCredentialSchema.model_rebuild()
    VerifiableCredentialSchema.model_rebuild()
    AchievementCredentialSchema.model_rebuild()
    EndorsementCredentialSchema.model_rebuild()

# Note: _update_forward_refs() is called from __init__.py after all modules are loaded


# Additional schema for creating verifiable achievement credentials (with MongoDB docId)
# Note: This is application-specific and not part of the Open Badges spec
class CreateVerifiableAchievementCredentialSchema(AchievementCredentialSchema):
    """Schema for creating verifiable achievement credentials with document ID"""
    docId: str = Field(..., min_length=24, max_length=24)
    # Override type field - no default, must be provided
    type: List[str] = Field(...)
    
    @field_validator("docId")
    @classmethod
    def validate_doc_id(cls, v: str) -> str:
        """
        Validate docId format (Postgres/UUID compatible).
        Accepts UUID strings (canonical 36-character form) or integer IDs as string.
        """
        import uuid

        # Accept UUID (canonical string form)
        try:
            uuid_obj = uuid.UUID(v)
            if str(uuid_obj) == v.lower():
                return v
        except Exception:
            pass
        # Accept integer as string (Postgres SERIAL PK as string)
        if v.isdigit():
            return v
        raise ValueError("docId must be a valid UUID (36 characters) or integer string for Postgres")
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """
        Validate type includes AchievementCredential or OpenBadgeCredential.
        
        This overrides the parent's validation - it does NOT require "VerifiableCredential",
        only "AchievementCredential" OR "OpenBadgeCredential" (matching TypeScript behavior).
        """
        # Positive check: must include AchievementCredential OR OpenBadgeCredential
        if not ("AchievementCredential" in v or "OpenBadgeCredential" in v):
            raise ValueError(
                "One of the items in type MUST be the IRI 'AchievementCredential' or 'OpenBadgeCredential'"
            )
        return v


class GetOpenBadgeCredentialsResponse(BaseModel):
    """
    Response schema for GET /credentials endpoint.
    OpenBadgeCredentials that have not been signed with the VC-JWT Proof Format MUST be in the `credential` array.
    OpenBadgeCredentials that have been signed with the VC-JWT Proof Format MUST be in the `compactJwsString` array.
    """
    credential: List[AchievementCredentialSchema] = Field(
        default_factory=list,
        description="OpenBadgeCredentials that have not been signed with the VC-JWT Proof Format MUST be in the `credential` array."
    )
    compactJwsString: List[str] = Field(
        default_factory=list,
        description="OpenBadgeCredentials that have been signed with the VC-JWT Proof Format MUST be in the `compactJwsString` array."
    )

    @field_validator("compactJwsString")
    @classmethod
    def validate_compact_jws(cls, v: List[str]) -> List[str]:
        """Validate each Compact JWS string matches the pattern"""
        import re
        pattern = re.compile(r"^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]+$")
        for jws in v:
            if not pattern.match(jws):
                raise ValueError(f"Invalid Compact JWS format: {jws}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "credential": [],
                "compactJwsString": []
            }
        }

