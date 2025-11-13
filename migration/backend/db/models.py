"""
SQLAlchemy models for Badge Engine - Open Badge v3.0 compliant
Supports both PostgreSQL and SQLite
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Text,
    ForeignKey, Table, Enum as SQLEnum, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, CHAR
import enum
import uuid

from backend.db.base import Base, IS_SQLITE

# UUID type that works with both PostgreSQL and SQLite
class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36) for SQLite.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

# Use GUID for UUID columns (works with both PostgreSQL and SQLite)
# The GUID type always handles UUID conversion internally
# This wrapper allows UUID(as_uuid=True) syntax to work
def UUID(*args, **kwargs):
    """UUID type that works with both PostgreSQL and SQLite"""
    # Always return GUID - it handles UUID conversion internally
    # The as_uuid=True parameter is ignored since GUID always works with UUID objects
    return GUID()

# JSON type that works with both PostgreSQL and SQLite
if IS_SQLITE:
    # SQLite: Use Text with JSON serialization
    from sqlalchemy import JSON
    JSONB = JSON  # Alias JSONB to JSON for SQLite
else:
    # PostgreSQL: Use native JSONB
    from sqlalchemy.dialects.postgresql import JSONB


# ============================================================================
# Enums
# ============================================================================

class AchievementTypeEnum(str, enum.Enum):
    """Achievement types as per Open Badge v3.0"""
    ACHIEVEMENT = "Achievement"
    APPRENTICESHIP_CERTIFICATE = "ApprenticeshipCertificate"
    ASSESSMENT = "Assessment"
    ASSIGNMENT = "Assignment"
    ASSOCIATE_DEGREE = "AssociateDegree"
    AWARD = "Award"
    BADGE = "Badge"
    BACHELOR_DEGREE = "BachelorDegree"
    CERTIFICATE = "Certificate"
    CERTIFICATE_OF_COMPLETION = "CertificateOfCompletion"
    CERTIFICATION = "Certification"
    COMMUNITY_SERVICE = "CommunityService"
    COMPETENCY = "Competency"
    CO_CURRICULAR = "CoCurricular"
    DEGREE = "Degree"
    DIPLOMA = "Diploma"
    DOCTORAL_DEGREE = "DoctoralDegree"
    FIELDWORK = "Fieldwork"
    GENERAL_EDUCATION_DEVELOPMENT = "GeneralEducationDevelopment"
    JOURNEYMAN_CERTIFICATE = "JourneymanCertificate"
    LEARNING_PROGRAM = "LearningProgram"
    LICENSE = "License"
    MEMBERSHIP = "Membership"
    PROFESSIONAL_DOCTORATE = "ProfessionalDoctorate"
    QUALITY_ASSURANCE_CREDENTIAL = "QualityAssuranceCredential"
    MASTER_CERTIFICATE = "MasterCertificate"
    MASTER_DEGREE = "MasterDegree"
    MICRO_CREDENTIAL = "MicroCredential"
    RESEARCH_DOCTORATE = "ResearchDoctorate"
    SECONDARY_SCHOOL_DIPLOMA = "SecondarySchoolDiploma"
    EVENT_ATTENDANCE = "ext:EventAttendance"


class AlignmentTargetTypeEnum(str, enum.Enum):
    """Alignment target types"""
    CEASN_COMPETENCY = "ceasn:Competency"
    CETERMS_CREDENTIAL = "ceterms:Credential"
    CF_ITEM = "CFItem"
    CF_RUBRIC = "CFRubric"
    CF_RUBRIC_CRITERION = "CFRubricCriterion"
    CF_RUBRIC_CRITERION_LEVEL = "CFRubricCriterionLevel"
    CTDL = "CTDL"


class ResultTypeEnum(str, enum.Enum):
    """Result types"""
    GRADE_POINT_AVERAGE = "GradePointAverage"
    LETTER_GRADE = "LetterGrade"
    PERCENT = "Percent"
    PERFORMANCE_LEVEL = "PerformanceLevel"
    PREDICTED_SCORE = "PredictedScore"
    RAW_SCORE = "RawScore"
    RESULT = "Result"
    RUBRIC_CRITERION = "RubricCriterion"
    RUBRIC_CRITERION_LEVEL = "RubricCriterionLevel"
    RUBRIC_SCORE = "RubricScore"
    SCALED_SCORE = "ScaledScore"
    STATUS = "Status"


class ResultStatusTypeEnum(str, enum.Enum):
    """Result status types"""
    COMPLETED = "Completed"
    ENROLLED = "Enrolled"
    FAILED = "Failed"
    IN_PROGRESS = "InProgress"
    ON_HOLD = "OnHold"
    PROVISIONAL = "Provisional"
    WITHDREW = "Withdrew"


class IdentifierTypeEnum(str, enum.Enum):
    """Identifier types"""
    NAME = "name"
    SOURCED_ID = "sourcedId"
    SYSTEM_ID = "systemId"
    PRODUCT_ID = "productId"
    USER_NAME = "userName"
    ACCOUNT_ID = "accountId"
    EMAIL_ADDRESS = "emailAddress"
    NATIONAL_IDENTITY_NUMBER = "nationalIdentityNumber"
    ISBN = "isbn"
    ISSN = "issn"
    LIS_SOURCED_ID = "lisSourcedId"
    ONE_ROSTER_SOURCED_ID = "oneRosterSourcedId"
    SIS_SOURCED_ID = "sisSourcedId"
    LTI_CONTEXT_ID = "ltiContextId"
    LTI_DEPLOYMENT_ID = "ltiDeploymentId"
    LTI_TOOL_ID = "ltiToolId"
    LTI_PLATFORM_ID = "ltiPlatformId"
    LTI_USER_ID = "ltiUserId"
    IDENTIFIER = "identifier"


class QuestionTypeEnum(str, enum.Enum):
    """Question types (internal use)"""
    FILE_QUESTION = "FILEQUESTION"
    TEXT_QUESTION = "TEXTQUESTION"


class AssessmentPlacementEnum(str, enum.Enum):
    """Assessment placement (internal use)"""
    OVERVIEW = "Overview"
    WORK_EXAMPLE = "WorkExample"
    REFLECTION = "Reflection"


class DurationEnum(str, enum.Enum):
    """Duration units"""
    YEARS = "YEARS"
    MONTHS = "MONTHS"
    WEEKS = "WEEKS"
    DAYS = "DAYS"
    HOURS = "HOURS"


# ============================================================================
# Association Tables (Many-to-Many)
# ============================================================================

achievement_alignments = Table(
    'achievement_alignments',
    Base.metadata,
    Column('achievement_id', UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'), primary_key=True),
    Column('alignment_id', UUID(as_uuid=True), ForeignKey('alignments.id', ondelete='CASCADE'), primary_key=True)
)

result_alignments = Table(
    'result_alignments',
    Base.metadata,
    Column('result_id', UUID(as_uuid=True), ForeignKey('results.id', ondelete='CASCADE'), primary_key=True),
    Column('alignment_id', UUID(as_uuid=True), ForeignKey('alignments.id', ondelete='CASCADE'), primary_key=True)
)


# ============================================================================
# Authentication Models
# ============================================================================

class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    email_verified = Column(Boolean, default=False)
    image = Column(String(500))
    is_active = Column(Boolean, default=True, index=True)
    is_super_user = Column(Boolean, default=False)
    role = Column(String(50))
    last_login = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    """OAuth account model"""
    __tablename__ = 'accounts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    provider_account_id = Column(String(255), nullable=False)
    refresh_token = Column(Text)
    access_token = Column(Text)
    id_token = Column(Text)
    expires_at = Column(Integer)
    token_type = Column(String(50))
    scope = Column(Text)
    session_state = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="accounts")


class Session(Base):
    """Session model"""
    __tablename__ = 'sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    expires = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")


class VerificationToken(Base):
    """Verification token model"""
    __tablename__ = 'verification_tokens'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String(255), nullable=False)
    token = Column(String(500), unique=True, nullable=False)
    expires = Column(DateTime(timezone=True), nullable=False)


# ============================================================================
# Geographic Models
# ============================================================================

class GeoCoordinates(Base):
    """Geographic coordinates"""
    __tablename__ = 'geo_coordinates'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), default='GeoCoordinates')
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Relationships
    addresses = relationship("Address", back_populates="geo")


class Address(Base):
    """Address model"""
    __tablename__ = 'addresses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(JSONB, nullable=False)  # Array of strings
    address_country = Column(String(100))
    address_country_code = Column(String(2))
    address_region = Column(String(100))
    address_locality = Column(String(100))
    street_address = Column(String(255))
    post_office_box_number = Column(String(50))
    postal_code = Column(String(20))
    geo_id = Column(UUID(as_uuid=True), ForeignKey('geo_coordinates.id', ondelete='SET NULL'))

    # Relationships
    geo = relationship("GeoCoordinates", back_populates="addresses")
    profiles = relationship("Profile", back_populates="address")


# ============================================================================
# Image Model
# ============================================================================

class Image(Base):
    """Image model for badges, profiles, etc."""
    __tablename__ = 'images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    type = Column(String(50), default='Image')
    caption = Column(Text)
    encoded_image_data = Column(Text)

    # Relationships
    profiles = relationship("Profile", back_populates="image")
    achievements = relationship("Achievement", back_populates="image")
    achievement_subjects = relationship("AchievementSubject", back_populates="image")
    achievement_credentials = relationship("AchievementCredential", back_populates="image")


# ============================================================================
# Profile Model (Issuers)
# ============================================================================

class Profile(Base):
    """Profile model for issuers and organizations"""
    __tablename__ = 'profiles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), unique=True, nullable=False)
    type = Column(JSONB, nullable=False)
    name = Column(String(500))
    url = Column(String(500))
    phone = Column(String(50))
    description = Column(Text)
    email = Column(String(255), index=True)
    email_verified = Column(Boolean)
    receive_notifications = Column(Boolean)
    official = Column(String(255))
    parent_org_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='SET NULL'), index=True)
    family_name = Column(String(255))
    given_name = Column(String(255))
    additional_name = Column(String(255))
    patronymic_name = Column(String(255))
    honorific_prefix = Column(String(50))
    honorific_suffix = Column(String(50))
    family_name_prefix = Column(String(50))
    date_of_birth = Column(Date)
    role = Column(String(100))
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False)
    has_agreed_terms = Column(Boolean)
    agreed_terms_version = Column(String(20))
    endorsement_jwt = Column(JSONB)
    image_id = Column(UUID(as_uuid=True), ForeignKey('images.id', ondelete='SET NULL'))
    address_id = Column(UUID(as_uuid=True), ForeignKey('addresses.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    image = relationship("Image", back_populates="profiles")
    address = relationship("Address", back_populates="profiles")
    parent_org = relationship("Profile", remote_side=[id], back_populates="child_orgs")
    child_orgs = relationship("Profile", back_populates="parent_org")
    achievements = relationship("Achievement", back_populates="creator")
    achievement_credentials_issued = relationship("AchievementCredential", back_populates="issuer")
    verifiable_credentials_issued = relationship("VerifiableCredential", back_populates="issuer")
    endorsement_credentials_issued = relationship("EndorsementCredential", foreign_keys="EndorsementCredential.issuer_id", back_populates="issuer")
    endorsement_credentials_profile = relationship("EndorsementCredential", foreign_keys="EndorsementCredential.profile_id", back_populates="profile")
    identifier_entries = relationship("IdentifierEntry", back_populates="profile")


# ============================================================================
# Alignment Model
# ============================================================================

class Alignment(Base):
    """Alignment to educational frameworks"""
    __tablename__ = 'alignments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(JSONB, nullable=False)
    target_code = Column(String(255))
    target_description = Column(Text)
    target_name = Column(String(500), nullable=False)
    target_framework = Column(String(255))
    target_type = Column(SQLEnum(AlignmentTargetTypeEnum, name='alignment_target_type_enum'))
    target_url = Column(String(500), nullable=False)

    # Relationships
    achievements = relationship("Achievement", secondary=achievement_alignments, back_populates="alignments")
    results = relationship("Result", secondary=result_alignments, back_populates="alignments")


# ============================================================================
# Achievement Models
# ============================================================================

class Achievement(Base):
    """Achievement/Badge definition"""
    __tablename__ = 'achievements'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), unique=True, nullable=False, index=True)
    type = Column(JSONB, nullable=False)
    achievement_type = Column(SQLEnum(AchievementTypeEnum, name='achievement_type_enum'))
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    criteria = Column(JSONB, nullable=False)  # {id, narrative}
    credits_available = Column(Float)
    field_of_study = Column(String(255))
    human_code = Column(String(100))
    in_language = Column(String(10))
    specialization = Column(String(255))
    tags = Column(JSONB)  # Array of strings
    version = Column(String(50))
    is_public = Column(Boolean, default=False, index=True)
    endorsement_jwt = Column(JSONB)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='SET NULL'), index=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey('images.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("Profile", back_populates="achievements")
    image = relationship("Image", back_populates="achievements")
    alignments = relationship("Alignment", secondary=achievement_alignments, back_populates="achievements")
    related_achievements = relationship("RelatedAchievement", back_populates="achievement", cascade="all, delete-orphan")
    result_descriptions = relationship("ResultDescription", back_populates="achievement", cascade="all, delete-orphan")
    achievement_subjects = relationship("AchievementSubject", back_populates="achievement", cascade="all, delete-orphan")
    endorsement_credentials = relationship("EndorsementCredential", back_populates="achievement")
    identifier_entries = relationship("IdentifierEntry", back_populates="achievement")
    extensions = relationship("Extensions", back_populates="achievement", uselist=False, cascade="all, delete-orphan")


class RelatedAchievement(Base):
    """Related achievement references"""
    __tablename__ = 'related_achievements'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False, index=True)
    related_iri = Column(String(500), nullable=False)
    type = Column(JSONB, nullable=False)
    in_language = Column(String(10))
    version = Column(String(50))

    # Relationships
    achievement = relationship("Achievement", back_populates="related_achievements")


# ============================================================================
# Result Description Models
# ============================================================================

class ResultDescription(Base):
    """Result description for achievements"""
    __tablename__ = 'result_descriptions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    type = Column(JSONB, nullable=False)
    name = Column(String(500), nullable=False)
    result_type = Column(SQLEnum(ResultTypeEnum, name='result_type_enum'), nullable=False)
    allowed_value = Column(JSONB)  # Array of strings
    required_level = Column(String(500))
    required_value = Column(String(255))
    value_max = Column(String(255))
    value_min = Column(String(255))
    question_type = Column(SQLEnum(QuestionTypeEnum, name='question_type_enum'), nullable=False)
    ui_placement = Column(SQLEnum(AssessmentPlacementEnum, name='assessment_placement_enum'), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False, index=True)

    # Relationships
    achievement = relationship("Achievement", back_populates="result_descriptions")
    rubric_criterion_levels = relationship("RubricCriterionLevel", back_populates="result_description", cascade="all, delete-orphan")


class RubricCriterionLevel(Base):
    """Rubric criterion level"""
    __tablename__ = 'rubric_criterion_levels'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    type = Column(JSONB, nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    level = Column(String(255))
    points = Column(String(50))
    result_description_id = Column(UUID(as_uuid=True), ForeignKey('result_descriptions.id', ondelete='CASCADE'), index=True)

    # Relationships
    result_description = relationship("ResultDescription", back_populates="rubric_criterion_levels")


# ============================================================================
# Achievement Subject Models (Recipients)
# ============================================================================

class AchievementSubject(Base):
    """Recipient of an achievement"""
    __tablename__ = 'achievement_subjects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500))
    type = Column(JSONB, nullable=False)
    activity_start_date = Column(DateTime(timezone=True))
    activity_end_date = Column(DateTime(timezone=True))
    credits_earned = Column(Float)
    license_number = Column(String(255))
    narrative = Column(Text)
    role = Column(String(255))
    term = Column(String(100))
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False, index=True)
    assessor_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='SET NULL'), index=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey('images.id', ondelete='SET NULL'))

    # Relationships
    achievement = relationship("Achievement", back_populates="achievement_subjects")
    assessor = relationship("Profile")
    image = relationship("Image", back_populates="achievement_subjects")
    identity_objects = relationship("IdentityObject", back_populates="achievement_subject", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="achievement_subject", cascade="all, delete-orphan")
    profile = relationship("AchievementSubjectProfile", back_populates="achievement_subject", uselist=False, cascade="all, delete-orphan")
    achievement_credentials = relationship("AchievementCredential", back_populates="credential_subject")


class IdentityObject(Base):
    """Identity object for achievement subjects"""
    __tablename__ = 'identity_objects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), default='IdentityObject')
    hashed = Column(Boolean, nullable=False)
    identity_hash = Column(String(500), nullable=False)
    identity_type = Column(SQLEnum(IdentifierTypeEnum, name='identifier_type_enum'), nullable=False)
    salt = Column(String(255))
    achievement_subject_id = Column(UUID(as_uuid=True), ForeignKey('achievement_subjects.id', ondelete='CASCADE'), index=True)

    # Relationships
    achievement_subject = relationship("AchievementSubject", back_populates="identity_objects")


class AchievementSubjectProfile(Base):
    """Profile information for achievement subject"""
    __tablename__ = 'achievement_subject_profiles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500))
    url = Column(String(500))
    phone = Column(String(50))
    description = Column(Text)
    email = Column(String(255))
    family_name = Column(String(255))
    given_name = Column(String(255))
    additional_name = Column(String(255))
    patronymic_name = Column(String(255))
    honorific_prefix = Column(String(50))
    honorific_suffix = Column(String(50))
    family_name_prefix = Column(String(50))
    date_of_birth = Column(Date)
    achievement_subject_id = Column(UUID(as_uuid=True), ForeignKey('achievement_subjects.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Relationships
    achievement_subject = relationship("AchievementSubject", back_populates="profile")


class Result(Base):
    """Result for achievement subject"""
    __tablename__ = 'results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(JSONB, nullable=False)
    achieved_level = Column(String(500))
    result_description = Column(String(500))
    status = Column(SQLEnum(ResultStatusTypeEnum, name='result_status_type_enum'))
    value = Column(String(255))
    achievement_subject_id = Column(UUID(as_uuid=True), ForeignKey('achievement_subjects.id', ondelete='CASCADE'), index=True)

    # Relationships
    achievement_subject = relationship("AchievementSubject", back_populates="results")
    alignments = relationship("Alignment", secondary=result_alignments, back_populates="results")


# ============================================================================
# Credential Models
# ============================================================================

class CredentialStatus(Base):
    """Credential status information"""
    __tablename__ = 'credential_statuses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    type = Column(String(100), nullable=False)

    # Relationships
    achievement_credentials = relationship("AchievementCredential", back_populates="credential_status")
    verifiable_credentials = relationship("VerifiableCredential", back_populates="credential_status")
    endorsement_credentials = relationship("EndorsementCredential", back_populates="credential_status")


class RefreshService(Base):
    """Refresh service information"""
    __tablename__ = 'refresh_services'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    type = Column(String(100), nullable=False)

    # Relationships
    achievement_credentials = relationship("AchievementCredential", back_populates="refresh_service")
    verifiable_credentials = relationship("VerifiableCredential", back_populates="refresh_service")
    endorsement_credentials = relationship("EndorsementCredential", back_populates="refresh_service")


class AchievementCredential(Base):
    """Achievement credential (awarded badge)"""
    __tablename__ = 'achievement_credentials'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), unique=True, nullable=False, index=True)
    context = Column(JSONB, nullable=False)
    type = Column(JSONB, nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    awarded_date = Column(String(50))
    valid_from = Column(String(50), nullable=False)
    valid_until = Column(String(50))
    claimed = Column(Boolean)
    endorsement_jwt = Column(JSONB)
    credential_subject_id = Column(UUID(as_uuid=True), ForeignKey('achievement_subjects.id', ondelete='CASCADE'), nullable=False, index=True)
    issuer_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False, index=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey('images.id', ondelete='SET NULL'))
    credential_status_id = Column(UUID(as_uuid=True), ForeignKey('credential_statuses.id', ondelete='SET NULL'))
    refresh_service_id = Column(UUID(as_uuid=True), ForeignKey('refresh_services.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    credential_subject = relationship("AchievementSubject", back_populates="achievement_credentials")
    issuer = relationship("Profile", back_populates="achievement_credentials_issued")
    image = relationship("Image", back_populates="achievement_credentials")
    credential_status = relationship("CredentialStatus", back_populates="achievement_credentials")
    refresh_service = relationship("RefreshService", back_populates="achievement_credentials")
    proofs = relationship("Proof", back_populates="achievement_credential", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="achievement_credential", cascade="all, delete-orphan")
    credential_schemas = relationship("CredentialSchema", back_populates="achievement_credential", cascade="all, delete-orphan")
    terms_of_use = relationship("TermsOfUse", back_populates="achievement_credential", cascade="all, delete-orphan")
    endorsement_credentials = relationship("EndorsementCredential", back_populates="achievement_credential")


class Proof(Base):
    """Cryptographic proof"""
    __tablename__ = 'proofs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(100), nullable=False)
    created = Column(DateTime(timezone=True))
    cryptosuite = Column(String(100))
    challenge = Column(String(500))
    domain = Column(String(500))
    nonce = Column(String(500))
    proof_purpose = Column(String(100))
    proof_value = Column(Text)
    verification_method = Column(String(500))
    achievement_credential_id = Column(UUID(as_uuid=True), ForeignKey('achievement_credentials.id', ondelete='CASCADE'), index=True)
    verifiable_credential_id = Column(UUID(as_uuid=True), ForeignKey('verifiable_credentials.id', ondelete='CASCADE'), index=True)
    endorsement_credential_id = Column(UUID(as_uuid=True), ForeignKey('endorsement_credentials.id', ondelete='CASCADE'), index=True)

    # Relationships
    achievement_credential = relationship("AchievementCredential", back_populates="proofs")
    verifiable_credential = relationship("VerifiableCredential", back_populates="proofs")
    endorsement_credential = relationship("EndorsementCredential", back_populates="proofs")


class Evidence(Base):
    """Evidence for achievement credential"""
    __tablename__ = 'evidence'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500))
    type = Column(JSONB, nullable=False)
    narrative = Column(Text)
    name = Column(String(500))
    description = Column(Text)
    genre = Column(String(255))
    audience = Column(String(255))
    achievement_credential_id = Column(UUID(as_uuid=True), ForeignKey('achievement_credentials.id', ondelete='CASCADE'), index=True)

    # Relationships
    achievement_credential = relationship("AchievementCredential", back_populates="evidence")


class TermsOfUse(Base):
    """Terms of use for credentials"""
    __tablename__ = 'terms_of_use'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500))
    type = Column(String(100), nullable=False)
    achievement_credential_id = Column(UUID(as_uuid=True), ForeignKey('achievement_credentials.id', ondelete='CASCADE'))
    verifiable_credential_id = Column(UUID(as_uuid=True), ForeignKey('verifiable_credentials.id', ondelete='CASCADE'))
    endorsement_credential_id = Column(UUID(as_uuid=True), ForeignKey('endorsement_credentials.id', ondelete='CASCADE'))

    # Relationships
    achievement_credential = relationship("AchievementCredential", back_populates="terms_of_use")
    verifiable_credential = relationship("VerifiableCredential", back_populates="terms_of_use")
    endorsement_credential = relationship("EndorsementCredential", back_populates="terms_of_use")


class CredentialSchema(Base):
    """Credential schema reference"""
    __tablename__ = 'credential_schemas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    type = Column(String(100), nullable=False)
    achievement_credential_id = Column(UUID(as_uuid=True), ForeignKey('achievement_credentials.id', ondelete='CASCADE'))
    verifiable_credential_id = Column(UUID(as_uuid=True), ForeignKey('verifiable_credentials.id', ondelete='CASCADE'))
    endorsement_credential_id = Column(UUID(as_uuid=True), ForeignKey('endorsement_credentials.id', ondelete='CASCADE'))
    assessment_extension_id = Column(UUID(as_uuid=True), ForeignKey('assessment_extensions.id', ondelete='CASCADE'))

    # Relationships
    achievement_credential = relationship("AchievementCredential", back_populates="credential_schemas")
    verifiable_credential = relationship("VerifiableCredential", back_populates="credential_schemas")
    endorsement_credential = relationship("EndorsementCredential", back_populates="credential_schemas")
    assessment_extension = relationship("AssessmentExtension", back_populates="credential_schemas")


# ============================================================================
# Verifiable Credential Models
# ============================================================================

class CredentialSubject(Base):
    """Generic credential subject"""
    __tablename__ = 'credential_subjects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500))

    # Relationships
    verifiable_credentials = relationship("VerifiableCredential", back_populates="credential_subject")


class VerifiableCredential(Base):
    """Generic verifiable credential"""
    __tablename__ = 'verifiable_credentials'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    context = Column(JSONB, nullable=False)
    type = Column(JSONB, nullable=False)
    valid_from = Column(String(50), nullable=False)
    valid_until = Column(String(50))
    issuer_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    credential_subject_id = Column(UUID(as_uuid=True), ForeignKey('credential_subjects.id', ondelete='CASCADE'), nullable=False)
    credential_status_id = Column(UUID(as_uuid=True), ForeignKey('credential_statuses.id', ondelete='SET NULL'))
    refresh_service_id = Column(UUID(as_uuid=True), ForeignKey('refresh_services.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    issuer = relationship("Profile", back_populates="verifiable_credentials_issued")
    credential_subject = relationship("CredentialSubject", back_populates="verifiable_credentials")
    credential_status = relationship("CredentialStatus", back_populates="verifiable_credentials")
    refresh_service = relationship("RefreshService", back_populates="verifiable_credentials")
    proofs = relationship("Proof", back_populates="verifiable_credential", cascade="all, delete-orphan")
    credential_schemas = relationship("CredentialSchema", back_populates="verifiable_credential", cascade="all, delete-orphan")
    terms_of_use = relationship("TermsOfUse", back_populates="verifiable_credential", cascade="all, delete-orphan")


# ============================================================================
# Endorsement Credential Models
# ============================================================================

class EndorsementSubject(Base):
    """Subject of an endorsement"""
    __tablename__ = 'endorsement_subjects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    type = Column(JSONB, nullable=False)
    endorsement_comment = Column(Text)

    # Relationships
    endorsement_credentials = relationship("EndorsementCredential", back_populates="credential_subject")


class EndorsementCredential(Base):
    """Endorsement credential"""
    __tablename__ = 'endorsement_credentials'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iri = Column(String(500), nullable=False)
    context = Column(JSONB, nullable=False)
    type = Column(JSONB, nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    awarded_date = Column(String(50))
    valid_from = Column(String(50), nullable=False)
    valid_until = Column(String(50))
    credential_subject_id = Column(UUID(as_uuid=True), ForeignKey('endorsement_subjects.id', ondelete='CASCADE'), nullable=False, index=True)
    issuer_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    profile_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'))
    achievement_credential_id = Column(UUID(as_uuid=True), ForeignKey('achievement_credentials.id', ondelete='CASCADE'))
    credential_status_id = Column(UUID(as_uuid=True), ForeignKey('credential_statuses.id', ondelete='SET NULL'))
    refresh_service_id = Column(UUID(as_uuid=True), ForeignKey('refresh_services.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    credential_subject = relationship("EndorsementSubject", back_populates="endorsement_credentials")
    issuer = relationship("Profile", foreign_keys=[issuer_id], back_populates="endorsement_credentials_issued")
    profile = relationship("Profile", foreign_keys=[profile_id], back_populates="endorsement_credentials_profile")
    achievement = relationship("Achievement", back_populates="endorsement_credentials")
    achievement_credential = relationship("AchievementCredential", back_populates="endorsement_credentials")
    credential_status = relationship("CredentialStatus", back_populates="endorsement_credentials")
    refresh_service = relationship("RefreshService", back_populates="endorsement_credentials")
    proofs = relationship("Proof", back_populates="endorsement_credential", cascade="all, delete-orphan")
    credential_schemas = relationship("CredentialSchema", back_populates="endorsement_credential", cascade="all, delete-orphan")
    terms_of_use = relationship("TermsOfUse", back_populates="endorsement_credential", cascade="all, delete-orphan")


# ============================================================================
# Extension Models
# ============================================================================

class Extensions(Base):
    """Extensions container"""
    __tablename__ = 'extensions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Relationships
    achievement = relationship("Achievement", back_populates="extensions")
    assessment_extensions = relationship("AssessmentExtension", back_populates="extensions", cascade="all, delete-orphan")


class AssessmentExtension(Base):
    """Assessment extension"""
    __tablename__ = 'assessment_extensions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    context = Column(JSONB, nullable=False)
    type = Column(JSONB, nullable=False)
    supporting_research_and_rationale = Column(Text)
    resources = Column(Text)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False)
    extensions_id = Column(UUID(as_uuid=True), ForeignKey('extensions.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    achievement = relationship("Achievement")
    extensions = relationship("Extensions", back_populates="assessment_extensions")
    credential_schemas = relationship("CredentialSchema", back_populates="assessment_extension", cascade="all, delete-orphan")


# ============================================================================
# Identifier Entry Model
# ============================================================================

class IdentifierEntry(Base):
    """Identifier entry for profiles and achievements"""
    __tablename__ = 'identifier_entries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), default='IdentifierEntry')
    identifier = Column(String(500), nullable=False)
    identifier_type = Column(SQLEnum(IdentifierTypeEnum, name='identifier_type_enum'), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'), index=True)

    # Relationships
    profile = relationship("Profile", back_populates="identifier_entries")
    achievement = relationship("Achievement", back_populates="identifier_entries")


# ============================================================================
# Validity Models (MVP specific)
# ============================================================================

class Validity(Base):
    """Validity information"""
    __tablename__ = 'validities'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    never_expires = Column(Boolean)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Relationships
    achievement = relationship("Achievement")
    date_range = relationship("DateRange", back_populates="validity", uselist=False, cascade="all, delete-orphan")
    time_period = relationship("TimePeriod", back_populates="validity", uselist=False, cascade="all, delete-orphan")


class DateRange(Base):
    """Date range for validity"""
    __tablename__ = 'date_ranges'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    validity_id = Column(UUID(as_uuid=True), ForeignKey('validities.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Relationships
    validity = relationship("Validity", back_populates="date_range")


class TimePeriod(Base):
    """Time period for validity"""
    __tablename__ = 'time_periods'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number_input = Column(Integer, nullable=False)
    duration = Column(SQLEnum(DurationEnum, name='duration_enum'), nullable=False)
    validity_id = Column(UUID(as_uuid=True), ForeignKey('validities.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Relationships
    validity = relationship("Validity", back_populates="time_period")

