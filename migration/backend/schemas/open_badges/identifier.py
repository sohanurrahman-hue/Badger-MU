"""
Identifier schemas for Open Badges v3.0
Reference: https://www.imsglobal.org/spec/ob/v3p0/#identifierentry
Reference: https://www.imsglobal.org/spec/ob/v3p0/#identityobject
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from backend.db.models import IdentifierTypeEnum


class IdentifierEntrySchema(BaseModel):
    """Identifier entry schema"""
    type: str = Field(default="IdentifierEntry")
    identifier: str
    identifierType: IdentifierTypeEnum

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that type is 'IdentifierEntry'"""
        if v != "IdentifierEntry":
            raise ValueError("Type must be 'IdentifierEntry'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "IdentifierEntry",
                "identifier": "https://example.com/user/123",
                "identifierType": "emailAddress"
            }
        }


class IdentityObjectSchema(BaseModel):
    """Identity object schema"""
    type: str = Field(default="IdentityObject")
    hashed: bool
    identityHash: str
    identityType: IdentifierTypeEnum
    salt: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that type is 'IdentityObject'"""
        if v != "IdentityObject":
            raise ValueError("Type must be 'IdentityObject'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "IdentityObject",
                "hashed": True,
                "identityHash": "abc123...",
                "identityType": "emailAddress",
                "salt": "xyz789"
            }
        }

