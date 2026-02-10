# InfoFi/SocialFi Platform - MVP

A social platform where every post becomes a tradable attention asset. Users create content, and markets determine its value through a bonding curve AMM. Creators earn from trading activity, and discovery is driven by market signals.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)
- PostgreSQL 15+

### Local Development

1. **Clone and setup**:
```bash
cd /app
```

2. **Backend Setup**:
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL database
# Make sure PostgreSQL is running on localhost:5432
# Create database: infofi_db

# Run migrations (database will be created automatically)
python -c "from database import init_db; init_db()"

# Start backend server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

3. **Frontend Setup**:
```bash
cd frontend

# Install dependencies
yarn install

# Start frontend
yarn start
```

4. **Access the app**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Docker Compose (Full Stack)

```bash
# From /app directory
docker-compose up --build
```

This will start:
- PostgreSQL (port 5432)
- Backend API (port 8001)
- Frontend (port 3000)

## 📚 Documentation

See the following docs for detailed information:

- **[PRODUCT_SPEC.md](./PRODUCT_SPEC.md)**: Full MVP product specification, user stories, market mechanics, anti-spam measures, moderation flow
- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: Technical architecture, data models, API endpoints, AMM engine, eventing
- **[BUILD_PLAN.md](./BUILD_PLAN.md)**: 14-day execution plan with daily milestones and demos
- **[SERVICES_APIS.md](./SERVICES_APIS.md)**: External services required, integration options, cost estimates
- **[SECURITY_COMPLIANCE.md](./SECURITY_COMPLIANCE.md)**: Security measures, threat models, compliance notes

## 🎯 Key Features (MVP)

### For Users
- **Create Posts**: Share text, images, links (max 500 chars)
- **Auto-Market Creation**: Each post mints a market with 100 initial shares
- **Trade Shares**: Buy/sell shares via bonding curve AMM
- **Portfolio Tracking**: View all holdings, P&L, transaction history
- **Discovery Feed**: Posts ranked by volume, price, or recency

### For Creators
- **Earn Fees**: Receive 50% of all trading fees on your posts
- **Reputation System**: Build reputation through successful posts
- **Market Analytics**: Track your post's volume, price, holders

### For Admins
- **Dashboard**: DAU, posts, volume, fees, reports
- **Moderation**: Review reports, hide/delete posts, ban users
- **User Management**: Adjust balances, view activity

## 🏗️ Architecture

### Stack
- **Frontend**: React 19 + TailwindCSS + shadcn/ui
- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL 15 (users, posts, markets, trades, balances)
- **Auth**: JWT (email/password, OAuth ready)
- **Market**: Bonding curve AMM (centralized ledger for MVP)

### API Endpoints

#### Auth
```
POST   /api/auth/register        - Register with email/password
POST   /api/auth/login           - Login, get JWT
GET    /api/auth/me              - Get current user
```

#### Posts & Markets
```
POST   /api/posts                - Create post (auto-creates market)
GET    /api/posts                - List posts (sort by volume/price/new)
GET    /api/posts/:id            - Get single post with market
GET    /api/markets/:id/quote    - Get price quote for X shares
```

#### Trading
```
POST   /api/trades/buy           - Buy shares
POST   /api/trades/sell          - Sell shares
GET    /api/users/me/portfolio   - Get portfolio
GET    /api/trades/history       - Trade history
```

#### Admin
```
GET    /api/admin/dashboard      - Platform metrics
POST   /api/admin/users/:id/ban  - Ban user
POST   /api/reports              - Create report
GET    /api/reports              - List reports (moderators)
PATCH  /api/reports/:id          - Resolve report
```

## 💰 Market Mechanics

### Bonding Curve
```
Price = 0.01 × (Supply ^ 1.5)

Example:
- 100 shares  → ~1.00 credits/share
- 200 shares  → ~2.83 credits/share
- 500 shares  → ~11.18 credits/share
```

### Trading Fees
- **2% fee per trade**:
  - 50% to post creator
  - 30% to platform
  - 20% to liquidity pool

### Initial State
- New users: 1000 credits signup bonus
- Post creation: 100 credits cost, receive 100 shares

## 🛡️ Security Features

- ✅ Password hashing (bcrypt)
- ✅ JWT authentication
- ✅ Rate limiting (posts, trades, API calls)
- ✅ Input validation (Pydantic models)
- ✅ SQL injection protection (ORM)
- ✅ CORS configured
- ✅ Admin role-based access control
- ✅ Transaction audit logs

## 🔧 Configuration

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://infofi:infofi123@localhost:5432/infofi_db

# Auth
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600  # 1 hour

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Frontend Environment Variables

```bash
REACT_APP_BACKEND_URL=http://localhost:8001
# or for production:
REACT_APP_BACKEND_URL=https://api.yourdomain.com
```

## 🧪 Testing

### Manual Testing

1. **Signup Flow**:
```bash
# Register
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }'

# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

2. **Create Post & Trade**:
```bash
# Get token from login response, then:

# Create post
curl -X POST http://localhost:8001/api/posts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "My first prediction: Bitcoin hits 100k in 2026!"
  }'

# Buy shares
curl -X POST http://localhost:8001/api/trades/buy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "market_id": 1,
    "shares": 10
  }'
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8001/api/
# Returns: {"message": "InfoFi/SocialFi API - Version 1.0"}
```

### Database Check
```bash
# Connect to PostgreSQL
psql -h localhost -U infofi -d infofi_db

# Check tables
\dt

# View users
SELECT * FROM users LIMIT 10;

# View markets
SELECT * FROM markets ORDER BY total_volume DESC LIMIT 10;
```

## 🚢 Deployment (Post-MVP)

### Production Recommendations
- **Frontend**: Vercel / Netlify (static hosting)
- **Backend**: Railway / Render / Fly.io (container)
- **Database**: Supabase / Neon (managed PostgreSQL)
- **CDN**: Cloudflare (DDoS protection)
- **Monitoring**: Sentry (errors), PostHog (analytics)

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is an MVP. Contributions welcome after initial launch.

### Roadmap (Post-MVP)
- [ ] Comments & likes
- [ ] Creator tokens (bet on all creator's posts)
- [ ] Topic/hashtag markets
- [ ] Following & notifications
- [ ] Advanced charts (price history, volume over time)
- [ ] Leaderboards
- [ ] Mobile app (React Native)
- [ ] Migrate to on-chain (Base/Solana)

## ⚠️ Disclaimers

**Important**: This platform uses virtual credits for content prediction markets. Credits have no cash value and cannot be exchanged for money. This is not an investment product, security, commodity, or financial instrument. Markets are for entertainment and community engagement only. By using this platform, you agree to our Terms of Service.

**Age Requirement**: 18+ only

---

**Built with ❤️ for the InfoFi/SocialFi revolution**
