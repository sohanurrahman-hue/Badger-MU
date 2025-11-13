# Open Badges v3.0 API Implementation Review

**Review Date:** 2024  
**Specification:** Open Badges v3.0 OpenAPI Schema  
**Reference:** https://purl.imsglobal.org/spec/ob/v3p0/schema/openapi/ob_v3p0_oas.json

---

## Executive Summary

This review compares the current Badge Engine implementation against the official Open Badges v3.0 OpenAPI specification. The implementation has a solid foundation with well-structured schemas, but **critical endpoints are missing** and several compliance issues need to be addressed.

**Overall Compliance Status:** ⚠️ **Partial** - Core schemas are well-implemented, but API endpoints do not match the specification.

---

## 1. Endpoint Paths & Methods

### ❌ **CRITICAL: Missing Endpoints**

The OpenAPI spec defines 5 operations across 3 paths, but **none are implemented**:

| Spec Endpoint | Spec Method | Current Status | Current Endpoint |
|--------------|-------------|----------------|------------------|
| `/credentials` | GET | ❌ **MISSING** | N/A |
| `/credentials` | POST | ❌ **MISSING** | N/A |
| `/profile` | GET | ❌ **MISSING** | `/api/issuers/{id}` (different) |
| `/profile` | PUT | ❌ **MISSING** | `/api/issuers/{id}` (PUT exists but not spec-compliant) |
| `/discovery` | GET | ❌ **MISSING** | N/A |

### Current Implementation vs. Spec

**Current endpoints:**
- `/api/achievements` - Custom endpoint (not in spec)
- `/api/issuers` - Similar to `/profile` but different structure
- `/api/award` - Custom endpoint (not in spec)
- `/api/sign` - Custom endpoint (not in spec)

**Required Changes:**
1. Implement `/credentials` endpoint (GET and POST)
2. Implement `/profile` endpoint (GET and PUT) matching spec exactly
3. Implement `/discovery` endpoint (GET) for Service Description Document

---

## 2. Request/Response Schemas

### ✅ **Schemas Are Well-Implemented**

The Pydantic schemas in `backend/schemas/open-badges/` are **largely compliant** with the OpenAPI spec:

**✅ Correctly Implemented:**
- `AchievementCredentialSchema` - Matches spec structure
- `ProfileSchema` - Matches spec structure
- `EvidenceSchema`, `CredentialSchemaSchema`, `CredentialStatusSchema` - All correct
- `EndorsementCredential` - Correctly implemented
- `AchievementSubjectSchema` - Properly structured

**⚠️ Minor Issues:**
1. **Field naming**: Schemas use camelCase (correct for JSON), but need to verify all fields match spec exactly
2. **@context field**: Schema uses `context` but spec uses `@context` - need to verify serialization handles this
3. **Missing `GetOpenBadgeCredentialsResponse` schema**: This response wrapper is not defined

**Required Schema Additions:**
```python
# Missing: GetOpenBadgeCredentialsResponse
class GetOpenBadgeCredentialsResponse(BaseModel):
    credential: Optional[List[AchievementCredentialSchema]] = []
    compactJwsString: Optional[List[str]] = []  # Compact JWS format
```

---

## 3. Query Parameters & Pagination

### ❌ **Missing Query Parameters**

**GET `/credentials` should support:**
- `limit` (integer, minimum: 1) - ✅ Can be implemented
- `offset` (integer, minimum: 0) - ✅ Can be implemented  
- `since` (date-time, ISO8601) - ❌ **NOT IMPLEMENTED** anywhere

**Current pagination:**
- Uses `skip`/`limit` pattern (different from spec's `offset`/`limit`)
- No `since` parameter support
- No `X-Total-Count` header (found in old code but not current implementation)
- No Link header with pagination relations (`first`, `prev`, `next`, `last`)

**Required Changes:**
1. Change `skip` to `offset` for spec compliance
2. Add `since` parameter for filtering credentials by issue date
3. Add `X-Total-Count` response header
4. Implement Link header with pagination relations per RFC 8288

---

## 4. Error Handling

### ❌ **Missing Imsx_StatusInfo Schema**

The spec requires all error responses to use `Imsx_StatusInfo` format:

```json
{
  "imsx_codeMajor": "failure|processing|success|unsupported",
  "imsx_severity": "error|status|warning",
  "imsx_description": "Human readable description",
  "imsx_codeMinor": {
    "imsx_codeMinorField": [{
      "imsx_codeMinorFieldName": "system",
      "imsx_codeMinorFieldValue": "forbidden|fullsuccess|..."
    }]
  }
}
```

**Current Status:**
- ❌ `Imsx_StatusInfo` schema **NOT FOUND** in codebase
- Current error responses use FastAPI's default format
- No standardized error response structure

**Required Changes:**
1. Create `Imsx_StatusInfo` schema
2. Create `Imsx_CodeMinor` and `Imsx_CodeMinorField` schemas
3. Update all error handlers to return Imsx_StatusInfo format
4. Map HTTP status codes to appropriate `imsx_codeMajor` values

**Error Response Mapping:**
- 400 → `imsx_codeMajor: "failure"`, `imsx_severity: "error"`
- 401 → `imsx_codeMajor: "failure"`, `imsx_severity: "error"`
- 403 → `imsx_codeMajor: "failure"`, `imsx_severity: "error"`
- 404 → `imsx_codeMajor: "failure"`, `imsx_severity: "error"`
- 405 → `imsx_codeMajor: "failure"`, `imsx_severity: "error"`
- 500 → `imsx_codeMajor: "failure"`, `imsx_severity: "error"`

---

## 5. Security & OAuth2 Scopes

### ⚠️ **OAuth2 Implementation Mismatch**

**Spec Requirements:**
- Security scheme: `OAuth2ACG` (OAuth2 Authorization Code Grant)
- Required scopes:
  - `https://purl.imsglobal.org/spec/ob/v3p0/scope/credential.readonly`
  - `https://purl.imsglobal.org/spec/ob/v3p0/scope/credential.upsert`
  - `https://purl.imsglobal.org/spec/ob/v3p0/scope/profile.readonly`
  - `https://purl.imsglobal.org/spec/ob/v3p0/scope/profile.update`

**Current Implementation:**
- Uses Microsoft Entra ID (Azure AD) SSO
- Uses custom `AuthMiddleware` with JWT validation
- No scope-based authorization - uses group-based access control
- No OAuth2 scope validation per endpoint

**Required Changes:**
1. Implement OAuth2 scope extraction from JWT tokens
2. Create dependency functions to validate scopes:
   ```python
   def require_credential_readonly(token: str = Depends(oauth2_scheme)):
       # Validate scope: credential.readonly
   
   def require_credential_upsert(token: str = Depends(oauth2_scheme)):
       # Validate scope: credential.upsert
   ```
3. Map Entra ID scopes to Open Badges scopes (or implement custom scope system)
4. Update endpoints to use scope-based dependencies

**Note:** If using Entra ID, you may need to:
- Configure custom app roles/scopes in Entra ID
- Map Entra ID scopes to Open Badges scope URIs
- Or implement a scope mapping layer

---

## 6. Content Types

### ⚠️ **Missing text/plain Support**

**POST `/credentials` spec requirements:**
- Accepts `application/json` (AchievementCredential object) ✅
- Accepts `text/plain` (Compact JWS string) ❌ **NOT IMPLEMENTED**

**Compact JWS Format:**
- Pattern: `^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]+$`
- Three parts separated by dots (header.payload.signature)
- Used for VC-JWT proof format credentials

**Current Status:**
- Only `application/json` is supported
- No `text/plain` content type handling

**Required Changes:**
1. Add content-type negotiation to POST `/credentials`
2. Parse Compact JWS strings when `text/plain` is received
3. Return appropriate content type in response (200/201 should return same format as request)

---

## 7. Service Description Document

### ❌ **Missing Discovery Endpoint**

**GET `/discovery` Requirements:**
- Returns `ServiceDescriptionDocument` (OpenAPI 3.0 JSON)
- Must include:
  - `openapi` version string
  - `info` object with required fields:
    - `title`, `version`, `termsOfService`
    - `x-imssf-privacyPolicyUrl` (required extension)
  - `components.securitySchemes` with OAuth2ACG definition

**Current Status:**
- ❌ Endpoint does not exist
- ❌ ServiceDescriptionDocument schema not defined
- ✅ OpenAPI schema can be generated from FastAPI app, but needs customization

**Required Changes:**
1. Create `ServiceDescriptionDocument` schema
2. Implement GET `/discovery` endpoint
3. Generate OpenAPI JSON dynamically or serve static profiled version
4. Include required `x-imssf-*` extensions
5. Ensure security schemes match spec

---

## 8. Response Headers

### ❌ **Missing Required Headers**

**GET `/credentials` should return:**
- `X-Total-Count` header (integer) - ❌ Not implemented
- `Link` header with pagination relations - ❌ Not implemented

**Link Header Format (RFC 8288):**
```
Link: <https://example.org/credentials?limit=10&offset=0>; rel="first",
      <https://example.org/credentials?limit=10&offset=10>; rel="next",
      <https://example.org/credentials?limit=10&offset=90>; rel="last"
```

**Current Status:**
- No `X-Total-Count` header
- No `Link` header
- Pagination info only in response body (if at all)

**Required Changes:**
1. Add `X-Total-Count` header to GET `/credentials` responses
2. Implement Link header generation with proper URL construction
3. Calculate pagination links based on `offset`, `limit`, and total count

---

## 9. Response Status Codes

### ⚠️ **Status Code Compliance**

**Spec Requirements:**
- POST `/credentials`: 200 (replaced), 201 (created), 304 (not modified), 400, 401, 403, 404, 405, 500
- GET `/credentials`: 200, 400, 401, 403, 405, 500
- PUT `/profile`: 200, 202 (accepted), 304 (not modified), 400, 401, 403, 404, 405, 500
- GET `/profile`: 200, 400, 401, 403, 404, 405, 500

**Current Status:**
- Standard FastAPI error handling
- 304 (Not Modified) not implemented
- 202 (Accepted) not used for PUT `/profile`

**Required Changes:**
1. Implement 304 responses for conditional requests (If-None-Match, If-Modified-Since)
2. Consider 202 for async profile updates
3. Ensure all specified status codes are handled

---

## 10. Additional Findings

### ✅ **Positive Aspects:**
1. **Schema Quality**: Pydantic schemas are well-structured and mostly spec-compliant
2. **Database Models**: Good separation between API schemas and database models
3. **Type Safety**: Good use of type hints and Pydantic validation
4. **Error Handling**: Basic error handling infrastructure exists

### ⚠️ **Areas for Improvement:**
1. **Path Structure**: Current paths use `/api/` prefix, spec uses root-level paths
2. **Versioning**: No API versioning in paths (spec doesn't require it, but consider `/ims/ob/v3p0/` prefix)
3. **Documentation**: OpenAPI docs exist but may not match spec exactly

---

## Priority Action Items

### 🔴 **Critical (Must Fix for Compliance):**
1. ✅ Implement `/credentials` endpoint (GET, POST)
2. ✅ Implement `/profile` endpoint (GET, PUT) matching spec
3. ✅ Implement `/discovery` endpoint (GET)
4. ✅ Create `Imsx_StatusInfo` error response schema
5. ✅ Implement OAuth2 scope validation
6. ✅ Add `GetOpenBadgeCredentialsResponse` schema

### 🟡 **High Priority:**
7. ✅ Add `since` query parameter to GET `/credentials`
8. ✅ Implement `X-Total-Count` and `Link` headers
9. ✅ Add `text/plain` content type support for POST `/credentials`
10. ✅ Create `ServiceDescriptionDocument` schema and endpoint

### 🟢 **Medium Priority:**
11. ✅ Update error handlers to use `Imsx_StatusInfo`
12. ✅ Implement 304 (Not Modified) responses
13. ✅ Verify all field names match spec exactly
14. ✅ Add comprehensive integration tests

---

## Recommended Implementation Order

1. **Phase 1: Core Endpoints**
   - Create `Imsx_StatusInfo` schemas
   - Implement GET `/credentials` with pagination
   - Implement POST `/credentials` with dual content-type support

2. **Phase 2: Profile & Discovery**
   - Implement GET/PUT `/profile`
   - Implement GET `/discovery` with ServiceDescriptionDocument

3. **Phase 3: Security & Compliance**
   - Implement OAuth2 scope validation
   - Update all error responses to Imsx_StatusInfo
   - Add required headers (X-Total-Count, Link)

4. **Phase 4: Testing & Validation**
   - Integration tests against spec
   - Validate against official test suite (if available)
   - Performance testing

---

## Conclusion

The current implementation has a **solid foundation** with well-designed schemas and database models. However, **the API endpoints do not match the OpenAPI specification**. The main gaps are:

1. **Missing core endpoints** (`/credentials`, `/profile`, `/discovery`)
2. **Missing error response format** (Imsx_StatusInfo)
3. **Missing OAuth2 scope validation**
4. **Missing pagination headers and query parameters**

With focused development effort, the implementation can be brought into full compliance with the Open Badges v3.0 specification.

**Estimated Effort:** 2-3 weeks for full compliance implementation.

