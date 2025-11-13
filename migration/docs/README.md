# Badge Engine Documentation

Welcome to the Badge Engine documentation! This directory contains comprehensive guides for developing, deploying, and maintaining the Badge Engine platform.

## Documentation Index

### Getting Started

1. **[Migration Plan](../migration/migration_plan.md)** - Complete migration strategy from T3 to Python/Rust
2. **[API Documentation](api_documentation.md)** - Complete API reference
3. **[Deployment Guide](deployment.md)** - Production deployment instructions
4. **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions

### Migration Guides

Located in `/migration/`:

- `migration_plan.md` - Complete roadmap
- `step_1_database_schema.md` - PostgreSQL schema design
- Additional step-by-step guides for each phase

### Technical Documentation

- **Architecture Overview** - System design and component interactions
- **Database Schema** - Entity relationships and data models
- **Authentication Flow** - Entra ID SSO implementation
- **SCIM Integration** - User and group provisioning
- **Badge Baking** - Rust-powered badge image processing

## Quick Links

### For Developers

- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [API Documentation](api_documentation.md)

### For Administrators

- [Deployment Guide](deployment.md)
- [Entra ID Configuration](deployment.md#entra-id-configuration)
- [SCIM Setup](deployment.md#entra-id-configuration)
- [Monitoring](deployment.md#monitoring-and-maintenance)

### For Troubleshooting

- [Common Issues](troubleshooting.md)
- [Error Messages](troubleshooting.md#common-error-messages)
- [Log Locations](troubleshooting.md#log-files)
- [Support Channels](troubleshooting.md#getting-help)

---

## Development Setup

### Prerequisites

- Python 3.11+
- Rust 1.75+ (for badge baking extension)
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose
- Node.js 20+ (for frontend)

### Quick Start

1. **Clone repository:**
   ```bash
   git clone https://github.com/your-org/badge-engine.git
   cd badge-engine
   ```

2. **Set up environment:**
   ```bash
   cp docker/.env.example docker/.env
   # Edit .env with your configuration
   ```

3. **Start services:**
   ```bash
   cd docker
   docker-compose up -d
   ```

4. **Initialize database:**
   ```bash
   docker-compose exec backend python -c "from backend.db.base import init_db; init_db()"
   ```

5. **Access application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs

### Running Tests

```bash
# Install test dependencies
pip install -r backend/requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=backend --cov-report=html
```

---

## Architecture Overview

### Technology Stack

**Backend:**
- FastAPI (Python 3.11)
- SQLAlchemy ORM
- PostgreSQL 16
- Redis (caching)
- Celery (background tasks)
- Rust (badge baking via PyO3)

**Frontend:**
- React 18
- Next.js 14
- Tailwind CSS

**Authentication:**
- Microsoft Entra ID (Azure AD)
- OAuth 2.0 / OpenID Connect
- SCIM 2.0 provisioning

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- PostgreSQL (data persistence)
- Redis (cache & message broker)

### System Components

```
┌─────────────┐
│   React     │
│  Frontend   │
└──────┬──────┘
       │
       │ HTTPS
       ▼
┌─────────────┐
│    Nginx    │
│ Rev. Proxy  │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌─────────────┐ ┌─────────────┐
│   FastAPI   │ │    SCIM     │
│   Backend   │ │  Endpoints  │
└──────┬──────┘ └──────┬──────┘
       │                │
       ├────────────────┤
       │                │
       ▼                ▼
┌─────────────┐ ┌─────────────┐
│ PostgreSQL  │ │    Redis    │
│  Database   │ │    Cache    │
└─────────────┘ └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │   Celery    │
                │   Workers   │
                └─────────────┘
```

### Key Features

- **Open Badge v3.0 Compliant** - Full spec implementation
- **SSO Authentication** - Entra ID integration
- **SCIM 2.0 Provisioning** - Automated user/group sync
- **Badge Baking** - Rust-powered image processing
- **Scalable Architecture** - Horizontal and vertical scaling
- **Comprehensive Testing** - Unit, integration, and E2E tests
- **Production Ready** - Docker, monitoring, logging

---

## API Overview

### Base URL

- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

### Authentication

All API requests (except public routes) require authentication via Bearer token:

```http
Authorization: Bearer <entra_id_jwt_token>
```

### Main Endpoints

- `/api/achievements` - Badge definitions
- `/api/issuers` - Issuer profiles
- `/api/award` - Badge awarding
- `/api/sign` - Credential signing
- `/scim/v2/Users` - SCIM user provisioning
- `/scim/v2/Groups` - SCIM group management
- `/auth/login` - Entra ID login
- `/health` - Health check

See [API Documentation](api_documentation.md) for complete reference.

---

## Database Schema

### Core Tables

- `users` - Authentication users
- `profiles` - Issuer organizations
- `achievements` - Badge definitions
- `achievement_subjects` - Badge recipients
- `achievement_credentials` - Awarded badges
- `proofs` - Cryptographic signatures
- `evidence` - Supporting evidence
- `results` - Achievement results

### Relationships

- Achievements belong to Issuers (Profiles)
- Credentials link Achievements to Recipients (Subjects)
- Proofs verify Credentials
- Evidence supports Credentials

See [Database Schema](../migration/step_1_database_schema.md) for complete schema.

---

## SCIM Integration

### Supported Operations

**Users:**
- List: `GET /scim/v2/Users`
- Get: `GET /scim/v2/Users/{id}`
- Create: `POST /scim/v2/Users`
- Update: `PUT /scim/v2/Users/{id}`
- Patch: `PATCH /scim/v2/Users/{id}`
- Delete: `DELETE /scim/v2/Users/{id}`

**Groups:**
- List: `GET /scim/v2/Groups`
- Get: `GET /scim/v2/Groups/{id}`
- Create: `POST /scim/v2/Groups`
- Update: `PUT /scim/v2/Groups/{id}`
- Patch: `PATCH /scim/v2/Groups/{id}` (membership management)
- Delete: `DELETE /scim/v2/Groups/{id}`

### Entra ID Setup

See [Deployment Guide - SCIM Configuration](deployment.md#entra-id-configuration) for step-by-step instructions.

---

## Badge Baking

### Overview

Badge baking embeds OpenBadgeCredentials into badge images per Open Badge v3.0 spec:

- **PNG:** iTXt chunk with keyword `openbadgecredential`
- **SVG:** `<openbadges:credential>` tag with base64-encoded credential

### Implementation

**Rust Module (Performance):**
- Located in `backend/rust_extension/`
- Built with PyO3 for Python bindings
- ~10x faster than pure Python

**Python Fallback:**
- Automatic fallback if Rust unavailable
- Uses Pillow for PNG processing
- Full spec compliance

### Usage

```python
from backend.services.badge_service import badge_service

# Bake credential into PNG
with open('badge.png', 'rb') as f:
    image_data = f.read()

credential = {...}  # OpenBadgeCredential dict
baked_image = badge_service.bake_png(image_data, credential)

# Extract credential
extracted = badge_service.extract_png(baked_image)
```

---

## Security

### Authentication

- Microsoft Entra ID SSO
- OAuth 2.0 / OpenID Connect
- JWT token validation
- Group-based RBAC

### Authorization

- Admin endpoints: Require admin group membership
- Issuer endpoints: Require issuer group membership
- Resource ownership: Users can only modify their own resources

### Data Protection

- PostgreSQL with encrypted connections
- Redis password authentication
- Environment variable secrets
- HTTPS in production
- CORS configuration
- Rate limiting

### Compliance

- Open Badge v3.0 spec compliance
- SCIM 2.0 spec compliance
- GDPR considerations (user data handling)

---

## Monitoring and Logging

### Health Checks

- `/health` - Application health
- Docker health checks per service
- Database connection monitoring
- Redis availability checks

### Logging

**Locations:**
- Application: `/app/logs/error.log`
- Migration: `/app/logs/migration_errors.log`
- Nginx: `/var/log/nginx/`
- PostgreSQL: `/var/log/postgresql/`

**Log Levels:**
- DEBUG: Development debugging
- INFO: General information
- WARNING: Potential issues
- ERROR: Errors requiring attention
- CRITICAL: System failures

### Metrics

Recommended monitoring stack:
- Prometheus: Metrics collection
- Grafana: Visualization
- AlertManager: Alerting

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guide
- Development workflow
- Pull request process
- Testing requirements

---

## Support

### Documentation

- This documentation
- API reference
- Migration guides
- Troubleshooting

### Community

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and discussions
- Email: support@badge-engine.example.com

### Professional Support

For enterprise support, training, or custom development:
- Email: enterprise@badge-engine.example.com
- Website: https://badge-engine.example.com

---

## License

Badge Engine is open source software. See [LICENSE](../LICENSE) for details.

## Acknowledgments

- [IMS Global Learning Consortium](https://www.imsglobal.org/) - Open Badge specification
- [Digital Promise](https://digitalpromise.org/) - Original badge-engine implementation
- [Microsoft](https://microsoft.com/) - Entra ID authentication platform

---

**Last Updated:** 2024-01-01  
**Version:** 2.0.0

