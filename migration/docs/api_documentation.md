# Badge Engine API Documentation

## Overview

Badge Engine provides a RESTful API for managing Open Badge v3.0 compliant digital credentials. The API is built with FastAPI and secured with Microsoft Entra ID (Azure AD) SSO.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication

All API endpoints (except public routes) require Bearer token authentication using Microsoft Entra ID JWT tokens.

### Authentication Flow

1. Redirect user to `/auth/login`
2. User authenticates with Microsoft Entra ID
3. Callback to `/auth/callback` with authorization code
4. Exchange code for access token
5. Use access token in `Authorization` header: `Bearer <token>`

### Headers

```http
Authorization: Bearer <your_entra_id_jwt_token>
Content-Type: application/json
```

## Endpoints

### Health Check

#### GET /health

Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy"
}
```

---

### Authentication

#### GET /auth/login

Initiate Entra ID login flow. Redirects to Microsoft login page.

#### GET /auth/callback

OAuth2 callback endpoint. Handles authorization code exchange.

**Query Parameters:**
- `code`: Authorization code from Entra ID

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "...",
  "id_token": "..."
}
```

#### GET /auth/me

Get current authenticated user information.

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "name": "User Name",
  "groups": ["Issuers", "Badge Admins"]
}
```

#### POST /auth/logout

Logout current user.

**Response:**
```json
{
  "message": "Logged out successfully",
  "logout_url": "https://login.microsoftonline.com/..."
}
```

---

### Achievements

#### GET /api/achievements/

List all achievements.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 100)

**Response:**
```json
{
  "achievements": [...],
  "total": 42
}
```

#### GET /api/achievements/{achievement_id}

Get a specific achievement by ID.

**Response:**
```json
{
  "id": "uuid",
  "iri": "https://example.com/achievements/...",
  "type": ["Achievement"],
  "name": "Achievement Name",
  "description": "Achievement description",
  "criteria": {
    "narrative": "Criteria narrative"
  },
  ...
}
```

#### POST /api/achievements/

Create a new achievement.

**Requires:** Issuer role

**Request Body:**
```json
{
  "name": "New Achievement",
  "description": "Description of the achievement",
  "criteria": {
    "narrative": "How to earn this achievement"
  },
  "type": ["Achievement"],
  ...
}
```

#### PUT /api/achievements/{achievement_id}

Update an existing achievement.

**Requires:** Issuer role, must be achievement creator

#### DELETE /api/achievements/{achievement_id}

Delete an achievement.

**Requires:** Issuer role, must be achievement creator

---

### Issuers (Profiles)

#### GET /api/issuers/

List all issuer profiles.

#### GET /api/issuers/{issuer_id}

Get a specific issuer profile.

#### POST /api/issuers/

Create a new issuer profile.

**Requires:** Authenticated user

#### PUT /api/issuers/{issuer_id}

Update an issuer profile.

#### DELETE /api/issuers/{issuer_id}

Delete an issuer profile.

---

### Awards

#### POST /api/award/

Award a badge to a recipient.

**Requires:** Issuer role

**Request Body:**
```json
{
  "achievement_id": "achievement-uuid",
  "recipient": {
    "type": ["AchievementSubject"],
    "identifier": {
      "type": "email",
      "value": "recipient@example.com",
      "hashed": false
    }
  },
  "issued_on": "2024-01-01T00:00:00Z",
  "expires": "2025-01-01T00:00:00Z"
}
```

#### GET /api/award/history

Get award history for current user's organization.

---

### Signing

#### POST /api/sign/

Sign a credential with cryptographic proof.

**Request Body:**
```json
{
  "credential": {
    "@context": [...],
    "type": ["VerifiableCredential", "OpenBadgeCredential"],
    ...
  },
  "proof_type": "DataIntegrityProof"
}
```

#### POST /api/sign/verify

Verify a signed credential.

**Request Body:**
```json
{
  "credential": {
    "@context": [...],
    "type": ["VerifiableCredential", "OpenBadgeCredential"],
    "proof": {...}
  }
}
```

---

### SCIM 2.0 Endpoints

All SCIM endpoints require admin access.

#### GET /scim/v2/Users

List users with pagination and filtering.

**Query Parameters:**
- `startIndex` (int): Starting index (default: 1)
- `count` (int): Number of results (default: 100)
- `filter` (string): SCIM filter expression

**Example Filter:**
```
userName eq "user@example.com"
```

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 10,
  "startIndex": 1,
  "itemsPerPage": 10,
  "Resources": [
    {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
      "id": "uuid",
      "userName": "user@example.com",
      "name": {
        "formatted": "User Name",
        "givenName": "User",
        "familyName": "Name"
      },
      "emails": [{"value": "user@example.com", "primary": true}],
      "active": true,
      "groups": [],
      "meta": {
        "resourceType": "User",
        "created": "2024-01-01T00:00:00Z",
        "lastModified": "2024-01-01T00:00:00Z",
        "location": "/scim/v2/Users/uuid"
      }
    }
  ]
}
```

#### POST /scim/v2/Users

Create a new user.

**Request Body:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "newuser@example.com",
  "name": {
    "formatted": "New User",
    "givenName": "New",
    "familyName": "User"
  },
  "emails": [{"value": "newuser@example.com", "primary": true}],
  "active": true
}
```

#### GET /scim/v2/Users/{user_id}

Get a specific user.

#### PUT /scim/v2/Users/{user_id}

Replace a user (full update).

#### PATCH /scim/v2/Users/{user_id}

Partially update a user.

**Request Body:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "replace",
      "path": "active",
      "value": false
    }
  ]
}
```

#### DELETE /scim/v2/Users/{user_id}

Delete (deactivate) a user.

---

#### GET /scim/v2/Groups

List groups.

#### POST /scim/v2/Groups

Create a new group.

**Request Body:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "displayName": "New Group",
  "members": []
}
```

#### GET /scim/v2/Groups/{group_id}

Get a specific group.

#### PATCH /scim/v2/Groups/{group_id}

Update group membership.

**Request Body (Add Member):**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "add",
      "path": "members",
      "value": [
        {
          "value": "user-uuid",
          "display": "User Name"
        }
      ]
    }
  ]
}
```

**Request Body (Remove Member):**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "remove",
      "path": "members[value eq \"user-uuid\"]"
    }
  ]
}
```

#### DELETE /scim/v2/Groups/{group_id}

Delete a group.

---

#### GET /scim/v2/ServiceProviderConfig

Get SCIM service provider configuration.

#### GET /scim/v2/ResourceTypes

Get SCIM resource types.

#### GET /scim/v2/Schemas

Get SCIM schemas.

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Common Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `204 No Content`: Successful deletion
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- General API: 10 requests/second (burst: 20)
- SCIM endpoints: 5 requests/second (burst: 10)

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: Time when limit resets

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `skip`: Number of records to skip
- `limit`: Maximum number of records to return

**Response includes:**
- `total`: Total number of records
- `items`: Array of results

## Filtering

SCIM endpoints support filtering using SCIM filter expressions:

**Examples:**
```
userName eq "user@example.com"
displayName co "John"
active eq true
```

**Operators:**
- `eq`: Equal
- `ne`: Not equal
- `co`: Contains
- `sw`: Starts with
- `ew`: Ends with

## Versioning

API version is included in the URL path: `/api/v1/...`

Current version: v1

## SDKs and Client Libraries

- Python: `pip install badge-engine-client`
- JavaScript: `npm install @badge-engine/client`

## Support

For API support, contact: support@badge-engine.example.com

## Changelog

### v2.0.0 (2024-01-01)
- Migrated from T3 stack to Python/Rust
- Implemented Entra ID SSO
- Added SCIM 2.0 endpoints
- PostgreSQL database
- Enhanced badge baking with Rust

