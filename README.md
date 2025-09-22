# Pangan Indonesia Data Cache & API — Phase 2 Complete

**Status: Phase 2 Complete** ✅

Clean Architecture implementation with FastAPI for Indonesian food price data caching and API services.

## 🏗️ Architecture Overview

This project follows **Clean Architecture** principles with the following structure:

```
app/
├── core/           # Domain models, value objects, errors, shared types
├── usecases/       # Application services: orchestrate domain logic (framework-agnostic)
├── api/           # FastAPI routers, request/response DTO mapping, validation
├── infra/         # Adapters: db, http clients, schedulers (port implementations)
├── common/        # Settings, logging, middleware, utils (no domain logic)
└── lifespan.py    # App startup/shutdown readiness management
```

## 🚀 Quickstart (Local Development)

### 1. Setup Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Local PostgreSQL Setup (Development)
```bash
# Create database (macOS/Homebrew Postgres example)
createdb pangan-db

# Or create user and DB explicitly
createuser -s postgres || true
psql -U postgres -c "CREATE DATABASE \"pangan-db\";" || true
```

### 4. Configure Environment
Create `.env` (auto-loaded) with local DB URL:
```bash
cp .env.example .env
# Ensure DATABASE_URL points to local Postgres
# postgresql+psycopg://<user>:<password>@localhost:5432/pangan-db
```

### 5. Run Development Server
```bash
# Start the FastAPI server with hot reload
python3 -m uvicorn app.main:app --reload --port 8000

# Or using the shorter form
uvicorn app.main:app --reload --port 8000
```

### 6. Verify Installation
```bash
# Test health endpoints (the app exposes root-level probes)
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz

# View API documentation
open http://localhost:8000/docs  # Swagger UI
```

## 🐳 Production Deployment (Docker + VPS + Caddy)

The application is fully configured for production deployment on a VPS with Caddy reverse proxy and automated CI/CD pipeline.

### 🚀 Production Architecture

```
GitHub Actions CI/CD → GitHub Container Registry → VPS (Edge Proxy + API + PostgreSQL)
├── Automated builds on main branch push
├── Multi-arch Docker images (AMD64/ARM64)
├── SSH deployment to VPS
├── Database migrations on deploy
├── Administrative data seeding
├── Health checks and monitoring
└── Automatic SSL certificates via Caddy Docker Proxy
```

**Edge Proxy Architecture:**
```
┌─────────────────┐    ┌──────────────────┐
│   Internet      │────│  Caddy Proxy     │  (Ports 80/443 only)
│                 │    │  (Docker Labels) │
└─────────────────┘    └──────────────────┘
                                │
                        ┌───────┴───────┐
                        │  edge network │
                        └───────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│   Pangan API   │    │   Other Apps    │    │   Other Apps    │
│ ┌────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │    Web     │ │    │ │    Web      │ │    │ │    Web      │ │
│ └────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │     DB     │ │    │ │     DB      │ │    │ │     DB      │ │
│ └────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└────────────────┘    └─────────────────┘    └─────────────────┘
   pangan-network       private networks      private networks
```

### 📋 Production Deployment Prerequisites

#### 1. VPS Setup
- ✅ **Caddy Edge Proxy already configured** (using `lucaslorentz/caddy-docker-proxy`)
- ✅ **Edge network already exists** (created by your edge proxy setup)
- ✅ **Docker and Docker Compose installed**
- ✅ **SSH access configured**
- At least 2GB RAM, 20GB storage recommended

#### 2. Domain Configuration
- Domain name pointing to your VPS IP
- DNS records configured (A record for the API subdomain)
- SSL certificates handled automatically by Caddy

#### 3. GitHub Repository Secrets
Configure these secrets in your GitHub repository settings:
```bash
VPS_HOST=your-vps-ip-or-domain.com
VPS_USERNAME=your-ssh-username
SSH_PRIVATE_KEY=your-private-ssh-key
DB_PASSWORD=your-production-database-password
GITHUB_TOKEN=github-personal-access-token
```

### 🚀 Production Deployment Steps

#### Step 1: Initial VPS Setup
```bash
# On your VPS, ensure Docker is installed (Caddy Edge Proxy is already configured)
sudo apt update
sudo apt install -y docker.io docker-compose-plugin

# Create required directories for Pangan deployment
sudo mkdir -p /opt/pangan-be
sudo chown $USER:$USER /opt/pangan-be

# Verify your existing Caddy Edge Proxy setup
docker ps | grep caddy
docker network ls | grep edge

# The edge network should already exist from your edge proxy setup
docker network inspect edge
```

#### Step 2: Configure GitHub Secrets
1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add the required secrets listed above
3. Generate SSH key pair if needed:
```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions@pangan-be"
# Add public key to VPS ~/.ssh/authorized_keys
# Add private key as SSH_PRIVATE_KEY secret
```

#### Step 3: Deploy via CI/CD
```bash
# Simply push to main branch - deployment happens automatically
git add .
git commit -m "Deploy to production"
git push origin main
```

The CI/CD pipeline will:
- ✅ Build optimized Docker images
- ✅ Push to GitHub Container Registry
- ✅ SSH into VPS and pull latest images
- ✅ Run database migrations
- ✅ Seed administrative data
- ✅ Start services with health checks
- ✅ Verify deployment success

### 🔧 Production Configuration Files

#### Docker Compose (Production)
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    image: ghcr.io/yourusername/pangan-be/pangan-api:latest
    networks:
      - pangan-network
      - edge  # Connects to Caddy
    environment:
      - ENV=production
      - DATABASE_URL=postgresql+psycopg://...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  postgres:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    networks:
      - pangan-network
networks:
  edge:
    external: true  # Your existing Caddy network
```

#### Caddy Docker Proxy Configuration
Your Caddy setup uses Docker labels for automatic configuration. The API service is configured with these labels in `docker-compose.prod.yml`:

```yaml
services:
  api:
    labels:
      caddy: api.yourdomain.com  # Your domain
      caddy.reverse_proxy: "{{upstreams 8000}}"
      caddy.header_up.Host: "{host}"
      caddy.header_up.X-Real-IP: "{remote}"
      caddy.header_up.X-Forwarded-For: "{remote}"
      caddy.header_up.X-Forwarded-Proto: "{scheme}"
      # Security headers
      caddy.header.X-Frame-Options: "DENY"
      caddy.header.X-Content-Type-Options: "nosniff"
      caddy.header.X-XSS-Protection: "1; mode=block"
      caddy.header.Referrer-Policy: "strict-origin-when-cross-origin"
      # Enable automatic updates
      com.centurylinklabs.watchtower.enable: "true"
```

**Key Features:**
- ✅ **Automatic HTTPS** via Let's Encrypt
- ✅ **Security headers** for production security
- ✅ **Health checks** and load balancing
- ✅ **Automatic updates** via Watchtower
- ✅ **No manual Caddyfile management** required

#### Environment Variables
```bash
# .env.production
GITHUB_REPOSITORY=yourusername/pangan-be
IMAGE_TAG=latest
DB_PASSWORD=your-secure-password
ENV=production
TZ=Asia/Jakarta
LOG_LEVEL=INFO
```

### 📊 Production Monitoring

#### Health Endpoints
- `GET /health` - Simple health check for Docker/load balancers
- `GET /health/healthz` - Liveness probe
- `GET /health/readyz` - Readiness probe

#### Application Logs
```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f api

# View database logs
docker-compose -f docker-compose.prod.yml logs -f postgres
```

#### Monitoring Commands
```bash
# Check service health
docker-compose -f docker-compose.prod.yml ps

# Check container resource usage
docker stats

# View Caddy access logs (using your existing Caddy Docker Proxy)
docker logs edge-proxy-caddy-1 2>&1 | grep api.yourdomain.com
```

### 🔄 Production Maintenance

#### Database Operations
```bash
# Run migrations manually
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Backup database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres pangan-db > backup.sql

# Access database shell
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d pangan-db
```

#### Service Management
```bash
# Restart services
docker-compose -f docker-compose.prod.yml restart

# Scale API service (if needed)
docker-compose -f docker-compose.prod.yml up -d --scale api=2

# Update to latest version
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

#### Troubleshooting
```bash
# Check service logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=100 api

# Verify network connectivity
docker network ls
docker network inspect edge

# Check Caddy Docker Proxy configuration
docker logs edge-proxy-caddy-1 --tail=50

# Test API endpoints through Caddy
curl -H "Host: api.yourdomain.com" http://localhost/health

# Test direct API access (bypass Caddy for debugging)
curl http://localhost:8000/health

# Check SSL certificate
curl -v -H "Host: api.yourdomain.com" https://localhost/health

# Verify Caddy labels are applied correctly
docker inspect pangan-api | grep -A 10 "Labels"
```

### 🔒 Security Considerations

#### Production Security Features
- ✅ Non-root Docker containers
- ✅ Restricted CORS origins for production
- ✅ Automatic SSL/TLS certificates
- ✅ Security headers (HSTS, XSS protection, etc.)
- ✅ Rate limiting on API endpoints
- ✅ Database credentials via environment variables
- ✅ SSH key-based deployment access

#### Additional Security Recommendations
- Regularly update Docker images and dependencies
- Implement proper firewall rules on VPS
- Use managed database backups
- Monitor for security vulnerabilities
- Implement proper log rotation
- Consider using secrets management (Vault, AWS Secrets Manager, etc.)

### 📈 Scaling Considerations

#### Horizontal Scaling
```yaml
# docker-compose.prod.yml (scaled)
services:
  api:
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
    depends_on:
      - postgres
      - redis  # Add Redis for session/caching if needed
```

#### Load Balancing
- Caddy automatically load balances between multiple API instances
- Add Redis for session management if scaling beyond single instance
- Consider using a managed PostgreSQL service for high availability

### 🚨 Emergency Procedures

#### Rollback Deployment
```bash
# If deployment fails, rollback to previous version
docker tag ghcr.io/yourusername/pangan-be/pangan-api:previous ghcr.io/yourusername/pangan-be/pangan-api:latest
docker-compose -f docker-compose.prod.yml up -d api
```

#### Database Recovery
```bash
# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d pangan-db < backup.sql
```

#### Emergency Shutdown
```bash
# Stop all services immediately
docker-compose -f docker-compose.prod.yml down

# Start only essential services
docker-compose -f docker-compose.prod.yml up -d postgres
```

### 📞 Support & Maintenance

- **Logs**: All application logs are in JSON format for easy parsing
- **Backups**: Database backups are stored in `./backups/` directory
- **Updates**: Push to main branch triggers automatic deployment
- **Monitoring**: Use health endpoints for uptime monitoring
- **Alerts**: Configure alerts for failed deployments or health check failures

---

*For detailed CI/CD configuration, see `.github/workflows/deploy.yml` and `docker-compose.prod.yml`*

## 📊 Health Endpoints

- `GET /health/healthz` — Liveness probe (always returns 200 when running)
- `GET /health/readyz` — Readiness probe (503 while starting, 200 when ready)

## 🔧 Development Workflow

### Environment Variables
Create a `.env` file in the project root (not committed to git):

```bash
# Copy from .env.example when available
cp .env.example .env

# Or create manually with:
ENV=development
TZ=Asia/Jakarta
PORT=8000
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/pangan-db
```

### Available Scripts
```bash
# Development server
uvicorn app.main:app --reload --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# With environment file
uvicorn app.main:app --reload --port 8000 --env-file .env

# Quality gates (linting & formatting)
python scripts/dev.py quality

# Individual quality checks
python scripts/dev.py lint      # Check linting
python scripts/dev.py format    # Format code
```

## 🧪 Testing & Verification

### Manual Testing
```bash
# Health checks (root-level probes)
curl -s http://localhost:8000/healthz | python3 -m json.tool
curl -s http://localhost:8000/readyz | python3 -m json.tool

# API documentation
curl http://localhost:8000/openapi.json
```

### Step-by-step: Test Ingest (SQLite dev flow)
Follow these exact steps — they match the repository helpers and CLI in `scripts/dev.py`.

1) Create and activate a virtualenv, then install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) (Optional) set environment variables — leave `DATABASE_URL` unset to use the SQLite dev DB:
```bash
export ENV=development
export TZ=Asia/Jakarta
export LOG_LEVEL=INFO
# Leave DATABASE_URL unset to use sqlite ./dev.db
```

3) Create DB tables for quick local testing (uses the sync engine and models metadata):
```bash
python - <<'PY'
from app.infra.db import get_engine
from app.infra import models
engine = get_engine()
models.metadata.create_all(bind=engine)
print('Tables created')
PY
```

4) Dry-run ingest (validates fetch/normalize; does not persist):
```bash
python scripts/dev.py ingest --start 2025-01 --end 2025-01 --level 3 --province NATIONAL --dry-run --mock
```

5) Real ingest (persist to local sqlite dev.db using mock payload):
```bash
python scripts/dev.py ingest --start 2025-01 --end 2025-01 --level 3 --province NATIONAL --mock --save-dir ./payloads --save ./summary.json
```

6) Inspect the SQLite DB to confirm rows were persisted:
```bash
sqlite3 dev.db "SELECT count(*) FROM prices_monthly;"
sqlite3 dev.db "SELECT commodity_id, period_start, price FROM prices_monthly LIMIT 5;"
```

Notes:
- `--mock` uses a local mock payload (no network). Remove `--mock` to fetch real upstream data (requires network and upstream availability).
- `--save-dir` writes per-month raw payload files; `--save` writes final summary JSON.
- The CLI will exit with non-zero status if nothing was persisted.

### Test Ingest (Postgres)
To test against Postgres instead of SQLite:

1) Start or create a Postgres database and set `DATABASE_URL` in your environment or `.env` (example):
```bash
# create DB (example using psql)
createdb pangan-db
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/pangan-db"
```

2) Create tables (quick dev path) or use Alembic migrations (recommended):
```bash
python - <<'PY'
from app.infra.db import get_engine
from app.infra import models
engine = get_engine()
models.metadata.create_all(bind=engine)
print('Tables created in Postgres')
PY
```

3) Run ingest (remove `--mock` to call upstream):
```bash
python scripts/dev.py ingest --start 2025-01 --end 2025-01 --level 3 --province NATIONAL --save ./summary.json
```

### Alembic migrations (recommended for Postgres / production)
The repo contains an `alembic/` directory wired to `app.infra.models`. To generate and apply migrations:

1) Edit `alembic.ini` and set `sqlalchemy.url` to your `DATABASE_URL`, or replace the value before running migrations.

2) Create an initial autogenerate revision:
```bash
alembic revision --autogenerate -m "init"
```

3) Apply migrations:
```bash
alembic upgrade head
```

If you prefer the quick dev flow, `models.metadata.create_all(bind=engine)` is supported (used in the CLI and README steps above) but is not a substitute for production migrations.

## 🔄 **Data Ingestion Pipeline (Phase 2)**

The application includes a complete data ingestion pipeline for fetching Indonesian food price data from the official API and storing it in the database with full idempotency and observability.

### Core Features

- **🔄 Idempotent Upserts**: SHA256 checksums prevent duplicate data while allowing updates
- **📊 Structured Logging**: JSON logs with detailed timing metrics for each operation
- **🌱 Auto-Seeding**: Commodities and provinces automatically seeded from API payloads
- **🧪 Dry-Run Mode**: Validate data without persisting to database
- **🎭 Mock Mode**: Test pipeline without calling external APIs
- **💾 Payload Persistence**: Save raw API responses for debugging/analysis

### CLI Usage Examples

#### Basic Ingestion (Mock Mode)
```bash
# Ingest January 2024 data using mock payloads
python scripts/dev.py ingest --start 2024-01 --end 2024-01 --mock

# Ingest multiple months
python scripts/dev.py ingest --start 2024-01 --end 2024-03 --mock
```

#### Real API Ingestion
```bash
# Fetch from live upstream API (requires internet)
python scripts/dev.py ingest --start 2024-01 --end 2024-01

# With custom level and province
python scripts/dev.py ingest --start 2024-01 --end 2024-01 --level 2 --province NATIONAL
```

#### Advanced Options
```bash
# Dry-run to validate without persisting
python scripts/dev.py ingest --start 2024-01 --end 2024-01 --dry-run --mock

# Save payloads and summary for analysis
python scripts/dev.py ingest --start 2024-01 --end 2024-01 --mock \
  --save-dir ./payloads \
  --save ./ingest-summary.json
```

### Pipeline Architecture

```
Upstream API → Validation → Normalization → Checksum → Database Upsert
     ↓            ↓            ↓           ↓           ↓
   Raw JSON    Pydantic     Monthly     SHA256     PostgreSQL
  Response    Models       Records     Hash       ON CONFLICT

API Endpoints → Query Service → Repository → Database Response
     ↓             ↓             ↓            ↓
  REST API     Business      Data Access    JSON Response
  Requests     Logic         Layer          with Pagination
```

### Structured Logging Output

The ingestion pipeline produces detailed JSON logs for monitoring:

```json
{
  "asctime": "2025-09-18 09:38:17,727",
  "levelname": "INFO",
  "name": "__main__",
  "message": "Ingestion completed",
  "operation": "ingest",
  "level_harga_id": 3,
  "province_id": "NATIONAL",
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "fetch_duration_ms": 45.23,
  "normalize_duration_ms": 0.08,
  "checksum_duration_ms": 0.05,
  "upsert_duration_ms": 3.92,
  "total_duration_ms": 49.28,
  "normalized_rows": 2,
  "upsert_rows": 2,
  "inserted": 2,
  "updated": 0,
  "unchanged": 0
}
```

### Data Model

The system ingests monthly price data with the following structure:

- **Commodities**: Rice varieties (Premium, Medium, etc.) with unique IDs
- **Provinces**: Geographic regions (NATIONAL aggregate, specific provinces)
- **Price Records**: Monthly prices per commodity-province-level combination
- **Checksums**: SHA256 hashes for change detection and idempotency

### Acceptance Testing

The pipeline includes comprehensive acceptance tests:

```bash
# Verify ingestion produces data
python scripts/dev.py ingest --start 2024-01 --end 2024-01 --mock

# Verify idempotency (re-run should show unchanged records)
python scripts/dev.py ingest --start 2024-01 --end 2024-01 --mock

# Check database contents
sqlite3 dev.db "SELECT COUNT(*) FROM prices_monthly;"
sqlite3 dev.db "SELECT commodity_id, province_id, period_start, price FROM prices_monthly LIMIT 5;"
```

### Logs
The application provides structured JSON logging:
```json
{
  "asctime": "2025-09-01 11:17:06,908",
  "levelname": "INFO",
  "name": "pangan",
  "message": "",
  "event": "request_start",
  "method": "GET",
  "path": "/health/healthz"
}
```

## ⏰ **Scheduler Recommendations**

For production deployment, implement automated data refresh using APScheduler (already included in dependencies). Here are recommended approaches:

### Option 1: Background Scheduler (Recommended)

Add to your FastAPI lifespan management:

```python
# app/lifespan.py
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = BackgroundScheduler(timezone="Asia/Jakarta")

    # Daily ingestion at 2 AM
    from app.usecases.ingest import fetch_and_upsert
    from app.infra.http.upstream import make_upstream_client
    from app.infra.repositories.prices import make_price_repository
    from app.infra.db import get_engine

    def daily_ingest():
        try:
            client = make_upstream_client()
            repo = make_price_repository(get_engine())
            params = FetchParams(
                start_year=2024, end_year=2024,
                period_start=date.today().replace(day=1),
                period_end=date.today(),
                level_harga_id=3, province_id=None
            )
            summary = fetch_and_upsert(client, repo, params)
            logger.info("Scheduled ingestion completed", extra={
                "inserted": summary.inserted,
                "updated": summary.updated,
                "unchanged": summary.unchanged
            })
        except Exception as e:
            logger.error("Scheduled ingestion failed", extra={"error": str(e)})

    scheduler.add_job(daily_ingest, CronTrigger(hour=2, minute=0))
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()
```

### Option 2: External Scheduler (Cron/Kubernetes CronJob)

For better reliability in production, use external schedulers:

```bash
# Cron job example (crontab -e)
# Daily at 2 AM Jakarta time
0 2 * * * cd /path/to/app && /path/to/venv/bin/python scripts/dev.py ingest --start $(date +\%Y-\%m) --end $(date +\%Y-\%m)

# Or Kubernetes CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pangan-daily-ingest
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: ingest
            image: pangan-app:latest
            command: ["python", "scripts/dev.py", "ingest", "--start", "$(date +%Y-%m)", "--end", "$(date +%Y-%m)"]
```

### Scheduler Configuration Best Practices

- **Timezone**: Always use `Asia/Jakarta` for consistency with upstream data
- **Error Handling**: Implement retry logic and alerting for failures
- **Monitoring**: Log all scheduled runs with success/failure metrics
- **Overlapping Jobs**: Use job locking to prevent concurrent executions
- **Backfilling**: Support manual backfill operations for historical data

## 📊 **Observability & Monitoring Recommendations**

Enhance observability with these production-ready additions:

### Health Checks Enhancement

Extend health endpoints to include data freshness:

```python
# app/api/health.py
@app.get("/health/freshness")
async def data_freshness_check(db: Session = Depends(get_db_session)):
    """Check data freshness - fail if data is older than 48 hours"""
    latest_price = db.query(PriceMonthly).order_by(
        desc(PriceMonthly.updated_at)
    ).first()

    if not latest_price:
        raise HTTPException(status_code=503, detail="No price data found")

    hours_old = (datetime.now() - latest_price.updated_at).total_seconds() / 3600
    if hours_old > 48:
        raise HTTPException(
            status_code=503,
            detail=f"Data is {hours_old:.1f} hours old (threshold: 48h)"
        )

    return {"status": "fresh", "hours_old": round(hours_old, 1)}
```

### Metrics Collection

Add Prometheus metrics for monitoring:

```python
# app/common/metrics.py
from prometheus_client import Counter, Histogram, Gauge

INGEST_DURATION = Histogram(
    'pangan_ingest_duration_seconds',
    'Time spent on data ingestion',
    ['operation', 'status']
)

INGEST_ROWS = Counter(
    'pangan_ingest_rows_total',
    'Number of rows processed',
    ['operation', 'result']  # inserted, updated, unchanged
)

DATA_FRESHNESS = Gauge(
    'pangan_data_freshness_hours',
    'Hours since last successful data ingestion'
)

# Usage in ingestion code:
INGEST_DURATION.labels(operation='fetch').observe(fetch_duration)
INGEST_ROWS.labels(operation='ingest', result='inserted').inc(summary.inserted)
```

### Structured Logging Enhancements

Add correlation IDs and request tracing:

```python
# app/common/logging.py
import uuid
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar('correlation_id')

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        try:
            record.correlation_id = correlation_id.get()
        except LookupError:
            record.correlation_id = str(uuid.uuid4())
        return True

# Add to formatter
fmt = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(correlation_id)s %(message)s"
)
```

### Alerting Recommendations

Set up alerts for:

1. **Ingestion Failures**: Alert when scheduled ingestion fails
2. **Data Staleness**: Alert when data hasn't been updated in >48 hours
3. **Performance Degradation**: Alert when ingestion takes >5 minutes
4. **Data Quality Issues**: Alert on validation errors or zero rows ingested

### Monitoring Dashboard

Recommended Grafana panels:

- **Ingestion Success Rate**: % of successful vs failed ingestion runs
- **Data Freshness**: Hours since last successful ingestion
- **Ingestion Performance**: Duration trends over time
- **Data Volume**: Rows inserted/updated over time
- **Error Rates**: Validation errors, connection failures, etc.

### Production Logging Setup

```bash
# Environment variables for production logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_CORRELATION_ENABLED=true

# With ELK stack or similar
# Forward JSON logs to Elasticsearch for analysis
```

## 📋 Project Status

### ✅ Completed (Phase 0 - 95%)
- [x] Clean Architecture structure implemented
- [x] FastAPI application with health endpoints
- [x] Pydantic v2 configuration
- [x] JSON logging with correlation
- [x] Basic Docker setup
- [x] Virtual environment support
- [x] `.env.example` file created
- [x] Quality gates configured (ruff linting & formatting)
- [x] Development scripts and workflows

### ✅ **PHASE 2 COMPLETE - Data Ingestion Pipeline**
- [x] **Full ingestion pipeline**: Upstream API client → validation → normalization → checksum-based upsert
- [x] **Idempotent data ingestion**: SHA256 checksum prevents duplicates, supports re-runs
- [x] **Structured JSON logging**: Detailed latency metrics and operation tracking
- [x] **Automatic dimension seeding**: Commodities and provinces seeded from API payloads
- [x] **CLI ingestion command**: `scripts/dev.py ingest` with dry-run, mock mode, and save options
- [x] **Acceptance testing**: Comprehensive verification of data integrity and idempotency

### 🔄 Remaining Tasks
- [ ] Add Dockerfile healthcheck
- [ ] Setup mypy type checking (optional enhancement)
- [ ] Implement API endpoints (`GET /prices`, `GET /commodities`, `GET /provinces`)
- [ ] Add scheduled data refresh jobs (see Scheduler Recommendations)
- [ ] Enhance observability with Prometheus metrics (see Observability Recommendations)

## 🆘 Troubleshooting

### Common Issues

**Module not found errors:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
pip install -r requirements.txt
```

**Port already in use:**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Permission errors with virtualenv:**
```bash
# On macOS/Linux, ensure proper permissions
chmod +x .venv/bin/activate
```

### Getting Help
- Check the [RFC documents](./rfc/) for detailed specifications
- Review [todo.md](./todo.md) for current progress and next steps
- API documentation available at `http://localhost:8000/docs` when running

---

**Next Phase**: Database setup and SQLAlchemy models integration.
