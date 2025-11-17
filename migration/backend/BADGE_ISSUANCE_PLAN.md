# Badge Issuance Implementation Plan

## ✅ Completed Tasks

### 1. Database Model
- ✅ Created `IssuedBadge` model in `db/models.py`
  - Stores JWT strings for issued badges
  - Tracks achievement_id and organization_id
  - Includes timestamps

### 2. API Endpoint Fixes
- ✅ Added missing `BaseModel` import from pydantic
- ✅ Added missing `achievement_id` field to `IssueBadgeRequest`
- ✅ Added `IssuedBadge` import to achievements router
- ✅ Updated `issue_badge_as_jwt_eddsa` to save badges to database
- ✅ Added error handling for missing DOMAIN environment variable
- ✅ Fixed duplicate import issue (uuid)

### 3. Test Infrastructure
- ✅ Created test script: `scripts/test_badge_issuance.py`
- ✅ Created key generation script: `scripts/generate_ed25519_key.py`

## 🔧 What Needs to Be Done

### 1. Environment Setup (REQUIRED)

#### Generate Ed25519 Key Pair
```bash
python scripts/generate_ed25519_key.py
```
This creates `private_key.pem` in the backend directory, which is required for signing badges.

#### Set Environment Variables
Ensure these are set in your `.env` file or environment:
- `DOMAIN`: The base domain for your badge service (e.g., `https://example.com`)
- `DATABASE_URL`: Database connection string (defaults to SQLite if not set)

### 2. Database Migration

The `IssuedBadge` table needs to be created in the database. You have two options:

#### Option A: Automatic (Recommended)
If `init_db()` is called on application startup (which it is in `api/main.py`), the table will be created automatically when you start the server.

#### Option B: Manual Migration
If using Alembic migrations:
```bash
# Create migration
alembic revision --autogenerate -m "Add issued_badges table"

# Apply migration
alembic upgrade head
```

### 3. Testing the Implementation

#### Start the API Server
```bash
uvicorn api.main:app --reload
```

#### Run the Test Script
```bash
python scripts/test_badge_issuance.py
```

The test script will:
1. Issue a test badge via the `/achievements/issue-vc-jwt` endpoint
2. Verify the badge was saved to the database
3. Test retrieving the badge via `/achievements/credentials/{badge_uuid}`

### 4. API Endpoint Usage

#### Issue a Badge
```bash
POST /achievements/issue-vc-jwt
Content-Type: application/json

{
  "achievement_iri": "https://example.com/achievements/test-achievement",
  "organization_name": "Test Organization",
  "organization_id": "org-123",
  "achievement_name": "Test Achievement",
  "achievement_type": "Badge",
  "narrative": "Achievement narrative",
  "description": "Achievement description",
  "achievement_id": "credential-123"
}
```

Response:
```json
{
  "message": "VC-JWT (EdDSA) created successfully",
  "badge_jwt": "eyJ...",
  "badge_uuid": "uuid-here",
  "credential_url": "/credentials/uuid-here"
}
```

#### Retrieve a Badge
```bash
GET /achievements/credentials/{badge_uuid}
Accept: text/plain
```

Returns the raw JWT string (for validators).

## 🐛 Known Issues / Improvements Needed

### 1. Private Key Path
- **Issue**: The `public_key()` function looks for `private_key.pem` in the current working directory
- **Current**: `with open("private_key.pem", "rb") as f:`
- **Fix Needed**: Use absolute path or path relative to backend directory
- **Recommendation**: Update to use `Path(__file__).parent.parent / "private_key.pem"`

### 2. JWT Encoding Issue
- **Issue**: Line 154 uses `jwt.encode()` with `public_key()` but the function returns an `Ed25519PublicKey` object, not a private key
- **Current**: `jwt.encode(jwt_payload, public_key(), algorithm='EdDSA', headers=JWT_JWK_HEADER)`
- **Fix Needed**: The function should return the private key, not the public key, OR create a separate function for the private key
- **Recommendation**: 
  - Rename `public_key()` to `get_private_key()` and return the private key
  - Create a separate `get_public_key()` function if needed
  - Update `JWT_JWK_HEADER` to use the public key function

### 3. Domain Parsing
- **Issue**: Line 87 in `create_payload()` assumes domain format `http://...` or `https://...`
- **Current**: `organization_domain_name = domain[7:].split(".")[0]`
- **Fix Needed**: More robust domain parsing that handles various formats
- **Recommendation**: Use `urllib.parse.urlparse()` for proper URL parsing

### 4. Error Handling
- **Issue**: Missing error handling for JWT encoding failures
- **Recommendation**: Add try/except around `jwt.encode()` and handle cryptography errors

### 5. Database Transaction Management
- **Issue**: If JWT encoding fails after database commit, the badge record might be inconsistent
- **Recommendation**: Consider wrapping in a transaction or validating JWT before saving

## 📋 Additional Features to Consider

### 1. Badge Validation Endpoint
Create an endpoint to validate issued badges:
```python
@router.post("/validate-badge")
async def validate_badge(jwt_string: str):
    # Decode and verify JWT signature
    # Return validation result
```

### 2. Badge Revocation
Add support for revoking badges:
- Add `revoked` boolean field to `IssuedBadge` model
- Add revocation endpoint
- Update retrieval endpoint to check revocation status

### 3. Badge Listing
Add endpoint to list all issued badges (with pagination):
```python
@router.get("/issued-badges")
async def list_issued_badges(skip: int = 0, limit: int = 100):
    # Query IssuedBadge table
```

### 4. Badge Metadata
Store additional metadata with issued badges:
- Recipient information
- Issuance date
- Expiration date
- Status (active, revoked, expired)

### 5. Integration with AchievementCredential Model
Consider using the existing `AchievementCredential` model instead of `IssuedBadge`:
- More comprehensive schema
- Better alignment with Open Badges spec
- Already has relationships to profiles and achievements

## 🔍 Testing Checklist

- [ ] Generate Ed25519 key pair
- [ ] Set DOMAIN environment variable
- [ ] Start API server
- [ ] Run test script
- [ ] Verify badge is saved to database
- [ ] Verify badge can be retrieved
- [ ] Test with Open Badges validator
- [ ] Test JWT signature verification
- [ ] Test error cases (missing key, invalid domain, etc.)

## 📚 Resources

- [Open Badges v3.0 Specification](https://www.imsglobal.org/spec/ob/v3p0/)
- [Ed25519 Cryptography](https://en.wikipedia.org/wiki/EdDSA)
- [JWT (JSON Web Token) Specification](https://datatracker.ietf.org/doc/html/rfc7519)
- [JWS (JSON Web Signature) Specification](https://datatracker.ietf.org/doc/html/rfc7515)

