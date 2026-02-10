# InfoFi/SocialFi Platform - Services & APIs Required

## D) EXTERNAL SERVICES CHECKLIST

**Purpose**: Precise list of every external service/API needed for MVP, with options and fastest choice.

---

## 1. AUTHENTICATION & IDENTITY

### Service: OAuth Providers

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Google OAuth** | Widely used, free, trusted | Requires Google account | ✅ YES |
| **GitHub OAuth** | Good for tech audience | Limited to developers | ❌ Post-MVP |
| **Magic Link (email)** | No password needed | Email deliverability issues | ❌ Post-MVP |

**Implementation**:
- **SDK**: `authlib` (Python) or `google-auth-library`
- **Endpoint**: POST /api/auth/oauth/google
- **Flow**: Frontend → Google → Callback → Backend (exchange code for tokens) → Create/login user → Return JWT

**Setup**:
1. Create Google Cloud project
2. Enable OAuth 2.0
3. Add authorized redirect URI: `http://localhost:3000/auth/callback`
4. Get Client ID & Secret
5. Store in env vars: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

**Free Tier**: Unlimited (no cost)

---

## 2. STORAGE (IMAGES/MEDIA)

### Service: Image Hosting

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Cloudinary** | Free 25GB, CDN, transforms | Limited free tier | ✅ YES |
| **AWS S3 + CloudFront** | Scalable, cheap | More setup, billing complexity | ❌ Later |
| **Imgur API** | Simple, free | Rate limits, ads | ❌ Backup |

**Implementation**:
- **SDK**: `cloudinary` (Python)
- **Frontend**: Direct upload from browser (signed upload URL)
- **Endpoint**: POST /api/upload/signed-url (backend generates signed URL)
- **Flow**: User selects image → Get signed URL → Upload direct to Cloudinary → Return URL → Use in post

**Setup**:
1. Sign up at cloudinary.com
2. Get Cloud Name, API Key, API Secret
3. Store in env: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

**Free Tier**: 25GB storage, 25GB bandwidth/month (enough for 1000+ users)

---

## 3. AI MODERATION

### Service: Content Moderation API

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **OpenAI Moderation API** | Free, fast (<1s), accurate | Limited categories | ✅ YES |
| **Perspective API (Google)** | Free, toxicity detection | Slower | ❌ Backup |
| **AWS Rekognition** | Image + text | Paid, complex setup | ❌ Later |

**Implementation**:
- **SDK**: `openai` (Python) or use Emergent Universal Key
- **Endpoint**: Call on POST /api/posts (before saving)
- **Flow**: User submits post → Send text to OpenAI → Check flags (hate, violence, sexual, etc.) → Block/flag/allow → Save post

**Setup**:
1. Get OpenAI API key OR use Emergent Universal Key
2. Store in env: `OPENAI_API_KEY` or `EMERGENT_API_KEY`

**Code Example**:
```python
import openai

def moderate_content(text: str) -> dict:
    response = openai.Moderation.create(input=text)
    result = response["results"][0]
    return {
        "flagged": result["flagged"],
        "categories": result["categories"],
        "scores": result["category_scores"]
    }
```

**Free Tier**: OpenAI Moderation API is free (no cost)

**Emergent Universal Key**: If user has Emergent Universal Key, use that (supports OpenAI)

---

## 4. DATABASE

### Service: PostgreSQL

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Local Docker** | Free, full control, fast dev | Not production-ready | ✅ MVP |
| **Supabase** | Managed Postgres, free tier, auth included | Limited connections | ✅ Prod |
| **Neon** | Serverless Postgres, generous free tier | New service | ❌ Backup |
| **AWS RDS** | Reliable, scalable | Paid, complex | ❌ Later |

**Implementation**:
- **SDK**: `asyncpg` + `SQLAlchemy` (Python ORM)
- **Connection**: PostgreSQL URI in env

**Setup (Local)**:
```yaml
# docker-compose.yml
postgres:
  image: postgres:15
  environment:
    POSTGRES_USER: infofi
    POSTGRES_PASSWORD: infofi123
    POSTGRES_DB: infofi_db
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

**Setup (Supabase - Production)**:
1. Sign up at supabase.com
2. Create project
3. Get connection string
4. Store in env: `DATABASE_URL`

**Free Tier (Supabase)**: 500MB database, unlimited API requests

---

## 5. CACHE & RATE LIMITING

### Service: Redis

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Local Docker** | Free, fast | Not production-ready | ✅ MVP |
| **Upstash** | Serverless Redis, free tier, global | Limited ops/month | ✅ Prod |
| **Redis Cloud** | Managed, reliable | Paid | ❌ Later |

**Implementation**:
- **SDK**: `redis-py` (Python)
- **Use Cases**: Rate limiting, session cache, price cache

**Setup (Local)**:
```yaml
# docker-compose.yml
redis:
  image: redis:7
  ports:
    - "6379:6379"
```

**Setup (Upstash - Production)**:
1. Sign up at upstash.com
2. Create Redis database
3. Get connection URL
4. Store in env: `REDIS_URL`

**Free Tier (Upstash)**: 10,000 commands/day (enough for 100+ DAU)

---

## 6. EMAIL (OPTIONAL FOR MVP)

### Service: Transactional Email

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Resend** | Modern API, free tier, React templates | New service | ✅ Post-MVP |
| **SendGrid** | Reliable, 100 emails/day free | Complex API | ❌ Backup |
| **Mailgun** | Good deliverability | Paid after 5k | ❌ Later |

**Use Cases** (Post-MVP):
- Welcome email
- Password reset
- Trade notifications
- Weekly digest

**Setup**:
1. Sign up at resend.com
2. Verify domain (or use test mode)
3. Get API key
4. Store in env: `RESEND_API_KEY`

**Free Tier (Resend)**: 3,000 emails/month

**MVP Decision**: Skip for MVP, add in Week 3.

---

## 7. ANALYTICS & MONITORING

### Service: Application Monitoring

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Sentry** | Error tracking, free tier, easy setup | Limited events | ✅ YES |
| **LogRocket** | Session replay, performance | Paid | ❌ Post-MVP |
| **Datadog** | Full observability | Complex, expensive | ❌ Later |

**Implementation**:
- **SDK**: `sentry-sdk` (Python), `@sentry/react` (JS)
- **Captures**: Errors, exceptions, performance issues

**Setup**:
1. Sign up at sentry.io
2. Create project (Python + React)
3. Get DSN (Data Source Name)
4. Add to backend:
```python
import sentry_sdk
sentry_sdk.init(dsn="https://...", traces_sample_rate=1.0)
```
5. Add to frontend:
```javascript
import * as Sentry from "@sentry/react";
Sentry.init({ dsn: "https://..." });
```

**Free Tier**: 5,000 events/month (enough for MVP)

---

### Service: User Analytics

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **PostHog** | Open-source, self-hosted or cloud, free tier | Learning curve | ✅ YES |
| **Mixpanel** | Great UX, free tier | Limited events | ❌ Backup |
| **Google Analytics 4** | Free, universal | Privacy concerns, complex | ❌ Later |

**Implementation**:
- **SDK**: `posthog-js` (frontend)
- **Tracks**: Page views, button clicks, trades, signups

**Setup**:
1. Sign up at posthog.com (cloud version)
2. Create project
3. Get API key
4. Add to frontend:
```javascript
import posthog from 'posthog-js';
posthog.init('YOUR_API_KEY', { api_host: 'https://app.posthog.com' });
```

**Events to Track**:
- `user_signed_up`
- `post_created`
- `trade_executed` (buy/sell)
- `post_viewed`
- `report_submitted`

**Free Tier**: 1M events/month

---

## 8. PAYMENTS / ONRAMP (POST-MVP)

### Service: Credit Purchase (Future)

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Stripe** | Standard, reliable, easy | 2.9% fee | ❌ Phase 2 |
| **Crypto Onramp (Coinbase, Transak)** | Web3 native | Complex, KYC | ❌ Phase 3 |
| **PayPal** | Widely used | Higher fees | ❌ Alternative |

**MVP Decision**: Credits are free (signup bonus). No real money yet.

**Phase 2**: Allow users to buy credits with Stripe.

**Phase 3**: Allow users to bridge credits to on-chain tokens.

---

## 9. SEARCH (POST-MVP)

### Service: Full-Text Search

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Postgres Full-Text Search** | Built-in, free, good enough | Slower at scale | ✅ MVP |
| **Algolia** | Fast, great UX, free tier | Limited records | ❌ Phase 2 |
| **Typesense** | Open-source, fast | Self-hosted | ❌ Later |

**MVP Implementation**: Use Postgres `ILIKE` for simple text search.

```sql
SELECT * FROM posts WHERE content ILIKE '%keyword%';
```

**Phase 2**: Add Postgres full-text search with `tsvector`.

**Phase 3**: Migrate to Algolia for advanced features (typo tolerance, facets).

---

## 10. NOTIFICATIONS (POST-MVP)

### Service: Push Notifications

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Firebase Cloud Messaging** | Free, reliable, cross-platform | Google dependency | ❌ Phase 2 |
| **OneSignal** | Easy setup, free tier | Limited subscribers | ❌ Alternative |
| **Pusher** | Real-time, WebSockets | Paid | ❌ Later |

**MVP Decision**: No push notifications. Use in-app notifications (query DB on page load).

**Phase 2**: Add email notifications (Resend).

**Phase 3**: Add push notifications (FCM).

---

## 11. BLOCKCHAIN RPC (PHASE 2/3)

### Service: Blockchain Access

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Alchemy** | Reliable, free tier, good docs | Limited requests | ❌ Phase 2 |
| **Infura** | Standard, trusted | Rate limits | ❌ Alternative |
| **QuickNode** | Fast, multi-chain | Paid | ❌ Later |

**MVP Decision**: No blockchain. Centralized ledger only.

**Phase 2**: Add Base or Solana RPC for on-chain migration.

---

## 12. CDN (OPTIONAL)

### Service: Content Delivery Network

**Options**:

| Option | Pros | Cons | MVP Choice |
|--------|------|------|-----------|
| **Cloudflare** | Free, fast, DDoS protection | Learning curve | ✅ Production |
| **Vercel (built-in)** | Automatic for frontend | Frontend only | ✅ Frontend |
| **CloudFront** | AWS integration | Complex setup | ❌ Later |

**MVP Decision**: 
- Frontend: Deploy to Vercel (CDN included)
- Backend: Use Cloudflare for DDoS protection (post-MVP)
- Images: Cloudinary (CDN included)

---

## COST SUMMARY (MVP)

| Service | Cost (MVP) | Cost (100 DAU) | Cost (1000 DAU) |
|---------|------------|----------------|------------------|
| Google OAuth | Free | Free | Free |
| Cloudinary | Free | Free | Free (~20GB) |
| OpenAI Moderation | Free | Free | Free |
| PostgreSQL (Local) | Free | Free | N/A |
| PostgreSQL (Supabase) | N/A | Free | $25/mo |
| Redis (Local) | Free | Free | N/A |
| Redis (Upstash) | N/A | Free | Free |
| Sentry | Free | Free | Free (5k events) |
| PostHog | Free | Free | Free (~50k events) |
| Vercel (Frontend) | Free | Free | Free |
| Railway (Backend) | N/A | $5/mo | $20/mo |
| **TOTAL** | **$0** | **$5-10/mo** | **$50-100/mo** |

---

## ENV VARS CHECKLIST

**Backend (.env)**:
```bash
# Database
DATABASE_URL=postgresql://infofi:infofi123@localhost:5432/infofi_db

# Redis
REDIS_URL=redis://localhost:6379

# Auth
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600  # 1 hour

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback

# Image Upload
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# AI Moderation (Option 1: OpenAI)
OPENAI_API_KEY=sk-...

# AI Moderation (Option 2: Emergent Universal Key)
EMERGENT_API_KEY=your-emergent-key

# Monitoring
SENTRY_DSN=https://...@sentry.io/...

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_POSTS_PER_DAY=10
RATE_LIMIT_TRADES_PER_HOUR=100
```

**Frontend (.env)**:
```bash
REACT_APP_API_URL=http://localhost:8001
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id
REACT_APP_SENTRY_DSN=https://...@sentry.io/...
REACT_APP_POSTHOG_KEY=your-posthog-key
REACT_APP_CLOUDINARY_CLOUD_NAME=your-cloud-name
REACT_APP_CLOUDINARY_UPLOAD_PRESET=your-upload-preset
```

---

## NEXT STEPS

1. Sign up for required services:
   - Google Cloud (OAuth)
   - Cloudinary (Images)
   - OpenAI (Moderation) OR use Emergent Universal Key
   - Sentry (Errors)
   - PostHog (Analytics)

2. Create `.env` files with credentials

3. Test each integration in isolation before integrating

4. Proceed to codebase generation

---

**Document Version**: 1.0  
**Last Updated**: Jan 2026  
**Status**: APPROVED - Services identified
