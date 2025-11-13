# Badge Engine Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Building and Deployment](#building-and-deployment)
4. [Entra ID Configuration](#entra-id-configuration)
5. [Database Setup](#database-setup)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Scaling](#scaling)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB SSD
- OS: Ubuntu 20.04+ or similar Linux distribution

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ SSD
- OS: Ubuntu 22.04 LTS

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- Git
- (Optional) Make for build automation

### Network Requirements

- Ports: 80 (HTTP), 443 (HTTPS), 8000 (API), 3000 (Frontend)
- Outbound: Access to Azure/Microsoft services for Entra ID
- Inbound: HTTP/HTTPS from users

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/badge-engine.git
cd badge-engine
```

### 2. Configure Environment Variables

Copy and edit environment file:

```bash
cp docker/.env.example docker/.env
```

Edit `docker/.env` with your configuration:

```env
# Database
POSTGRES_PASSWORD=generate_strong_password_here
REDIS_PASSWORD=generate_strong_password_here

# Entra ID (see Entra ID Configuration section)
ENTRA_CLIENT_ID=your-client-id-from-azure
ENTRA_CLIENT_SECRET=your-client-secret-from-azure
ENTRA_TENANT_ID=your-tenant-id-from-azure
ENTRA_REDIRECT_URI=https://yourdomain.com/auth/callback

# Groups for access control
ENTRA_ADMIN_GROUPS=Badge Admins,Platform Admins
ENTRA_ISSUER_GROUPS=Issuers

# Application
ENV=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com

# Domain
DOMAIN=yourdomain.com
```

**Security Note:** Generate strong passwords:
```bash
openssl rand -base64 32
```

---

## Entra ID Configuration

### 1. Create App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**

**Settings:**
- Name: `Badge Engine`
- Supported account types: `Accounts in this organizational directory only`
- Redirect URI: 
  - Type: `Web`
  - URI: `https://yourdomain.com/auth/callback`

### 2. Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Description: `Badge Engine Production`
4. Expires: Choose appropriate expiration
5. Copy the **Value** (this is your `ENTRA_CLIENT_SECRET`)

**Important:** Secret is only shown once! Store securely.

### 3. Configure API Permissions

1. Go to **API permissions**
2. Add permissions:
   - Microsoft Graph > Delegated permissions
     - `User.Read`
     - `GroupMember.Read.All`
   - Click **Grant admin consent**

### 4. Configure Token Claims

1. Go to **Token configuration**
2. Add groups claim:
   - Click **Add groups claim**
   - Select **Security groups**
   - For both ID and Access tokens

### 5. Create Security Groups

1. Navigate to **Azure Active Directory** > **Groups**
2. Create groups:
   - `Badge Admins` - For platform administrators
   - `Issuers` - For badge issuers
3. Add users to appropriate groups

### 6. Configure SCIM Provisioning

1. Go to **Enterprise applications**
2. Find your app
3. Go to **Provisioning**
4. Set provisioning mode: **Automatic**
5. Configure:
   - Tenant URL: `https://yourdomain.com/scim/v2`
   - Secret Token: Use admin bearer token
6. Test connection
7. Set provisioning status: **On**

---

## Building and Deployment

### Option 1: Docker Compose (Recommended for Single Server)

1. **Build images:**
   ```bash
   cd docker
   docker-compose build
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment:**
   ```bash
   docker-compose ps
   docker-compose logs -f backend
   ```

4. **Initialize database:**
   ```bash
   docker-compose exec backend python -c "from backend.db.base import init_db; init_db()"
   ```

5. **Test health:**
   ```bash
   curl http://localhost:8000/health
   ```

### Option 2: Kubernetes (Production, Multiple Servers)

1. **Create namespace:**
   ```bash
   kubectl create namespace badge-engine
   ```

2. **Create secrets:**
   ```bash
   kubectl create secret generic badge-engine-secrets \
     --from-env-file=docker/.env \
     -n badge-engine
   ```

3. **Deploy:**
   ```bash
   kubectl apply -f k8s/ -n badge-engine
   ```

4. **Check status:**
   ```bash
   kubectl get pods -n badge-engine
   kubectl logs -f deployment/backend -n badge-engine
   ```

---

## Database Setup

### Initial Setup

Database tables are created automatically on first startup via SQLAlchemy.

### Manual Initialization

If needed:

```bash
docker-compose exec backend python <<EOF
from backend.db.base import init_db
init_db()
print("Database initialized successfully")
EOF
```

### Data Migration from MongoDB

If migrating from existing T3/MongoDB installation:

```bash
# 1. Backup MongoDB
mongodump --uri="mongodb://localhost:27017/badge_engine" --out=/backup

# 2. Run migration script
docker-compose exec backend python migration/data_migration_script.py \
  --mongodb-uri="mongodb://old-host:27017/badge_engine" \
  --dry-run  # Test first

# 3. Run actual migration
docker-compose exec backend python migration/data_migration_script.py \
  --mongodb-uri="mongodb://old-host:27017/badge_engine"

# 4. Verify data
docker-compose exec postgres psql -U badge_user -d badge_engine \
  -c "SELECT COUNT(*) FROM achievements;"
```

### Backup and Restore

**Backup:**
```bash
docker-compose exec postgres pg_dump -U badge_user badge_engine > backup.sql
```

**Restore:**
```bash
cat backup.sql | docker-compose exec -T postgres psql -U badge_user badge_engine
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

1. **Install Certbot:**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. **Obtain certificate:**
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. **Auto-renewal:**
   ```bash
   sudo certbot renew --dry-run
   ```

### Option 2: Custom Certificate

1. **Place certificates:**
   ```bash
   mkdir -p docker/ssl
   cp your-cert.pem docker/ssl/cert.pem
   cp your-key.pem docker/ssl/key.pem
   ```

2. **Update nginx.conf:**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;
       
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       
       # ... rest of config
   }
   ```

3. **Restart nginx:**
   ```bash
   docker-compose restart nginx
   ```

---

## Monitoring and Maintenance

### Health Checks

Monitor service health:

```bash
# API health
curl https://yourdomain.com/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli PING
```

### Logging

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Search logs
docker-compose logs backend | grep ERROR
```

**Log rotation:**

Create `/etc/logrotate.d/badge-engine`:
```
/app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose restart backend
    endscript
}
```

### Metrics and Monitoring

**Prometheus + Grafana:**

1. **Add to docker-compose.yml:**
   ```yaml
   prometheus:
     image: prom/prometheus
     volumes:
       - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
     ports:
       - "9090:9090"
   
   grafana:
     image: grafana/grafana
     ports:
       - "3001:3000"
   ```

2. **Configure Prometheus:**
   ```yaml
   # monitoring/prometheus.yml
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'badge-engine'
       static_configs:
         - targets: ['backend:8000']
   ```

### Database Maintenance

**Vacuum and analyze:**
```bash
docker-compose exec postgres psql -U badge_user -d badge_engine \
  -c "VACUUM ANALYZE;"
```

**Check database size:**
```bash
docker-compose exec postgres psql -U badge_user -d badge_engine \
  -c "SELECT pg_size_pretty(pg_database_size('badge_engine'));"
```

### Updates and Patches

**Update application:**
```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build --no-cache

# Restart with new images
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

**Update dependencies:**
```bash
# Update Python packages
docker-compose exec backend pip install --upgrade -r requirements.txt

# Rebuild Rust extension
docker-compose exec backend bash -c "cd rust_extension && cargo update && maturin develop"
```

---

## Scaling

### Horizontal Scaling

**Add backend workers:**

```yaml
# docker-compose.yml
services:
  backend:
    # ... existing config
    deploy:
      replicas: 3
  
  # Or manually
  backend-2:
    <<: *backend
    container_name: badge-engine-backend-2
    ports:
      - "8001:8000"
```

**Load balancer configuration:**

```nginx
upstream backend_servers {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
    server backend-2:8000 max_fails=3 fail_timeout=30s;
    server backend-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    location /api/ {
        proxy_pass http://backend_servers;
    }
}
```

### Vertical Scaling

**Increase resources:**

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Database Scaling

**Read replicas:**

1. Configure PostgreSQL streaming replication
2. Update connection string for read-only queries
3. Use pgpool for connection pooling

**Connection pooling:**

```python
# backend/db/base.py
engine = create_engine(
    DATABASE_URL,
    pool_size=50,
    max_overflow=100,
    pool_pre_ping=True
)
```

---

## Production Checklist

- [ ] Strong passwords for all services
- [ ] SSL/TLS configured and tested
- [ ] Entra ID app registration complete
- [ ] Security groups created and users assigned
- [ ] SCIM provisioning tested
- [ ] Database backups configured
- [ ] Log rotation enabled
- [ ] Monitoring in place
- [ ] Health checks passing
- [ ] Rate limiting configured
- [ ] Firewall rules set
- [ ] DNS records updated
- [ ] Email notifications tested
- [ ] Disaster recovery plan documented

---

## Support

For deployment assistance:
- Documentation: https://docs.badge-engine.example.com
- Email: support@badge-engine.example.com
- GitHub: https://github.com/your-org/badge-engine/issues

