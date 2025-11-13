# Badge Engine Troubleshooting Guide

## Table of Contents

1. [Database Issues](#database-issues)
2. [Authentication Problems](#authentication-problems)
3. [SCIM Provisioning Errors](#scim-provisioning-errors)
4. [Badge Baking Failures](#badge-baking-failures)
5. [Docker Issues](#docker-issues)
6. [Performance Problems](#performance-problems)
7. [Common Error Messages](#common-error-messages)

---

## Database Issues

### Cannot Connect to PostgreSQL

**Symptoms:**
- Error: `could not connect to server: Connection refused`
- Backend fails to start

**Solutions:**

1. **Check PostgreSQL is running:**
   ```bash
   docker ps | grep postgres
   # or
   sudo systemctl status postgresql
   ```

2. **Verify connection string:**
   ```bash
   # Check .env file
   cat .env | grep DATABASE_URL
   ```

3. **Test connection manually:**
   ```bash
   psql postgresql://badge_user:badge_pass@localhost:5432/badge_engine
   ```

4. **Check firewall rules:**
   ```bash
   sudo ufw status
   ```

**Log Location:** `/var/log/postgresql/postgresql-16-main.log`

---

### Migration Errors

**Symptoms:**
- Tables don't exist
- Column not found errors

**Solutions:**

1. **Run database initialization:**
   ```bash
   cd backend
   python -c "from db.base import init_db; init_db()"
   ```

2. **Check for pending migrations:**
   ```bash
   alembic current
   alembic upgrade head
   ```

3. **Reset database (development only):**
   ```bash
   docker-compose down -v
   docker-compose up -d postgres
   # Wait for postgres to be ready
   docker-compose up backend
   ```

**Log Location:** `/app/logs/migration_errors.log`

---

## Authentication Problems

### Entra ID Login Fails

**Symptoms:**
- Redirect loop
- "Invalid client" error
- Token validation fails

**Solutions:**

1. **Verify Entra ID configuration:**
   ```bash
   # Check environment variables
   echo $ENTRA_CLIENT_ID
   echo $ENTRA_TENANT_ID
   ```

2. **Check redirect URI in Azure Portal:**
   - Go to Azure Portal > App Registrations
   - Select your app
   - Authentication > Redirect URIs
   - Ensure `http://localhost:8000/auth/callback` is listed

3. **Verify client secret:**
   - Client secrets expire! Check expiration date
   - Generate new secret if expired
   - Update `ENTRA_CLIENT_SECRET` in .env

4. **Check token validation:**
   ```bash
   # Enable debug logging
   export LOG_LEVEL=DEBUG
   docker-compose restart backend
   ```

5. **Test token manually:**
   ```bash
   curl -X POST https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token \
     -d "client_id=${CLIENT_ID}" \
     -d "client_secret=${CLIENT_SECRET}" \
     -d "grant_type=client_credentials" \
     -d "scope=https://graph.microsoft.com/.default"
   ```

**Log Location:** `/app/logs/error.log`

---

### "403 Forbidden" on Admin Endpoints

**Symptoms:**
- User can authenticate but cannot access `/admin` or `/scim` endpoints

**Solutions:**

1. **Check user's group membership:**
   ```bash
   # Get user groups via Graph API
   curl https://graph.microsoft.com/v1.0/me/memberOf \
     -H "Authorization: Bearer ${ACCESS_TOKEN}"
   ```

2. **Verify group configuration:**
   ```bash
   # Check configured admin groups
   echo $ENTRA_ADMIN_GROUPS
   ```

3. **Add user to admin group in Azure AD:**
   - Azure Portal > Azure Active Directory > Groups
   - Find admin group (e.g., "Badge Admins")
   - Members > Add members
   - Add the user

4. **Check group claims in token:**
   - Configure app to include group claims
   - Azure Portal > App Registrations > Token Configuration
   - Add groups claim

**Resolution Time:** Group membership changes may take up to 5 minutes to propagate

---

## SCIM Provisioning Errors

### Entra SCIM Validator Fails

**Symptoms:**
- SCIM endpoint validation fails in Azure
- "Schema mismatch" errors

**Solutions:**

1. **Test SCIM endpoints manually:**
   ```bash
   # List users
   curl -X GET http://localhost:8000/scim/v2/Users \
     -H "Authorization: Bearer ${TOKEN}"
   
   # Get ServiceProviderConfig
   curl http://localhost:8000/scim/v2/ServiceProviderConfig
   ```

2. **Check SCIM schema compliance:**
   ```bash
   # Schemas endpoint
   curl http://localhost:8000/scim/v2/Schemas
   ```

3. **Verify authentication token:**
   - SCIM endpoints require admin access
   - Ensure token has admin group claim

4. **Enable SCIM debug logging:**
   ```python
   # In backend/api/routers/scim_users.py
   import logging
   logging.getLogger("scim").setLevel(logging.DEBUG)
   ```

**Log Location:** `/app/logs/error.log` (search for "SCIM")

---

### User/Group Provisioning Fails

**Symptoms:**
- Users not created in database
- Group membership not syncing

**Solutions:**

1. **Check provisioning logs in Azure:**
   - Azure Portal > Enterprise Applications
   - Select your app
   - Provisioning > View provisioning logs

2. **Verify SCIM user creation:**
   ```bash
   # Check database
   docker-compose exec postgres psql -U badge_user -d badge_engine \
     -c "SELECT email, name, is_active FROM users;"
   ```

3. **Test user creation manually:**
   ```bash
   curl -X POST http://localhost:8000/scim/v2/Users \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
       "userName": "test@example.com",
       "emails": [{"value": "test@example.com", "primary": true}],
       "active": true
     }'
   ```

4. **Check for database constraints:**
   ```bash
   # Look for unique constraint violations
   docker-compose logs backend | grep "UNIQUE constraint"
   ```

---

## Badge Baking Failures

### Rust Module Not Loading

**Symptoms:**
- `ImportError: No module named 'badge_baking'`
- Falling back to Python implementation

**Solutions:**

1. **Build Rust extension:**
   ```bash
   cd backend/rust_extension
   cargo build --release
   ```

2. **Install with maturin:**
   ```bash
   cd backend/rust_extension
   maturin develop --release
   ```

3. **Check Python path:**
   ```bash
   python -c "import sys; print(sys.path)"
   python -c "import badge_baking; print(badge_baking.__file__)"
   ```

4. **Rebuild Docker image:**
   ```bash
   docker-compose build --no-cache backend
   ```

**Note:** Python fallback is available if Rust extension fails to load

---

### Badge Image Corruption

**Symptoms:**
- Baked images won't open
- Credential extraction returns None

**Solutions:**

1. **Verify input image format:**
   ```bash
   file image.png  # Should say "PNG image data"
   ```

2. **Check image encoding:**
   ```python
   # Test with Python
   from backend.services.badge_service import badge_service
   
   with open('image.png', 'rb') as f:
       image_data = f.read()
   
   credential = {"id": "test", "type": ["VerifiableCredential"]}
   baked = badge_service.bake_png(image_data, credential)
   
   # Verify
   extracted = badge_service.extract_png(baked)
   print(extracted)
   ```

3. **Validate PNG structure:**
   ```bash
   pngcheck image.png
   ```

4. **Test with minimal PNG:**
   ```bash
   # Create 1x1 black pixel PNG
   echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > test.png
   ```

---

## Docker Issues

### Container Fails to Start

**Symptoms:**
- `docker-compose up` exits with error
- Container status is "Exited"

**Solutions:**

1. **Check container logs:**
   ```bash
   docker-compose logs backend
   docker-compose logs postgres
   docker-compose logs redis
   ```

2. **Verify environment variables:**
   ```bash
   docker-compose config
   ```

3. **Check port conflicts:**
   ```bash
   # See what's using port 8000
   lsof -i :8000
   netstat -tulpn | grep 8000
   ```

4. **Remove and rebuild:**
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up
   ```

5. **Check disk space:**
   ```bash
   df -h
   docker system df
   ```

**Clean up Docker:**
```bash
docker system prune -a --volumes
```

---

### Health Checks Failing

**Symptoms:**
- Container marked as "unhealthy"
- Load balancer not routing traffic

**Solutions:**

1. **Check health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **View health check logs:**
   ```bash
   docker inspect --format='{{json .State.Health}}' badge-engine-backend | jq
   ```

3. **Adjust health check timing:**
   ```yaml
   # In docker-compose.yml
   healthcheck:
     interval: 30s
     timeout: 10s
     start_period: 60s  # Increase if slow to start
     retries: 3
   ```

---

## Performance Problems

### Slow API Responses

**Symptoms:**
- Requests taking > 5 seconds
- Timeout errors

**Solutions:**

1. **Enable query logging:**
   ```bash
   export SQL_ECHO=true
   docker-compose restart backend
   ```

2. **Check database connection pool:**
   ```python
   # In backend/db/base.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,  # Increase pool size
       max_overflow=40
   )
   ```

3. **Monitor slow queries:**
   ```sql
   -- In PostgreSQL
   SELECT query, mean_exec_time
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

4. **Check Redis cache:**
   ```bash
   docker-compose exec redis redis-cli
   > INFO stats
   > DBSIZE
   ```

5. **Add database indexes:**
   ```sql
   CREATE INDEX idx_achievements_creator ON achievements(creator_id);
   CREATE INDEX idx_credentials_issuer ON achievement_credentials(issuer_id);
   ```

---

### High Memory Usage

**Symptoms:**
- Container OOM kills
- System slowdown

**Solutions:**

1. **Check memory usage:**
   ```bash
   docker stats
   ```

2. **Limit container memory:**
   ```yaml
   # In docker-compose.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 2G
           reservations:
             memory: 1G
   ```

3. **Monitor Python memory:**
   ```bash
   pip install memory_profiler
   python -m memory_profiler backend/api/main.py
   ```

4. **Tune PostgreSQL:**
   ```conf
   # postgresql.conf
   shared_buffers = 256MB
   effective_cache_size = 1GB
   ```

---

## Common Error Messages

### "Database connection failed"

**Cause:** PostgreSQL not accessible

**Fix:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

---

### "Redis connection error"

**Cause:** Redis not accessible or wrong password

**Fix:**
```bash
# Check Redis
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} PING

# Check password in .env
cat .env | grep REDIS_PASSWORD
```

---

### "Invalid token signature"

**Cause:** Token signing key mismatch or expired token

**Fix:**
1. Token might be expired - get a new token
2. Check JWKS endpoint accessibility
3. Verify tenant ID matches token issuer

---

### "SCIM schema validation failed"

**Cause:** Response doesn't match SCIM 2.0 schema

**Fix:**
1. Check response format matches spec
2. Ensure all required fields present
3. Validate against SCIM schema:
   ```bash
   curl -s http://localhost:8000/scim/v2/Users/uuid | \
     python -m json.tool
   ```

---

## Getting Help

### Log Files

- Application logs: `/app/logs/error.log`
- Migration logs: `/app/logs/migration_errors.log`
- Nginx logs: `/var/log/nginx/error.log`
- PostgreSQL logs: `/var/log/postgresql/postgresql-16-main.log`

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
export SQL_ECHO=true
docker-compose restart backend
```

### Support Channels

- GitHub Issues: https://github.com/your-org/badge-engine/issues
- Email: support@badge-engine.example.com
- Slack: #badge-engine-support

### Reporting Bugs

Include:
1. Error message and stack trace
2. Steps to reproduce
3. Environment details (OS, Docker version)
4. Relevant log files
5. Configuration (sanitize secrets!)

