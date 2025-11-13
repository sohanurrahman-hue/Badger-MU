# Backend Scripts

Utility scripts for the Badge Engine backend.

## Available Scripts

### `create_test_account.py`

Creates dummy test accounts for local development and testing.

**Usage:**
```bash
python scripts/create_test_account.py
```

**What it creates:**
- **Admin User**: `test@badgeengine.local` (super user, admin role)
- **Issuer User**: `issuer@badgeengine.local` (issuer role)
- **Regular User**: `user@badgeengine.local` (user role)
- **Test Issuer Profile**: A test issuer organization profile

**Note:** These accounts are for development/testing only. In production, users are created via Entra ID SSO authentication.

**Requirements:**
- Database must be running and accessible
- Environment variables must be set (see `.env.example`)
- Database tables must be initialized (run `init_db()` or start the application)

## Environment Setup

Before running scripts, make sure you have:

1. Copied `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Filled in your actual environment variables in `.env`

3. Database is running and accessible via `DATABASE_URL`

4. (Optional) Redis is running if using caching/Celery

