"""
Image schema for Open Badges v3.0
Reference: https://www.imsglobal.org/spec/ob/v3p0/#image
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ImageSchema(BaseModel):
    """Image object schema"""
    id: str
    type: str = Field(default="Image")
    caption: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that type is 'Image'"""
        if v != "Image":
            raise ValueError("Type must be 'Image'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/badge-image.png",
                "type": "Image",
                "caption": "Badge image"
            }
        }

