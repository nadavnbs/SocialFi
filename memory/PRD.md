# SocialFi Multi-Network Platform

## Product Requirements Document

### Overview
SocialFi is a multi-network content ingestion and trading platform where viral posts become tradable markets. Users authenticate via Web3 wallet (SIWE/EIP-4361), browse aggregated content from Reddit, Farcaster, X, Instagram, and Twitch, and trade shares using a bonding curve AMM.

---

## Production-Ready Status ✅

### Completed (December 2025)

**Core Features**
- ✅ Wallet-based authentication (SIWE for EVM, structured messages for Solana)
- ✅ Multi-network content ingestion (Reddit, Farcaster active; X/Instagram/Twitch stubbed)
- ✅ Network filtering (multi-select)
- ✅ Sorting (trending, new, price, volume)
- ✅ Paste URL to list posts as markets
- ✅ Buy/sell shares with bonding curve AMM
- ✅ Portfolio tracking with P&L
- ✅ Leaderboard by XP/reputation/balance
- ✅ 1,000 credits for new wallets

**Security Hardening**
- ✅ SIWE (EIP-4361) authentication with nonce replay protection
- ✅ JWT secret validation (rejects weak/default in production)
- ✅ CORS validation (no wildcards with credentials in production)
- ✅ Rate limiting on auth, trades, and feed endpoints
- ✅ Security headers middleware (HSTS, X-Frame-Options, etc.)
- ✅ Input validation with Pydantic models
- ✅ No sensitive data in logs

**Concurrency Safety**
- ✅ Optimistic locking on market updates (version field)
- ✅ Atomic balance/position updates with conditional checks
- ✅ Idempotency keys for trade requests
- ✅ Invariant checks (no negative supply/balance/shares)

**Performance**
- ✅ MongoDB aggregation pipeline for feed (eliminates N+1)
- ✅ Proper database indexes for all query patterns
- ✅ TTL indexes for challenge cleanup

**DevOps**
- ✅ Docker Compose with MongoDB + Redis
- ✅ Production Dockerfiles (non-root, health checks)
- ✅ GitHub Actions CI/CD pipeline
- ✅ Deployment documentation

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   MongoDB       │
│   (React)       │     │   (FastAPI)     │     │   (Primary DB)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Redis         │
                        │   (Cache/Queue) │
                        └─────────────────┘
```

### Key Files
- `/app/backend/server.py` - Main API endpoints
- `/app/backend/siwe.py` - SIWE authentication
- `/app/backend/security.py` - Security config validation
- `/app/backend/amm.py` - Bonding curve AMM
- `/app/backend/connectors.py` - Network connectors
- `/app/frontend/src/pages/LandingPage.js` - Wallet connect UI
- `/app/frontend/src/pages/Feed.js` - Main feed with trading

### API Endpoints
| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/api/health` | GET | No | - | Health check |
| `/api/auth/challenge` | POST | No | 10/min | Get SIWE challenge |
| `/api/auth/verify` | POST | No | 5/min | Verify signature |
| `/api/auth/me` | GET | Yes | 30/min | Get current user |
| `/api/feed` | GET | No | 60/min | Get posts with filters |
| `/api/feed/refresh` | POST | No | 5/min | Trigger refresh |
| `/api/posts/paste-url` | POST | Yes | 10/min | List post by URL |
| `/api/trades/buy` | POST | Yes | 30/min | Buy shares |
| `/api/trades/sell` | POST | Yes | 30/min | Sell shares |
| `/api/portfolio` | GET | Yes | 30/min | Get positions |
| `/api/leaderboard` | GET | No | 30/min | Get rankings |

---

## Database Schema (MongoDB)

**users**
```json
{
  "wallet_address": "0x...",
  "chain_type": "ethereum",
  "balance_credits": 1000.0,
  "level": 1,
  "xp": 0,
  "reputation": 0.0
}
```

**unified_posts**
```json
{
  "source_network": "reddit",
  "source_id": "abc123",
  "source_url": "https://...",
  "author_username": "...",
  "title": "...",
  "content_text": "...",
  "source_likes": 1000,
  "status": "active"
}
```

**markets**
```json
{
  "post_id": "...",
  "total_supply": 100.0,
  "price_current": 1.0,
  "total_volume": 0.0,
  "version": 0
}
```

---

## Test Results (Updated Feb 2025)

```
Backend Unit Tests: 85/85 passed ✅
- AMM calculations: 19 tests
- SIWE authentication: 14 tests  
- Security config: 17 tests (includes SystemExit validation)
- Stress validation: 18 tests (concurrency, horizontal scaling, security abuse)
- Farcaster Frames: 17 tests (generation, validation, security)

API Integration: All endpoints verified
- Health, Feed, Networks, Challenge, Leaderboard
- Protected endpoints return 401 without auth
- Production security enforcement validated
- Farcaster Frame endpoints deployed
```

---

## Farcaster Frames (NEW)

Frame endpoints for viral trading directly in Warpcast:
- `GET /api/frames/market/{id}` - Market preview frame
- `POST /api/frames/action/{id}` - Handle frame button clicks
- `GET /api/frames/leaderboard` - Top traders frame

Features:
- Quick Buy (1 or 5 shares) via frame buttons
- Replay attack prevention
- Per-FID rate limiting
- Signature validation ready for Neynar Hub

---

## Marketing Strategy

See `/app/MARKETING.md` for basic marketing plan.
See `/app/DOMINATION_STRATEGY.md` for execution-level 14-day viral ignition plan.

**Key Strategies:**
- 14-day viral ignition calendar with exact copy
- Liquidity theater for price movement marketing
- Creator capture with revenue sharing
- Psychological hooks (loss aversion, FOMO leaderboards)
- Escape velocity metrics tracking

---

## Prioritized Backlog

### P0 - None (MVP Complete)

### P1 - High Priority
- Implement Redis caching for feed
- Add Celery/RQ for background job queue
- Implement WebSocket for real-time prices

### P2 - Medium Priority
- OAuth for X/Instagram when API keys available
- Price history charts
- Moderation panel
- Share/embed functionality

### P3 - Low Priority
- Mobile responsive improvements
- Notification system
- Advanced analytics

---

## Deployment

See `/app/DEPLOY.md` for full deployment guide.

**Quick Start:**
```bash
cp .env.example .env
# Edit .env with secure values
docker compose up -d
```

**Production Checklist:**
- [ ] ENV=production
- [ ] Strong JWT_SECRET (32+ chars)
- [ ] Strong MONGO_ROOT_PASSWORD
- [ ] Explicit CORS_ORIGINS (no wildcards)
- [ ] HTTPS configured on reverse proxy
