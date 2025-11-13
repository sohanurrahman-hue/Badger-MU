"""
Open Badges v3.0 Pydantic Schemas
These schemas validate Open Badge v3.0 compliant data structures
"""

from .image import ImageSchema
from .identifier import IdentifierEntrySchema, IdentityObjectSchema
from .alignment import AlignmentSchema
from .proof import ProofSchema, CompactJWSSchema, DataIntegrityProofSchema
from .profile import (
    GeoCoordinatesSchema,
    AddressSchema,
    ProfileSchema,
    ProfileRefSchema,
)
from .achievement import (
    CriteriaSchema,
    RubricCriterionLevelSchema,
    ResultDescriptionSchema,
    AchievementSchema,
    RelatedAchievementSchema,
    ResultSchema,
    AchievementSubjectSchema,
)
from .credential import (
    EvidenceSchema,
    CredentialSchemaSchema,
    CredentialStatusSchema,
    CredentialSubjectSchema,
    RefreshServiceSchema,
    TermsOfUseSchema,
    EndorsementSubjectSchema,
    VerifiableCredentialSchema,
    AchievementCredentialSchema,
    EndorsementCredentialSchema,
    GetOpenBadgeCredentialsResponse,
)
from .status import (
    ImsxStatusInfo,
    ImsxCodeMinor,
    ImsxCodeMinorField,
    ImsxCodeMajorEnum,
    ImsxSeverityEnum,
    ImsxCodeMinorFieldValueEnum,
    create_imsx_status_info,
    map_http_status_to_imsx,
)
from .discovery import (
    ServiceDescriptionDocument,
    OpenApiInfo,
    OpenApiComponents,
    OpenApiSecuritySchemes,
    OpenApiOAuth2SecurityScheme,
)

__all__ = [
    # Image
    "ImageSchema",
    # Identifier
    "IdentifierEntrySchema",
    "IdentityObjectSchema",
    # Alignment
    "AlignmentSchema",
    # Proof
    "ProofSchema",
    "CompactJWSSchema",
    "DataIntegrityProofSchema",
    # Profile
    "GeoCoordinatesSchema",
    "AddressSchema",
    "ProfileSchema",
    "ProfileRefSchema",
    # Achievement
    "CriteriaSchema",
    "RubricCriterionLevelSchema",
    "ResultDescriptionSchema",
    "AchievementSchema",
    "RelatedAchievementSchema",
    "ResultSchema",
    "AchievementSubjectSchema",
    # Credential
    "EvidenceSchema",
    "CredentialSchemaSchema",
    "CredentialStatusSchema",
    "CredentialSubjectSchema",
    "RefreshServiceSchema",
    "TermsOfUseSchema",
    "EndorsementSubjectSchema",
    "VerifiableCredentialSchema",
    "AchievementCredentialSchema",
    "EndorsementCredentialSchema",
    "GetOpenBadgeCredentialsResponse",
    # Status
    "ImsxStatusInfo",
    "ImsxCodeMinor",
    "ImsxCodeMinorField",
    "ImsxCodeMajorEnum",
    "ImsxSeverityEnum",
    "ImsxCodeMinorFieldValueEnum",
    "create_imsx_status_info",
    "map_http_status_to_imsx",
    # Discovery
    "ServiceDescriptionDocument",
    "OpenApiInfo",
    "OpenApiComponents",
    "OpenApiSecuritySchemes",
    "OpenApiOAuth2SecurityScheme",
]

# Update forward references after all modules are loaded
# This resolves circular import issues by rebuilding models after all classes are defined
def _update_all_forward_refs():
    """Update forward references for all modules with circular dependencies"""
    from . import profile, achievement, credential
    
    # Import all schemas that are used in forward references
    from .profile import ProfileSchema
    from .credential import EndorsementCredentialSchema
    
    # Make both available in all module namespaces before rebuilding
    import sys
    
    # Inject into profile module
    profile_module = sys.modules[profile.__name__]
    profile_module.EndorsementCredentialSchema = EndorsementCredentialSchema
    
    # Inject into credential module
    credential_module = sys.modules[credential.__name__]
    credential_module.ProfileSchema = ProfileSchema
    
    # Inject into achievement module
    achievement_module = sys.modules[achievement.__name__]
    achievement_module.ProfileSchema = ProfileSchema
    achievement_module.EndorsementCredentialSchema = EndorsementCredentialSchema
    
    # Now rebuild in dependency order
    # 1. ProfileSchema first (doesn't depend on others being rebuilt)
    profile._update_forward_refs()
    
    # 2. Credential schemas (need ProfileSchema in namespace)
    if hasattr(credential, '_update_forward_refs'):
        credential._update_forward_refs()
    
    # 3. Achievement schemas last (depend on EndorsementCredentialSchema)
    achievement._update_forward_refs()

# Call after all imports are complete
_update_all_forward_refs()

