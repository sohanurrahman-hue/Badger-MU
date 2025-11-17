"""
Proof schemas for Open Badges v3.0
Reference: https://www.imsglobal.org/spec/ob/v3p0/#proof
"""
from pydantic import BaseModel, Field, field_validator, field_serializer, BeforeValidator
from typing import Optional, Annotated
from datetime import datetime
import re


# Compact JWS pattern for validation
_COMPACT_JWS_PATTERN = r'^[-A-Za-z0-9]+\.[-A-Za-z0-9]+\.[-A-Za-z0-9\-\_]*$'


def validate_compact_jws(value: str) -> str:
    """Validate Compact JWS format"""
    if not isinstance(value, str):
        raise ValueError("Compact JWS must be a string")
    if not re.match(_COMPACT_JWS_PATTERN, value):
        raise ValueError("Invalid Compact JWS format")
    return value


# Use Annotated with Field and BeforeValidator to create a constrained string type
# This approach supports JSON schema generation while providing validation
CompactJWSSchema = Annotated[
    str,
    BeforeValidator(validate_compact_jws),
    Field(
        pattern=_COMPACT_JWS_PATTERN,
        description="A string in Compact JWS format (RFC 7515)",
        json_schema_extra={
            "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        }
    )
]


class ProofSchema(BaseModel):
    """Cryptographic proof schema"""
    type: str
    created: Optional[datetime] = None
    cryptosuite: Optional[str] = None
    challenge: Optional[str] = None
    domain: Optional[str] = None
    nonce: Optional[str] = None
    proofPurpose: Optional[str] = None
    proofValue: Optional[str] = None
    verificationMethod: Optional[str] = None

    @field_serializer("created")
    def serialize_created(self, value: Optional[datetime], _info) -> Optional[str]:
        """Serialize datetime to ISO string"""
        if value is None:
            return None
        return value.isoformat()

    class Config:
        json_schema_extra = {
            "example": {
                "type": "DataIntegrityProof",
                "created": "2024-01-01T00:00:00Z",
                "cryptosuite": "eddsa-rdfc-2022",
                "proofPurpose": "assertionMethod",
                "verificationMethod": "https://example.com/keys/1",
                "proofValue": "z1234567890" # multibase encoded proof value
            }
        }


class DataIntegrityProofConfigSchema(BaseModel):
    """Data Integrity Proof configuration"""
    type: str = Field(default="DataIntegrityProof", literal=True)
    cryptosuite: str = Field(default="eddsa-rdfc-2022", literal=True)
    created: datetime

    @field_serializer("created")
    def serialize_created(self, value: datetime, _info) -> str:
        """Serialize datetime to ISO string"""
        return value.isoformat()


class DataIntegrityProofSchema(DataIntegrityProofConfigSchema):
    """Data Integrity Proof schema"""
    challenge: Optional[str] = None
    domain: Optional[str] = None
    nonce: Optional[str] = None
    proofPurpose: str = Field(default="assertionMethod")
    proofValue: str = Field(min_length=88, max_length=89)
    verificationMethod: Optional[str] = None

    @field_validator("proofValue")
    @classmethod
    def validate_proof_value(cls, v: str) -> str:
        """Validate proof value format (multibase encoded)"""
        # Pattern: starts with 'z' followed by base58 characters
        pattern = r'^z[1-9A-HJ-NP-Za-km-z]+'
        if not re.match(pattern, v):
            raise ValueError("Invalid proof value format")
        return v

