"""
Achievement schemas for Open Badges v3.0
Reference: https://www.imsglobal.org/spec/ob/v3p0#achievement
"""
from pydantic import BaseModel, Field, field_validator, model_validator, field_serializer
from typing import Optional, List
from datetime import datetime
from backend.db.models import (
    AchievementTypeEnum,
    ResultTypeEnum,
    ResultStatusTypeEnum,
)
from .alignment import AlignmentSchema
from .image import ImageSchema
from .identifier import IdentifierEntrySchema, IdentityObjectSchema
from .proof import CompactJWSSchema

# Forward references to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .profile import ProfileSchema, ProfileRefSchema
    from .credential import EndorsementCredentialSchema
else:
    # Import at runtime but use string annotation in fields
    from .profile import ProfileRefSchema


class CriteriaSchema(BaseModel):
    """Criteria schema for achievements"""
    id: Optional[str] = None
    narrative: Optional[str] = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        """Must provide at least one of id or narrative"""
        if not self.id and not self.narrative:
            raise ValueError("Must provide at least one of id or narrative")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "narrative": "Complete all required coursework with a passing grade"
            }
        }


class RubricCriterionLevelSchema(BaseModel):
    """Rubric criterion level schema"""
    id: str
    type: List[str] = Field(default=["RubricCriterionLevel"])
    alignment: Optional[List[AlignmentSchema]] = None
    description: Optional[str] = None
    level: Optional[str] = None
    name: str
    points: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'RubricCriterionLevel'"""
        if "RubricCriterionLevel" not in v:
            raise ValueError("One of the items MUST be the IRI 'RubricCriterionLevel'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/rubric/level/1",
                "type": ["RubricCriterionLevel"],
                "name": "Exemplary",
                "points": "4"
            }
        }


class ResultDescriptionSchema(BaseModel):
    """Result description schema"""
    id: str
    type: List[str] = Field(default=["ResultDescription"])
    alignment: Optional[List[AlignmentSchema]] = None
    allowedValue: Optional[List[str]] = None
    name: str
    requiredLevel: Optional[str] = None
    requiredValue: Optional[str] = None
    resultType: ResultTypeEnum
    rubricCriterionLevel: Optional[List[RubricCriterionLevelSchema]] = None
    valueMax: Optional[str] = None
    valueMin: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'ResultDescription'"""
        if "ResultDescription" not in v:
            raise ValueError("One of the items MUST be the IRI 'ResultDescription'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/result/desc/1",
                "type": ["ResultDescription"],
                "name": "Final Grade",
                "resultType": "LetterGrade"
            }
        }


class BaseAchievementSchema(BaseModel):
    """Base achievement schema with common fields"""
    id: str = Field(description="REQUIRED: Unique identifier (IRI) for the achievement")
    inLanguage: Optional[str] = Field(None, min_length=2, description="OPTIONAL: Language code (e.g., 'en', 'es')")
    version: Optional[str] = Field(None, description="OPTIONAL: Version of the achievement")


class RelatedAchievementSchema(BaseAchievementSchema):
    """Related achievement schema"""
    type: List[str] = Field(default=["Related"])

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'Related'"""
        if "Related" not in v:
            raise ValueError("One of the items MUST be the IRI 'Related'")
        return v


class AchievementSchema(BaseAchievementSchema):
    """Achievement/Badge definition schema"""
    name: str = Field(description="REQUIRED: Name of the achievement")
    type: List[AchievementTypeEnum] = Field(default=[AchievementTypeEnum.ACHIEVEMENT], description="REQUIRED: Must include 'Achievement','Badge', 'Certificate', 'Degree', 'Assessment', 'Assignment', 'AssociateDegree', 'Award', 'Certification', 'CommunityService', 'Competency', 'CoCurricular', 'Diploma', 'DoctoralDegree', 'Fieldwork', 'GeneralEducationDevelopment', 'JourneymanCertificate', 'LearningProgram', 'License', 'Membership', 'ProfessionalDoctorate', 'QualityAssuranceCredential', 'MasterCertificate', 'MasterDegree', 'MicroCredential', 'ResearchDoctorate', 'SecondarySchoolDiploma', 'EventAttendance', 'ApprenticeshipCertificate')")
    alignment: Optional[List[AlignmentSchema]] = Field(None, description="OPTIONAL: Alignment objects")
    creator: Optional["ProfileSchema"] = Field(None, description="OPTIONAL: Profile that created this achievement")
    creditsAvailable: Optional[float] = Field(None, description="OPTIONAL: Number of credits available")
    criteria: CriteriaSchema = Field(description="REQUIRED: Criteria for earning this achievement")
    description: str = Field(description="REQUIRED: Description of the achievement")
    endorsement: Optional[List["EndorsementCredentialSchema"]] = Field(None, description="OPTIONAL: Endorsement credentials")
    endorsementJwt: Optional[List[CompactJWSSchema]] = Field(None, description="OPTIONAL: Endorsement JWTs")
    fieldOfStudy: Optional[str] = Field(None, description="OPTIONAL: Field of study")
    humanCode: Optional[str] = Field(None, description="OPTIONAL: Human-readable code")
    image: Optional[ImageSchema] = Field(None, description="OPTIONAL: Image representing the achievement")
    otherIdentifier: Optional[List[IdentifierEntrySchema]] = Field(None, description="OPTIONAL: Other identifiers")
    related: Optional[List[RelatedAchievementSchema]] = Field(None, description="OPTIONAL: Related achievements")
    resultDescription: Optional[List[ResultDescriptionSchema]] = Field(None, description="OPTIONAL: Result descriptions")
    specialization: Optional[str] = Field(None, description="OPTIONAL: Specialization")
    tag: Optional[List[str]] = Field(None, description="OPTIONAL: Tags for categorization")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[AchievementTypeEnum]) -> List[AchievementTypeEnum]:
        """Validate that type includes 'Achievement'"""
        if "Achievement" not in v:
            raise ValueError("The type MUST include the IRI 'Achievement'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "https://example.com/achievement/1",
                "type": ["Achievement"],
                "name": "Python Programming Badge",
                "description": "Demonstrates proficiency in Python",
                "criteria": {
                    "narrative": "Complete Python course with 80% or higher"
                },
                "image": {
                    "id": "https://example.com/badge-image.png",
                    "type": "Image"
                },
                "creditsAvailable": 3.0,
                "tag": ["programming", "python", "certification"],
                "fieldOfStudy": "Computer Science",
                "version": "1.0",
                "inLanguage": "en"
            },
            "examples": [
                {
                    "summary": "Minimal example (required fields only)",
                    "description": "Shows only the required fields: id, type, name, description, and criteria",
                    "value": {
                        "id": "https://example.com/achievement/1",
                        "type": ["Achievement"],
                        "name": "Python Programming Badge",
                        "description": "Demonstrates proficiency in Python",
                        "criteria": {
                            "narrative": "Complete Python course with 80% or higher"
                        }
                    }
                },
                {
                    "summary": "Full example (with optional fields)",
                    "description": "Shows all required fields plus several optional fields like image, creditsAvailable, tag, etc.",
                    "value": {
                        "id": "https://example.com/achievement/1",
                        "type": ["Achievement"],
                        "name": "Python Programming Badge",
                        "description": "Demonstrates proficiency in Python",
                        "criteria": {
                            "narrative": "Complete Python course with 80% or higher"
                        },
                        "image": {
                            "id": "https://example.com/badge-image.png",
                            "type": "Image"
                        },
                        "creditsAvailable": 3.0,
                        "tag": ["programming", "python", "certification"],
                        "fieldOfStudy": "Computer Science",
                        "version": "1.0",
                        "inLanguage": "en"
                    }
                }
            ]
        }


class ResultSchema(BaseModel):
    """Result schema"""
    type: List[str]
    achievedLevel: Optional[str] = None
    alignment: Optional[List[AlignmentSchema]] = None
    resultDescription: Optional[str] = None
    status: Optional[ResultStatusTypeEnum] = None
    value: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'Result'"""
        if "Result" not in v:
            raise ValueError("One of the items MUST be the IRI 'Result'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": ["Result"],
                "status": "Completed",
                "value": "A"
            }
        }


class AchievementSubjectSchema(BaseModel):
    """Achievement subject (recipient) schema"""
    id: Optional[str] = None
    type: List[str] = Field(default=["AchievementSubject"])
    activityEndDate: Optional[datetime] = None
    activityStartDate: Optional[datetime] = None
    creditsEarned: Optional[float] = None
    achievement: AchievementSchema
    identifier: Optional[List[IdentityObjectSchema]] = None
    image: Optional[ImageSchema] = None
    licenseNumber: Optional[str] = None
    narrative: Optional[str] = None
    result: Optional[List[ResultSchema]] = None
    role: Optional[str] = None
    source: Optional["ProfileSchema"] = None
    term: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: List[str]) -> List[str]:
        """Validate that type includes 'AchievementSubject'"""
        if "AchievementSubject" not in v:
            raise ValueError("One of the items MUST be the IRI 'AchievementSubject'")
        return v

    @model_validator(mode="after")
    def validate_id_or_identifier(self):
        """Either id or at least one identifier MUST be supplied"""
        if not self.id and (not self.identifier or len(self.identifier) == 0):
            raise ValueError("Either id or at least one identifier MUST be supplied")
        return self

    @field_serializer("activityEndDate", "activityStartDate")
    def serialize_datetime(self, value: Optional[datetime], _info) -> Optional[str]:
        """Serialize datetime to ISO string"""
        if value is None:
            return None
        return value.isoformat()

    def model_dump(self, **kwargs):
        """Remove id from output if it's None"""
        data = super().model_dump(**kwargs)
        if data.get("id") is None:
            data.pop("id", None)
        return data

    class Config:
        json_schema_extra = {
            "example": {
                "type": ["AchievementSubject"],
                "achievement": {
                    "id": "https://example.com/achievement/1",
                    "type": ["Achievement"],
                    "name": "Python Badge",
                    "description": "Python proficiency",
                    "criteria": {"narrative": "Complete course"}
                }
            }
        }

# Update forward references after all classes are defined
def _update_forward_refs():
    """Update forward references to resolve circular imports"""
    # Import all needed schemas to make them available in namespace
    from .profile import ProfileSchema
    from .credential import EndorsementCredentialSchema
    
    # Make ProfileSchema available in this module's namespace for model_rebuild()
    import sys
    current_module = sys.modules[__name__]
    current_module.ProfileSchema = ProfileSchema
    current_module.EndorsementCredentialSchema = EndorsementCredentialSchema
    
    # Rebuild any models that use EndorsementCredentialSchema
    # ProfileSchema must be in namespace for model_rebuild() to resolve forward references
    AchievementSchema.model_rebuild()

# Note: _update_forward_refs() is called from __init__.py after all modules are loaded