# Step 1: Database Migration - PostgreSQL Schema Design

## Overview

This document details the migration from MongoDB to PostgreSQL, including schema design, data types, relationships, and migration scripts.

## Design Principles

1. **Relational Integrity:** Use proper foreign keys and constraints
2. **UUID Primary Keys:** Better distribution and security than sequential IDs
3. **JSONB for Flexible Data:** Store arrays and nested objects where appropriate
4. **Indexing Strategy:** Index foreign keys, frequently queried fields
5. **Timestamp Tracking:** Created/updated timestamps on all major tables
6. **Soft Deletes:** Consider soft delete patterns for critical data

## Schema Conversion

### Data Type Mapping

| Prisma/MongoDB | PostgreSQL |
|----------------|------------|
| String @id @db.ObjectId | UUID PRIMARY KEY |
| String | VARCHAR/TEXT |
| String[] | JSONB or VARCHAR[] |
| Int | INTEGER |
| Float | NUMERIC/FLOAT8 |
| Boolean | BOOLEAN |
| DateTime | TIMESTAMP WITH TIME ZONE |
| Json | JSONB |
| Enum | ENUM type or CHECK constraint |

## Core Tables

### 1. Users & Authentication

```sql
-- Users table (replaces User from auth.prisma)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    image VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_super_user BOOLEAN DEFAULT FALSE,
    role VARCHAR(50),
    last_login TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- Accounts table (OAuth providers)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    provider_account_id VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    access_token TEXT,
    id_token TEXT,
    expires_at INTEGER,
    token_type VARCHAR(50),
    scope TEXT,
    session_state TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider, provider_account_id)
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_token VARCHAR(500) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- Verification tokens
CREATE TABLE verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(identifier, token)
);
```

### 2. Profiles (Issuers)

```sql
-- Profiles table (issuer organizations)
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) UNIQUE NOT NULL, -- Unique URI for the Profile
    type JSONB NOT NULL, -- ["Profile"]
    name VARCHAR(500),
    url VARCHAR(500),
    phone VARCHAR(50),
    description TEXT,
    email VARCHAR(255),
    email_verified BOOLEAN,
    receive_notifications BOOLEAN,
    official VARCHAR(255),
    parent_org_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    family_name VARCHAR(255),
    given_name VARCHAR(255),
    additional_name VARCHAR(255),
    patronymic_name VARCHAR(255),
    honorific_prefix VARCHAR(50),
    honorific_suffix VARCHAR(50),
    family_name_prefix VARCHAR(50),
    date_of_birth DATE,
    role VARCHAR(100),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    has_agreed_terms BOOLEAN,
    agreed_terms_version VARCHAR(20),
    endorsement_jwt JSONB, -- array of JWT strings
    image_id UUID REFERENCES images(id) ON DELETE SET NULL,
    address_id UUID REFERENCES addresses(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_profiles_email ON profiles(email);
CREATE INDEX idx_profiles_parent_org ON profiles(parent_org_id);
CREATE INDEX idx_profiles_active ON profiles(is_active);

-- Addresses
CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type JSONB NOT NULL,
    address_country VARCHAR(100),
    address_country_code VARCHAR(2),
    address_region VARCHAR(100),
    address_locality VARCHAR(100),
    street_address VARCHAR(255),
    post_office_box_number VARCHAR(50),
    postal_code VARCHAR(20),
    geo_id UUID REFERENCES geo_coordinates(id) ON DELETE SET NULL
);

-- Geo Coordinates
CREATE TABLE geo_coordinates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) DEFAULT 'GeoCoordinates',
    latitude FLOAT8 NOT NULL,
    longitude FLOAT8 NOT NULL
);
```

### 3. Achievements

```sql
-- Achievement types enum
CREATE TYPE achievement_type_enum AS ENUM (
    'Achievement', 'ApprenticeshipCertificate', 'Assessment', 'Assignment',
    'AssociateDegree', 'Award', 'Badge', 'BachelorDegree', 'Certificate',
    'CertificateOfCompletion', 'Certification', 'CommunityService', 'Competency',
    'CoCurricular', 'Degree', 'Diploma', 'DoctoralDegree', 'Fieldwork',
    'GeneralEducationDevelopment', 'JourneymanCertificate', 'LearningProgram',
    'License', 'Membership', 'ProfessionalDoctorate', 'QualityAssuranceCredential',
    'MasterCertificate', 'MasterDegree', 'MicroCredential', 'ResearchDoctorate',
    'SecondarySchoolDiploma', 'ext:EventAttendance'
);

-- Achievements table
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) UNIQUE NOT NULL,
    type JSONB NOT NULL,
    achievement_type achievement_type_enum,
    name VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    criteria JSONB NOT NULL, -- {id, narrative}
    credits_available NUMERIC,
    field_of_study VARCHAR(255),
    human_code VARCHAR(100),
    in_language VARCHAR(10),
    specialization VARCHAR(255),
    tags JSONB, -- array of strings
    version VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE,
    endorsement_jwt JSONB,
    creator_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    image_id UUID REFERENCES images(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_achievements_creator ON achievements(creator_id);
CREATE INDEX idx_achievements_public ON achievements(is_public);
CREATE INDEX idx_achievements_name ON achievements(name);
CREATE INDEX idx_achievements_tags ON achievements USING GIN(tags);

-- Related achievements
CREATE TABLE related_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    related_iri VARCHAR(500) NOT NULL,
    type JSONB NOT NULL,
    in_language VARCHAR(10),
    version VARCHAR(50)
);

CREATE INDEX idx_related_achievements ON related_achievements(achievement_id);
```

### 4. Alignments

```sql
CREATE TYPE alignment_target_type_enum AS ENUM (
    'ceasn:Competency', 'ceterms:Credential', 'CFItem', 'CFRubric',
    'CFRubricCriterion', 'CFRubricCriterionLevel', 'CTDL'
);

CREATE TABLE alignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type JSONB NOT NULL,
    target_code VARCHAR(255),
    target_description TEXT,
    target_name VARCHAR(500) NOT NULL,
    target_framework VARCHAR(255),
    target_type alignment_target_type_enum,
    target_url VARCHAR(500) NOT NULL
);

-- Achievement-Alignment junction table
CREATE TABLE achievement_alignments (
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    alignment_id UUID NOT NULL REFERENCES alignments(id) ON DELETE CASCADE,
    PRIMARY KEY (achievement_id, alignment_id)
);

CREATE INDEX idx_achievement_alignments_achievement ON achievement_alignments(achievement_id);
CREATE INDEX idx_achievement_alignments_alignment ON achievement_alignments(alignment_id);
```

### 5. Images

```sql
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    type VARCHAR(50) DEFAULT 'Image',
    caption TEXT,
    encoded_image_data TEXT -- Base64 or data URI
);
```

### 6. Result Descriptions

```sql
CREATE TYPE result_type_enum AS ENUM (
    'GradePointAverage', 'LetterGrade', 'Percent', 'PerformanceLevel',
    'PredictedScore', 'RawScore', 'Result', 'RubricCriterion',
    'RubricCriterionLevel', 'RubricScore', 'ScaledScore', 'Status'
);

CREATE TYPE question_type_enum AS ENUM ('FILEQUESTION', 'TEXTQUESTION');
CREATE TYPE assessment_placement_enum AS ENUM ('Overview', 'WorkExample', 'Reflection');

CREATE TABLE result_descriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    type JSONB NOT NULL,
    name VARCHAR(500) NOT NULL,
    result_type result_type_enum NOT NULL,
    allowed_value JSONB, -- array of strings
    required_level VARCHAR(500),
    required_value VARCHAR(255),
    value_max VARCHAR(255),
    value_min VARCHAR(255),
    question_type question_type_enum NOT NULL,
    ui_placement assessment_placement_enum NOT NULL,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE
);

CREATE INDEX idx_result_descriptions_achievement ON result_descriptions(achievement_id);

-- Rubric Criterion Levels
CREATE TABLE rubric_criterion_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    type JSONB NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    level VARCHAR(255),
    points VARCHAR(50),
    result_description_id UUID REFERENCES result_descriptions(id) ON DELETE CASCADE
);

CREATE INDEX idx_rubric_levels_result_desc ON rubric_criterion_levels(result_description_id);
```

### 7. Achievement Subjects (Recipients)

```sql
CREATE TYPE identifier_type_enum AS ENUM (
    'name', 'sourcedId', 'systemId', 'productId', 'userName', 'accountId',
    'emailAddress', 'nationalIdentityNumber', 'isbn', 'issn', 'lisSourcedId',
    'oneRosterSourcedId', 'sisSourcedId', 'ltiContextId', 'ltiDeploymentId',
    'ltiToolId', 'ltiPlatformId', 'ltiUserId', 'identifier'
);

CREATE TABLE achievement_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500),
    type JSONB NOT NULL,
    activity_start_date TIMESTAMP WITH TIME ZONE,
    activity_end_date TIMESTAMP WITH TIME ZONE,
    credits_earned NUMERIC,
    license_number VARCHAR(255),
    narrative TEXT,
    role VARCHAR(255),
    term VARCHAR(100),
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    assessor_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    image_id UUID REFERENCES images(id) ON DELETE SET NULL
);

CREATE INDEX idx_achievement_subjects_achievement ON achievement_subjects(achievement_id);
CREATE INDEX idx_achievement_subjects_assessor ON achievement_subjects(assessor_id);

-- Identity Objects (for subject identification)
CREATE TABLE identity_objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) DEFAULT 'IdentityObject',
    hashed BOOLEAN NOT NULL,
    identity_hash VARCHAR(500) NOT NULL,
    identity_type identifier_type_enum NOT NULL,
    salt VARCHAR(255),
    achievement_subject_id UUID REFERENCES achievement_subjects(id) ON DELETE CASCADE
);

CREATE INDEX idx_identity_objects_subject ON identity_objects(achievement_subject_id);

-- Achievement Subject Profiles
CREATE TABLE achievement_subject_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500),
    url VARCHAR(500),
    phone VARCHAR(50),
    description TEXT,
    email VARCHAR(255),
    family_name VARCHAR(255),
    given_name VARCHAR(255),
    additional_name VARCHAR(255),
    patronymic_name VARCHAR(255),
    honorific_prefix VARCHAR(50),
    honorific_suffix VARCHAR(50),
    family_name_prefix VARCHAR(50),
    date_of_birth DATE,
    achievement_subject_id UUID UNIQUE NOT NULL REFERENCES achievement_subjects(id) ON DELETE CASCADE
);
```

### 8. Achievement Credentials

```sql
CREATE TABLE achievement_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) UNIQUE NOT NULL,
    context JSONB NOT NULL,
    type JSONB NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    awarded_date VARCHAR(50),
    valid_from VARCHAR(50) NOT NULL,
    valid_until VARCHAR(50),
    claimed BOOLEAN,
    endorsement_jwt JSONB,
    credential_subject_id UUID NOT NULL REFERENCES achievement_subjects(id) ON DELETE CASCADE,
    issuer_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    image_id UUID REFERENCES images(id) ON DELETE SET NULL,
    credential_status_id UUID REFERENCES credential_statuses(id) ON DELETE SET NULL,
    refresh_service_id UUID REFERENCES refresh_services(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_achievement_credentials_subject ON achievement_credentials(credential_subject_id);
CREATE INDEX idx_achievement_credentials_issuer ON achievement_credentials(issuer_id);
CREATE INDEX idx_achievement_credentials_iri ON achievement_credentials(iri);
```

### 9. Proofs

```sql
CREATE TABLE proofs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(100) NOT NULL,
    created TIMESTAMP WITH TIME ZONE,
    cryptosuite VARCHAR(100),
    challenge VARCHAR(500),
    domain VARCHAR(500),
    nonce VARCHAR(500),
    proof_purpose VARCHAR(100),
    proof_value TEXT,
    verification_method VARCHAR(500),
    achievement_credential_id UUID REFERENCES achievement_credentials(id) ON DELETE CASCADE,
    verifiable_credential_id UUID REFERENCES verifiable_credentials(id) ON DELETE CASCADE,
    endorsement_credential_id UUID REFERENCES endorsement_credentials(id) ON DELETE CASCADE
);

CREATE INDEX idx_proofs_achievement_cred ON proofs(achievement_credential_id);
CREATE INDEX idx_proofs_verifiable_cred ON proofs(verifiable_credential_id);
CREATE INDEX idx_proofs_endorsement_cred ON proofs(endorsement_credential_id);
```

### 10. Evidence

```sql
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500),
    type JSONB NOT NULL,
    narrative TEXT,
    name VARCHAR(500),
    description TEXT,
    genre VARCHAR(255),
    audience VARCHAR(255),
    achievement_credential_id UUID REFERENCES achievement_credentials(id) ON DELETE CASCADE
);

CREATE INDEX idx_evidence_credential ON evidence(achievement_credential_id);
```

### 11. Results

```sql
CREATE TYPE result_status_type_enum AS ENUM (
    'Completed', 'Enrolled', 'Failed', 'InProgress',
    'OnHold', 'Provisional', 'Withdrew'
);

CREATE TABLE results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type JSONB NOT NULL,
    achieved_level VARCHAR(500),
    result_description VARCHAR(500),
    status result_status_type_enum,
    value VARCHAR(255),
    achievement_subject_id UUID REFERENCES achievement_subjects(id) ON DELETE CASCADE
);

CREATE INDEX idx_results_subject ON results(achievement_subject_id);

-- Result Alignments
CREATE TABLE result_alignments (
    result_id UUID NOT NULL REFERENCES results(id) ON DELETE CASCADE,
    alignment_id UUID NOT NULL REFERENCES alignments(id) ON DELETE CASCADE,
    PRIMARY KEY (result_id, alignment_id)
);
```

### 12. Credential Status & Refresh Services

```sql
CREATE TABLE credential_statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL
);

CREATE TABLE refresh_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL
);

CREATE TABLE terms_of_use (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500),
    type VARCHAR(100) NOT NULL,
    achievement_credential_id UUID REFERENCES achievement_credentials(id) ON DELETE CASCADE,
    verifiable_credential_id UUID REFERENCES verifiable_credentials(id) ON DELETE CASCADE,
    endorsement_credential_id UUID REFERENCES endorsement_credentials(id) ON DELETE CASCADE
);
```

### 13. Verifiable Credentials

```sql
CREATE TABLE credential_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500)
);

CREATE TABLE verifiable_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    context JSONB NOT NULL,
    type JSONB NOT NULL,
    valid_from VARCHAR(50) NOT NULL,
    valid_until VARCHAR(50),
    issuer_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    credential_subject_id UUID NOT NULL REFERENCES credential_subjects(id) ON DELETE CASCADE,
    credential_status_id UUID REFERENCES credential_statuses(id) ON DELETE SET NULL,
    refresh_service_id UUID REFERENCES refresh_services(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_verifiable_credentials_issuer ON verifiable_credentials(issuer_id);
```

### 14. Endorsement Credentials

```sql
CREATE TABLE endorsement_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    type JSONB NOT NULL,
    endorsement_comment TEXT
);

CREATE TABLE endorsement_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    context JSONB NOT NULL,
    type JSONB NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    awarded_date VARCHAR(50),
    valid_from VARCHAR(50) NOT NULL,
    valid_until VARCHAR(50),
    credential_subject_id UUID NOT NULL REFERENCES endorsement_subjects(id) ON DELETE CASCADE,
    issuer_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    achievement_id UUID REFERENCES achievements(id) ON DELETE CASCADE,
    achievement_credential_id UUID REFERENCES achievement_credentials(id) ON DELETE CASCADE,
    credential_status_id UUID REFERENCES credential_statuses(id) ON DELETE SET NULL,
    refresh_service_id UUID REFERENCES refresh_services(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_endorsement_credentials_subject ON endorsement_credentials(credential_subject_id);
CREATE INDEX idx_endorsement_credentials_issuer ON endorsement_credentials(issuer_id);
```

### 15. Credential Schemas

```sql
CREATE TABLE credential_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iri VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL,
    achievement_credential_id UUID REFERENCES achievement_credentials(id) ON DELETE CASCADE,
    verifiable_credential_id UUID REFERENCES verifiable_credentials(id) ON DELETE CASCADE,
    endorsement_credential_id UUID REFERENCES endorsement_credentials(id) ON DELETE CASCADE,
    assessment_extension_id UUID REFERENCES assessment_extensions(id) ON DELETE CASCADE
);
```

### 16. Extensions

```sql
CREATE TABLE extensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    achievement_id UUID UNIQUE NOT NULL REFERENCES achievements(id) ON DELETE CASCADE
);

CREATE TABLE assessment_extensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context JSONB NOT NULL,
    type JSONB NOT NULL,
    supporting_research_and_rationale TEXT,
    resources TEXT,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    extensions_id UUID NOT NULL REFERENCES extensions(id) ON DELETE CASCADE
);
```

### 17. Identifier Entries

```sql
CREATE TABLE identifier_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) DEFAULT 'IdentifierEntry',
    identifier VARCHAR(500) NOT NULL,
    identifier_type identifier_type_enum NOT NULL,
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    achievement_id UUID REFERENCES achievements(id) ON DELETE CASCADE
);

CREATE INDEX idx_identifier_entries_profile ON identifier_entries(profile_id);
CREATE INDEX idx_identifier_entries_achievement ON identifier_entries(achievement_id);
```

### 18. Validity (MVP specific)

```sql
CREATE TYPE duration_enum AS ENUM ('YEARS', 'MONTHS', 'WEEKS', 'DAYS', 'HOURS');

CREATE TABLE validities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    never_expires BOOLEAN,
    achievement_id UUID UNIQUE NOT NULL REFERENCES achievements(id) ON DELETE CASCADE
);

CREATE TABLE date_ranges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    validity_id UUID UNIQUE NOT NULL REFERENCES validities(id) ON DELETE CASCADE
);

CREATE TABLE time_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number_input INTEGER NOT NULL,
    duration duration_enum NOT NULL,
    validity_id UUID UNIQUE NOT NULL REFERENCES validities(id) ON DELETE CASCADE
);
```

## Indexes Summary

Key indexes for performance:
- All foreign keys
- Email addresses (users, profiles)
- Frequently queried text fields (name, tags)
- JSONB fields with GIN indexes
- Composite indexes for junction tables

## Migration Script Outline

The Python migration script (`data_migration_script.py`) will:

1. Connect to MongoDB and PostgreSQL
2. Extract data from MongoDB collections
3. Transform ObjectIds to UUIDs (with mapping)
4. Handle array fields → JSONB conversion
5. Migrate relationships using UUID mapping
6. Validate data integrity after migration
7. Generate migration report

## Next Steps

1. Review schema design
2. Create SQL initialization script
3. Develop SQLAlchemy models
4. Write data migration script
5. Test migration with sample data
6. Validate Open Badge v3.0 compliance

