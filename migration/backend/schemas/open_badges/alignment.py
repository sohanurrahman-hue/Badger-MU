"""
Alignment schema for Open Badges v3.0
Reference: https://www.imsglobal.org/spec/ob/v3p0/#alignment
"""
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, List
from backend.db.models import AlignmentTargetTypeEnum


class AlignmentSchema(BaseModel):
    """Alignment to educational frameworks"""
    type: List[str] = Field(default=["Alignment"])
    targetCode: Optional[str] = None
    targetDescription: Optional[str] = None
    targetName: str
    targetFramework: Optional[str] = None
    targetType: Optional[AlignmentTargetTypeEnum] = None
    targetUrl: HttpUrl

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'Alignment'"""
        if "Alignment" not in v:
            raise ValueError("One of the items MUST be the IRI 'Alignment'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": ["Alignment"],
                "targetName": "Common Core Standard",
                "targetUrl": "https://example.com/standards/cc/123",
                "targetCode": "CC.ELA.RL.1",
                "targetDescription": "Reading literature standard"
            }
        }

