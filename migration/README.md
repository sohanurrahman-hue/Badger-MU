# Badge Engine Migration

This directory contains all migration artifacts, plans, and documentation for migrating the Badge Engine from T3 stack to Python/Rust.

## Migration Overview

**From:** T3 Stack (Next.js, NextAuth.js, Prisma, MongoDB, tRPC)  
**To:** Python (FastAPI), Rust (PyO3), PostgreSQL, React (unchanged)

## Directory Structure

```
migration/
├── README.md                    # This file
├── migration_plan.md            # Detailed migration roadmap
├── step_1_database_schema.md    # PostgreSQL schema design
├── step_2_backend_refactor.md   # FastAPI implementation
├── step_3_auth_sso_scim.md      # Authentication & SCIM setup
├── step_4_rust_integration.md   # Rust badge baking module
├── step_5_docker_setup.md       # Dockerization
├── step_6_testing.md            # Testing strategy
└── data_migration_script.py     # MongoDB to PostgreSQL migration script
```

## Migration Status

- [x] Directory structure created
- [x] PostgreSQL schema designed
- [x] FastAPI backend implementation
- [x] Entra ID SSO authentication
- [x] SCIM endpoints (/Users, /Groups)
- [x] Rust badge baking module
- [x] Docker configuration
- [x] Testing suite
- [x] Documentation

## Quick Start

1. Review `migration_plan.md` for the complete roadmap
2. Follow steps 1-6 in order
3. Run data migration script to transfer data from MongoDB to PostgreSQL
4. Test each component before moving to the next
5. Deploy using Docker Compose

## Key Changes

### Backend
- **FastAPI** replaces Next.js API routes
- **SQLAlchemy** replaces Prisma ORM
- **Pydantic** replaces Zod for validation
- **Rust (PyO3)** handles badge baking/extraction

### Authentication
- **Entra ID OIDC** replaces NextAuth.js
- **SCIM 2.0** endpoints for provisioning
- **Group-based RBAC** for admin access

### Database
- **PostgreSQL** replaces MongoDB
- Relational schema with proper foreign keys
- UUID primary keys for better distribution

### Infrastructure
- Fully Dockerized (backend, frontend, database, Redis, Celery)
- Redis for caching
- Celery for background jobs
- Nginx as reverse proxy

## Support

For issues or questions, refer to:
- `/docs/troubleshooting.md`
- `/docs/api_documentation.md`
- Error logs in `/logs/`

