# Pangan-BE Production Deployment Plan
## VPS Deployment with Caddy Network Edge & Docker CI/CD

### 📋 Project Overview
- **Application**: FastAPI-based Indonesian food price data API
- **Architecture**: Clean architecture with PostgreSQL + SQLAlchemy
- **Current State**: Development-ready with basic Docker setup
- **Target**: Production deployment on VPS with Caddy reverse proxy

### 🏗️ Deployment Architecture
```
GitHub Actions CI/CD → GitHub Container Registry → VPS (Caddy + API + PostgreSQL)
```

### 📝 Implementation Tasks

#### 1. Production Docker Configuration
**docker-compose.prod.yml** - Multi-service production setup:
- API service connected to `edge` network for Caddy integration
- PostgreSQL with production optimizations and persistence
- Proper environment variable management via .env file
- Health checks and resource limits
- Network configuration for Caddy reverse proxy

#### 2. Optimized Production Dockerfile
**Dockerfile.prod** - Production-optimized container:
- Multi-stage build for smaller image size
- Non-root user for enhanced security
- Health check endpoint integration
- Proper Python production settings (no debug, optimized runtime)
- Efficient layer caching for faster builds

#### 3. CI/CD Pipeline
**`.github/workflows/deploy.yml`** - Complete deployment workflow:
```
Jobs: commit-hash → build-and-push → deploy-to-vps
├── commit-hash: Generate deployment commit hash
├── build-and-push: Build and push pangan-api image to GHCR
└── deploy-to-vps: SSH deployment to VPS with docker-compose orchestration
```

**Key Features:**
- Automated Docker image building and pushing to GHCR
- SSH-based deployment to VPS
- Database migrations execution
- Administrative data seeding (provinces/regencies/districts)
- Automatic rollback capability on deployment failure
- Environment-specific configuration management

#### 4. Environment & Secrets Management
**`.env.production`** template with production variables:
- Database credentials and connection strings
- Production environment settings (ENV=production)
- API configuration and security secrets
- Logging and monitoring configurations

**GitHub Repository Secrets Required:**
- `VPS_HOST`, `VPS_USERNAME`, `SSH_PRIVATE_KEY` (for deployment)
- `GITHUB_TOKEN` (for container registry access)
- Database passwords and API secrets

#### 5. Caddy Docker Proxy Integration
- ✅ **Already configured**: Using existing `lucaslorentz/caddy-docker-proxy`
- ✅ **Edge network**: Already exists and accessible
- Docker labels configuration for automatic routing
- Automatic SSL certificate management via Let's Encrypt
- Production CORS settings for security
- Security headers and health checks via Docker labels

#### 6. Database Production Setup
- PostgreSQL optimization for production workload
- Alembic migration execution in containerized environment
- Administrative data seeding automation
- Database backup and recovery strategy
- Connection pooling and performance tuning

#### 7. Monitoring & Observability
- Application health check endpoints (/health)
- Database connectivity monitoring
- Container resource usage tracking
- Structured JSON logging for production
- Integration with monitoring tools (optional)

### 🔧 Key Adaptations from Reference CI/CD

| Reference Project (viralkan) | Current Project (pangan-be) |
|-----------------------------|----------------------------|
| `viralkan-api` + `viralkan-web` | `pangan-api` (API-only) |
| `viralkan` database | `pangan-db` database |
| Multi-service (web + api) | Single API service |
| Firebase/web configurations | Removed (API-only) |
| `bun run` commands | Python/alembic commands |
| Web-specific environment vars | API-specific environment vars |

### 🚀 Deployment Checklist

#### Pre-deployment Setup
- [ ] Configure GitHub repository secrets (VPS access, tokens, credentials)
- [x] ~~Set up VPS with Docker, Docker Compose, and Caddy~~ **Already configured with Caddy Docker Proxy**
- [ ] Create/verify production domain and DNS configuration
- [ ] Test VPS connectivity and permissions
- [x] ~~Verify Caddy `edge` network exists and is accessible~~ **Already exists from edge proxy setup**

#### Deployment Execution
- [ ] Create production `docker-compose.prod.yml`
- [ ] Optimize `Dockerfile` for production use
- [ ] Implement CI/CD workflow (`.github/workflows/deploy.yml`)
- [ ] Configure Caddy routing and SSL certificates
- [ ] Test deployment pipeline with staging environment
- [ ] Execute production deployment

#### Post-deployment Validation
- [ ] Verify API endpoints functionality
- [ ] Test database operations and migrations
- [ ] Validate Caddy routing and SSL certificates
- [ ] Confirm monitoring and logging
- [ ] Set up automated backup strategy
- [ ] Configure alerting and notifications

### ⚠️ Critical Considerations

#### Security
- Update CORS settings for production domains only
- Secure database credentials and API secrets
- Implement proper firewall rules on VPS
- Use non-root containers and minimal privileges
- Regular security updates and vulnerability scanning

#### Database
- Ensure migration scripts work in container environment
- Implement database backup before migrations
- Set up connection pooling for production load
- Monitor database performance and query optimization

#### Networking & Caddy
- Proper integration with existing Caddy `edge` network
- Configure appropriate timeouts and rate limiting
- Set up SSL/TLS with automatic certificate renewal
- Implement proper error handling and fallback

#### Monitoring & Maintenance
- Health checks for application and database
- Log aggregation and analysis
- Resource monitoring and scaling considerations
- Automated backup and recovery procedures

### 📚 Implementation Order

1. **Environment Setup** - Configure secrets and VPS access
2. **Docker Configuration** - Create production docker-compose and optimized Dockerfile
3. **CI/CD Pipeline** - Implement GitHub Actions workflow
4. **Caddy Integration** - Configure reverse proxy routing
5. **Database Setup** - Ensure migrations and seeding work in production
6. **Security & Monitoring** - Implement production security and observability
7. **Testing & Validation** - Test deployment and monitoring
8. **Documentation** - Update README and create runbooks

### 🎯 Success Criteria

- ✅ Automated deployment from git push to main branch
- ✅ API accessible via HTTPS with valid SSL certificate
- ✅ Database migrations run automatically on deployment
- ✅ Administrative data properly seeded
- ✅ Health checks and monitoring operational
- ✅ Proper error handling and logging
- ✅ Rollback capability for failed deployments
- ✅ Security best practices implemented

### 📞 Support & Maintenance

**Post-deployment:**
- Monitor application logs and performance
- Set up automated alerts for critical issues
- Regular backup verification
- Security updates and dependency management
- Performance optimization based on usage patterns

---

*This document serves as the comprehensive deployment plan for Pangan-BE production deployment. All team members and AI assistants should reference this for context and implementation guidance.*
