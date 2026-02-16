# SocialFi Platform - Deployment Guide

## Overview

SocialFi is a multi-network content ingestion and trading platform. This guide covers local development setup and production deployment.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   MongoDB       │
│   (React)       │     │   (FastAPI)     │     │   (Primary DB)  │
│   Port: 3000    │     │   Port: 8001    │     │   Port: 27017   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Redis         │
                        │   (Cache/Queue) │
                        │   Port: 6379    │
                        └─────────────────┘
```

## Prerequisites

- Docker & Docker Compose v2.0+
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

## Quick Start (Local Development)

### 1. Clone and Setup

```bash
git clone <repository>
cd socialfi

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your settings:

```env
ENV=development
MONGO_ROOT_USER=socialfi
MONGO_ROOT_PASSWORD=<generate-strong-password>
DB_NAME=socialfi_db
JWT_SECRET=<generate-with-openssl-rand-base64-48>
CORS_ORIGINS=http://localhost:3000
REACT_APP_BACKEND_URL=http://localhost:8001
```

Generate secure values:
```bash
# Generate JWT secret
openssl rand -base64 48

# Generate MongoDB password
openssl rand -base64 24
```

### 3. Start Services

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f backend
```

### 4. Verify Deployment

```bash
# Health check
curl http://localhost:8001/api/health

# Feed endpoint
curl http://localhost:8001/api/feed

# Frontend
open http://localhost:3000
```

## Production Deployment

### Security Checklist

Before deploying to production:

- [ ] `ENV=production` set
- [ ] Strong `JWT_SECRET` (min 32 chars, random)
- [ ] Strong `MONGO_ROOT_PASSWORD`
- [ ] Explicit `CORS_ORIGINS` (no wildcards)
- [ ] HTTPS/TLS configured on reverse proxy
- [ ] Rate limiting configured
- [ ] Firewall rules for MongoDB/Redis (not public)

### Docker Compose (Production)

```bash
# Build images
docker compose build --no-cache

# Start with production config
ENV=production docker compose up -d

# Scale backend if needed
docker compose up -d --scale backend=3
```

### Kubernetes (Recommended for Scale)

For Kubernetes deployment, convert docker-compose.yml using:

```bash
kompose convert -f docker-compose.yml -o k8s/
```

Key considerations:
- Use StatefulSet for MongoDB
- Use Deployment for backend/frontend
- Configure HPA for auto-scaling
- Use Secrets for sensitive values
- Use PersistentVolumeClaims for data

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `ENV` | Yes | `development` or `production` |
| `MONGO_URL` | Yes | MongoDB connection string |
| `DB_NAME` | Yes | Database name |
| `JWT_SECRET` | Yes | JWT signing secret (min 32 chars in prod) |
| `CORS_ORIGINS` | Yes | Comma-separated allowed origins |
| `REDIS_URL` | No | Redis connection for caching |
| `JWT_EXPIRATION` | No | Token expiry in minutes (default: 1440) |

### Monitoring & Health Checks

**Backend Health:**
```bash
curl http://localhost:8001/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-15T10:00:00Z"
}
```

**Container Health:**
```bash
docker compose ps
docker compose logs --tail=100 backend
```

### Troubleshooting

**Backend won't start:**
```bash
# Check logs
docker compose logs backend

# Common issues:
# - MongoDB not ready: Wait or check mongo service
# - JWT_SECRET missing in production: Set env var
# - CORS_ORIGINS missing in production: Set env var
```

**Database connection issues:**
```bash
# Test MongoDB connection
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Check backend can reach MongoDB
docker compose exec backend curl mongodb:27017
```

**Rate limiting issues:**
```bash
# Check rate limit headers in response
curl -i http://localhost:8001/api/feed

# Headers: X-RateLimit-Limit, Retry-After
```

## CI/CD

The `.github/workflows/ci.yml` pipeline runs:

1. **Backend CI**: Lint, security scan, unit tests
2. **Frontend CI**: Lint, build, audit
3. **Docker Build**: Build and scan images with Trivy
4. **Integration Tests**: Full stack smoke tests

To run CI locally:
```bash
# Backend tests
cd backend && pytest tests/ -v

# Frontend build
cd frontend && yarn build

# Security scan
cd backend && bandit -r . -ll
```

## Scaling Considerations

### Database
- Use MongoDB replica set for production
- Enable transactions for atomic trading operations
- Consider sharding for >1M posts

### Caching
- Redis for feed caching (reduces DB load)
- Cache connector fetch results (Reddit/Farcaster)
- Use Redis for rate limiting in distributed setup

### Background Jobs
- Replace `BackgroundTasks` with Celery/RQ for reliability
- Implement job queues for feed refresh
- Add retry logic with exponential backoff

## Security Notes

1. **JWT Tokens**: Expire after 24 hours by default. Adjust `JWT_EXPIRATION`.
2. **SIWE Authentication**: EIP-4361 compliant for EVM chains.
3. **Rate Limiting**: Applied to auth and trade endpoints.
4. **Input Validation**: Pydantic models validate all inputs.
5. **SQL Injection**: N/A (MongoDB with Motor driver).
6. **XSS**: React escapes by default; security headers added.

## Support

For issues:
1. Check logs: `docker compose logs -f`
2. Verify environment: `docker compose config`
3. Test endpoints: `curl http://localhost:8001/api/health`
