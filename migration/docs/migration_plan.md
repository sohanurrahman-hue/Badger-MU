# Badge Engine Migration Plan

## Executive Summary

This document outlines the complete migration strategy for refactoring Badge Engine from a T3 stack (Next.js/MongoDB) to a Python/Rust backend with PostgreSQL, while maintaining the React frontend.

## Migration Phases

### Phase 1: Database Migration (Step 1)
**Duration:** Days 1-2  
**Status:** ✅ Complete

#### Objectives
- Design PostgreSQL schema from Prisma models
- Create migration scripts
- Set up database connection pooling
- Implement SQLAlchemy models

#### Deliverables
- PostgreSQL schema files
- SQLAlchemy models matching Open Badge v3.0 spec
- Data migration script (MongoDB → PostgreSQL)
- Database initialization script

---

### Phase 2: Backend Refactoring (Step 2)
**Duration:** Days 2-4  
**Status:** ✅ Complete

#### Objectives
- Build FastAPI application structure
- Implement RESTful API endpoints matching Open Badge spec
- Replace tRPC with REST APIs
- Implement Pydantic schemas for validation
- Create service layer for business logic

#### Deliverables
- FastAPI main application (`backend/api/main.py`)
- API routers for:
  - Achievements (`/api/achievements`)
  - Issuers (`/api/issuers`)
  - Awards (`/api/award`)
  - Signing (`/api/sign`)
- Pydantic models for request/response validation
- Service layer modules
- Error handling middleware

---

### Phase 3: Authentication & SCIM (Step 3)
**Duration:** Days 4-8  
**Status:** ✅ Complete

#### Objectives
- Implement Entra ID OIDC SSO
- Create SCIM 2.0 endpoints
- Set up group-based authorization
- Secure admin portal

#### Deliverables
- Entra ID OIDC integration (`backend/auth/sso.py`)
- SCIM endpoints:
  - `POST /scim/v2/Users`
  - `GET /scim/v2/Users/{id}`
  - `PATCH /scim/v2/Users/{id}`
  - `DELETE /scim/v2/Users/{id}`
  - `GET /scim/v2/Groups`
  - `POST /scim/v2/Groups`
- Group-based RBAC middleware
- Admin endpoint protection (`/admin`)
- SCIM validation tests using Entra SCIM Validator

**Checkpoint:** Successfully provision "Issuers" group and test user through Entra

---

### Phase 4: Rust Integration (Step 4)
**Duration:** Days 9-11  
**Status:** ✅ Complete

#### Objectives
- Create Rust module for badge baking/extraction
- Build PyO3 bindings
- Implement PNG iTXt chunk handling
- Implement SVG credential tag handling
- Handle errors per Open Badge spec

#### Deliverables
- Rust crate (`backend/rust_extension/`)
  - `lib.rs`: Main module with PyO3 exports
  - `baking.rs`: PNG/SVG baking logic
  - `extraction.rs`: Credential extraction logic
- Python wrapper (`backend/services/badge_service.py`)
- Badge baking API endpoint
- Badge extraction API endpoint
- Unit tests for Rust functions

**Specification Compliance:**
- PNG: iTXt chunk with keyword `openbadgecredential`
- SVG: `<openbadges:credential>` tag
- Error handling for existing credentials (throw or overwrite)

---

### Phase 5: Performance & Caching (Step 5)
**Duration:** Days 12-13  
**Status:** ✅ Complete

#### Objectives
- Integrate Redis for caching
- Set up Celery for background tasks
- Implement cache strategies
- Create async job queue

#### Deliverables
- Redis configuration
- Celery worker setup
- Cache decorator for frequently accessed data
- Background tasks for:
  - Badge image generation
  - Email notifications
  - Bulk award processing
- Monitoring for queue health

---

### Phase 6: Docker Infrastructure (Step 6)
**Duration:** Days 14-15  
**Status:** ✅ Complete

#### Objectives
- Dockerize all services
- Create docker-compose configuration
- Set up development and production environments
- Configure networking and volumes

#### Deliverables
- `docker/Dockerfile.backend`: Python/Rust backend
- `docker/Dockerfile.frontend`: React frontend
- `docker/docker-compose.yml`: Complete stack
- Environment configuration (`.env.example`)
- Health checks for all services
- Volume mounts for development
- Production-ready nginx configuration

---

### Phase 7: Testing (Step 7)
**Duration:** Days 16-18  
**Status:** ✅ Complete

#### Objectives
- Write comprehensive test suite
- Validate SCIM endpoints
- Test badge baking/extraction
- Integration tests
- Load testing

#### Deliverables
- Unit tests:
  - Auth tests (`tests/test_auth.py`)
  - SCIM tests (`tests/test_scim.py`)
  - Badge baking tests (`tests/test_badge_baking.py`)
  - API endpoint tests
- Integration tests:
  - End-to-end workflows
  - Database transactions
- Performance tests:
  - Load testing with locust
  - Cache hit rate validation
- SCIM validation with Entra SCIM Validator

---

### Phase 8: Documentation & Finalization (Step 8)
**Duration:** Days 19-20  
**Status:** ✅ Complete

#### Objectives
- Complete technical documentation
- Create troubleshooting guides
- Write API documentation
- Document deployment process

#### Deliverables
- API documentation (`docs/api_documentation.md`)
- Deployment guide (`docs/deployment.md`)
- Troubleshooting guide (`docs/troubleshooting.md`)
- Architecture diagrams
- Environment setup guide
- Data migration runbook

---

## Risk Mitigation

### Data Integrity
- **Risk:** Data loss during MongoDB to PostgreSQL migration
- **Mitigation:** 
  - Dry-run migrations with validation
  - Backup MongoDB before migration
  - Rollback scripts available
  - Data verification queries

### Authentication
- **Risk:** Entra ID configuration errors blocking access
- **Mitigation:**
  - Local dev authentication fallback
  - Comprehensive error logging
  - Step-by-step Entra ID setup guide
  - Test users in staging environment

### Badge Baking
- **Risk:** Rust module failures causing badge generation issues
- **Mitigation:**
  - Extensive unit tests for edge cases
  - Fallback to Python implementation if needed
  - Error handling with clear messages
  - Validation against Open Badge spec examples

### Performance
- **Risk:** Degraded performance after migration
- **Mitigation:**
  - Load testing before production
  - Database indexing strategy
  - Redis caching for hot paths
  - Connection pooling
  - Query optimization

---

## Rollback Strategy

Each phase includes rollback procedures:

1. **Database:** Restore MongoDB backup, point API to old DB
2. **Backend:** Revert to previous Docker image, restore environment
3. **Auth:** Switch back to NextAuth.js configuration
4. **Docker:** Use previous docker-compose version

---

## Success Criteria

- [ ] All API endpoints functional and spec-compliant
- [ ] SCIM provisioning working with Entra ID
- [ ] Badge baking/extraction validated against Open Badge spec
- [ ] < 200ms response time for 95th percentile
- [ ] Zero data loss in migration
- [ ] 100% test coverage for critical paths
- [ ] Documentation complete and reviewed
- [ ] Successful staging deployment
- [ ] Security audit passed

---

## Timeline Summary

| Phase | Duration | Days |
|-------|----------|------|
| Database Migration | 2 days | 1-2 |
| Backend Refactoring | 3 days | 2-4 |
| Auth & SCIM | 5 days | 4-8 |
| Rust Integration | 3 days | 9-11 |
| Performance & Caching | 2 days | 12-13 |
| Docker Infrastructure | 2 days | 14-15 |
| Testing | 3 days | 16-18 |
| Documentation | 2 days | 19-20 |
| **Total** | **~20 days** | **1-20** |

---

## Next Steps

1. Review this migration plan with stakeholders
2. Set up development environment
3. Begin Phase 1: Database Migration
4. Daily standups to track progress
5. Update status in this document as phases complete

