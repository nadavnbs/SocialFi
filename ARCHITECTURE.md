# InfoFi/SocialFi Platform - Technical Architecture

## B) SYSTEM ARCHITECTURE

### Stack Justification (Speed > Perfection)

**Frontend**: React 19 + TailwindCSS + shadcn/ui
- Fast development with component library
- Excellent DX, hot reload
- Easy to iterate on UI/UX

**Backend**: FastAPI + Python 3.11
- Rapid API development
- Async support for high concurrency
- Strong typing with Pydantic
- Easy integration with AI services

**Database**: PostgreSQL
- ACID compliance for financial transactions
- Strong indexing for complex queries
- JSON support for flexible schemas
- Battle-tested reliability

**Cache**: Redis (via Docker, local dev)
- Rate limiting
- Session management
- Real-time price caching

**Storage**: Cloudinary (images)
- Free tier for MVP
- CDN included
- Image optimization

**Auth**: JWT + OAuth (Google)
- Standard, secure
- Easy migration to Web3 wallets later

**AI**: OpenAI Moderation API
- Fast, accurate content filtering
- Minimal false positives

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  React App (Browser)                                            │
│  - Feed (Infinite Scroll)                                       │
│  - Post Composer                                                │
│  - Trade Drawer                                                 │
│  - Portfolio                                                    │
│  - Admin Dashboard                                              │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTPS/REST
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Server (uvicorn)                                       │
│  ├─ /api/auth (register, login, refresh)                       │
│  ├─ /api/posts (create, list, get)                             │
│  ├─ /api/markets (get market data, price quote)                │
│  ├─ /api/trades (buy, sell, history)                           │
│  ├─ /api/users (profile, balance, reputation)                  │
│  ├─ /api/reports (create, list for moderators)                 │
│  ├─ /api/admin (dashboard metrics, actions)                    │
│  └─ Middleware: CORS, Auth, Rate Limiting                      │
└────────┬──────────────────────────────────┬───────────────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────────┐          ┌────────────────────────┐
│   BUSINESS LOGIC    │          │   EXTERNAL SERVICES    │
├─────────────────────┤          ├────────────────────────┤
│ AMM Engine          │          │ OpenAI Moderation API  │
│ - Bonding curve     │          │ Cloudinary (images)    │
│ - Buy/sell calc     │          │ Google OAuth           │
│ - Fee distribution  │          │                        │
│                     │          └────────────────────────┘
│ Reputation System   │
│ - Score calculation │
│ - Gates/limits      │
│                     │
│ Rate Limiter        │
│ - Redis-backed      │
│ - Per-user quotas   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database                                            │
│  ├─ users (id, email, username, balance, reputation, ...)      │
│  ├─ posts (id, user_id, content, image_url, status, ...)       │
│  ├─ markets (id, post_id, supply, volume, price, fees)         │
│  ├─ trades (id, market_id, user_id, type, shares, price, ...)  │
│  ├─ balances (user_id, market_id, shares_owned)                │
│  ├─ reports (id, post_id, reporter_id, reason, status, ...)    │
│  ├─ transactions (id, user_id, type, amount, description, ...) │
│  └─ admin_actions (id, admin_id, action_type, target, ...)     │
│                                                                 │
│  Redis Cache                                                    │
│  ├─ Rate limit counters                                         │
│  ├─ Session tokens                                              │
│  └─ Real-time price cache (market_id → current_price)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Model (PostgreSQL Schema)

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- null if OAuth only
    avatar_url TEXT,
    balance_credits DECIMAL(20, 2) DEFAULT 1000.00,  -- Start with 1000 credits
    reputation DECIMAL(10, 2) DEFAULT 0.00,
    is_admin BOOLEAN DEFAULT FALSE,
    is_moderator BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    oauth_provider VARCHAR(50),  -- 'google', 'email'
    oauth_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    CONSTRAINT positive_balance CHECK (balance_credits >= 0)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_reputation ON users(reputation DESC);
```

### Posts Table
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (LENGTH(content) <= 500),
    image_url TEXT,
    link_url TEXT,
    status VARCHAR(20) DEFAULT 'active',  -- active, hidden, deleted, under_review
    moderation_note TEXT,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
```

### Markets Table
```sql
CREATE TABLE markets (
    id SERIAL PRIMARY KEY,
    post_id INTEGER UNIQUE NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    total_supply DECIMAL(20, 2) DEFAULT 100.00,  -- Starts at 100 shares
    total_volume DECIMAL(20, 2) DEFAULT 0.00,  -- Cumulative trading volume
    price_current DECIMAL(20, 6) DEFAULT 1.00,  -- Last traded price
    fees_collected DECIMAL(20, 2) DEFAULT 0.00,  -- Total fees from this market
    liquidity_pool DECIMAL(20, 2) DEFAULT 0.00,  -- 20% of fees
    creator_earnings DECIMAL(20, 2) DEFAULT 0.00,  -- 50% of fees
    is_frozen BOOLEAN DEFAULT FALSE,  -- True if post deleted/moderated
    created_at TIMESTAMP DEFAULT NOW(),
    last_trade_at TIMESTAMP
);

CREATE INDEX idx_markets_post_id ON markets(post_id);
CREATE INDEX idx_markets_volume ON markets(total_volume DESC);
CREATE INDEX idx_markets_price ON markets(price_current DESC);
```

### Trades Table
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    market_id INTEGER NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trade_type VARCHAR(4) NOT NULL CHECK (trade_type IN ('buy', 'sell')),
    shares DECIMAL(20, 2) NOT NULL CHECK (shares > 0),
    price_per_share DECIMAL(20, 6) NOT NULL,
    total_cost DECIMAL(20, 2) NOT NULL,  -- Includes fees for buys, excludes for sells
    fee_amount DECIMAL(20, 2) NOT NULL,
    supply_before DECIMAL(20, 2) NOT NULL,
    supply_after DECIMAL(20, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trades_market_id ON trades(market_id);
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_created_at ON trades(created_at DESC);
```

### Balances Table
```sql
CREATE TABLE balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    market_id INTEGER NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
    shares_owned DECIMAL(20, 2) DEFAULT 0.00 CHECK (shares_owned >= 0),
    avg_buy_price DECIMAL(20, 6) DEFAULT 0.00,  -- For P&L calculation
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, market_id)
);

CREATE INDEX idx_balances_user_id ON balances(user_id);
CREATE INDEX idx_balances_market_id ON balances(market_id);
```

### Reports Table
```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason VARCHAR(50) NOT NULL,  -- spam, harassment, illegal, manipulation, other
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, dismissed, actioned
    reviewed_by INTEGER REFERENCES users(id),
    resolution TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_post_id ON reports(post_id);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL,  -- trade_buy, trade_sell, fee_earned, signup_bonus, refund
    amount DECIMAL(20, 2) NOT NULL,  -- Positive = credit, negative = debit
    balance_after DECIMAL(20, 2) NOT NULL,
    description TEXT,
    reference_id INTEGER,  -- trade_id, market_id, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
```

### Admin Actions Table
```sql
CREATE TABLE admin_actions (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,  -- ban_user, delete_post, adjust_balance, freeze_market
    target_type VARCHAR(50) NOT NULL,  -- user, post, market
    target_id INTEGER NOT NULL,
    reason TEXT,
    metadata JSONB,  -- Additional context
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_admin_actions_admin_id ON admin_actions(admin_id);
CREATE INDEX idx_admin_actions_created_at ON admin_actions(created_at DESC);
```

---

## API Endpoints

### Authentication
```
POST   /api/auth/register        - Create account (email/password)
POST   /api/auth/login           - Login (returns JWT)
POST   /api/auth/oauth/google    - OAuth login/register
POST   /api/auth/refresh         - Refresh JWT token
GET    /api/auth/me              - Get current user profile
```

### Posts
```
POST   /api/posts                - Create post (auto-creates market)
GET    /api/posts                - List posts (paginated, filterable)
GET    /api/posts/:id            - Get single post with market data
DELETE /api/posts/:id            - Delete own post (admin can delete any)
```

### Markets
```
GET    /api/markets/:id          - Get market details
GET    /api/markets/:id/price    - Get current price quote for X shares
GET    /api/markets/:id/chart    - Get price/volume history (post-MVP)
```

### Trades
```
POST   /api/trades/buy           - Buy shares (market_id, shares)
POST   /api/trades/sell          - Sell shares (market_id, shares)
GET    /api/trades/history       - User's trade history
GET    /api/trades/:market_id    - All trades for a market
```

### Users
```
GET    /api/users/:id            - Get user profile (public)
GET    /api/users/me/portfolio   - Get own holdings
GET    /api/users/me/balance     - Get credit balance
PATCH  /api/users/me             - Update profile (username, avatar)
```

### Reports
```
POST   /api/reports              - Report a post
GET    /api/reports              - List reports (moderators only)
PATCH  /api/reports/:id          - Resolve report (moderators only)
```

### Admin
```
GET    /api/admin/dashboard      - Metrics (DAU, volume, posts, etc.)
POST   /api/admin/users/:id/ban  - Ban user
POST   /api/admin/posts/:id/delete - Delete post & freeze market
PATCH  /api/admin/users/:id/balance - Adjust balance (for testing/support)
GET    /api/admin/logs           - Recent admin actions
```

---

## AMM Engine (Bonding Curve Math)

### Price Function
```python
def get_price(supply: float, base: float = 0.01, exponent: float = 1.5) -> float:
    """Calculate price per share at given supply."""
    return base * (supply ** exponent)

def get_buy_cost(current_supply: float, shares: float) -> dict:
    """Calculate cost to buy X shares including fees."""
    # Integral of price function from current_supply to current_supply + shares
    # For p = b * s^e, integral = b/(e+1) * s^(e+1)
    
    base = 0.01
    exp = 1.5
    
    # Cost = integral from supply to supply+shares
    cost_before_fee = (base / (exp + 1)) * (
        (current_supply + shares) ** (exp + 1) - current_supply ** (exp + 1)
    )
    
    fee = cost_before_fee * 0.02  # 2% fee
    total_cost = cost_before_fee + fee
    
    avg_price = cost_before_fee / shares
    new_supply = current_supply + shares
    new_price = get_price(new_supply)
    
    return {
        "cost_before_fee": cost_before_fee,
        "fee": fee,
        "total_cost": total_cost,
        "avg_price": avg_price,
        "new_supply": new_supply,
        "new_price": new_price
    }

def get_sell_revenue(current_supply: float, shares: float) -> dict:
    """Calculate revenue from selling X shares after fees."""
    base = 0.01
    exp = 1.5
    
    # Revenue = integral from supply-shares to supply
    revenue_before_fee = (base / (exp + 1)) * (
        current_supply ** (exp + 1) - (current_supply - shares) ** (exp + 1)
    )
    
    fee = revenue_before_fee * 0.02
    total_revenue = revenue_before_fee - fee
    
    avg_price = revenue_before_fee / shares
    new_supply = current_supply - shares
    new_price = get_price(new_supply)
    
    return {
        "revenue_before_fee": revenue_before_fee,
        "fee": fee,
        "total_revenue": total_revenue,
        "avg_price": avg_price,
        "new_supply": new_supply,
        "new_price": new_price
    }
```

### Fee Distribution
```python
def distribute_fees(fee_amount: float, creator_id: int, post_id: int):
    """
    Split trading fee:
    - 50% to creator
    - 30% to platform
    - 20% to liquidity pool
    """
    creator_fee = fee_amount * 0.50
    platform_fee = fee_amount * 0.30
    liquidity_fee = fee_amount * 0.20
    
    # Credit creator
    update_user_balance(creator_id, +creator_fee, "fee_earned")
    
    # Update market stats
    update_market_fees(post_id, creator_earnings=+creator_fee, liquidity_pool=+liquidity_fee)
    
    # Platform fee tracked separately (not in user balances)
    record_platform_revenue(platform_fee)
```

---

## Eventing & Indexing

### Event Types
```python
POST_CREATED = "post.created"
MARKET_CREATED = "market.created"
TRADE_EXECUTED = "trade.executed"
BALANCE_UPDATED = "balance.updated"
REPORT_SUBMITTED = "report.submitted"
POST_MODERATED = "post.moderated"
USER_BANNED = "user.banned"
```

### Event Flow (MVP: Synchronous)
```
1. User action (create post, trade, report)
2. API handler processes
3. DB transaction commits
4. Event emitted (logged to events table)
5. Background worker processes (post-MVP: use Celery/RQ)
   - Send notifications
   - Update analytics
   - Trigger webhooks
```

### Post-MVP: Async Event Queue
```
FastAPI → PostgreSQL (write) → RabbitMQ/Redis Queue → Worker Pool → Process:
- Email notifications
- Push notifications
- Analytics aggregation
- Fraud detection
- Recommendation engine
```

---

## Caching Strategy

### Redis Cache Keys
```
rate_limit:{user_id}:{action} → count (TTL: 1 hour)
session:{token_hash} → user_id (TTL: 24 hours)
market_price:{market_id} → current_price (TTL: 30 seconds)
feed_cache:page:{n} → post_ids[] (TTL: 2 minutes)
user_balance:{user_id} → balance (TTL: 1 minute)
```

### Cache Invalidation
- Trade executed → invalidate market_price, user_balance, portfolio
- Post created → invalidate feed_cache
- Balance updated → invalidate user_balance

---

## Security Considerations

### Authentication
- JWTs with short expiry (1 hour access, 7 day refresh)
- HTTPOnly cookies for refresh tokens
- bcrypt for password hashing (cost factor 12)
- OAuth state parameter to prevent CSRF

### Authorization
- Role-based access control (user, moderator, admin)
- Own-resource checks (can only edit own posts)
- Rate limiting per user + IP

### Input Validation
- Pydantic models for all inputs
- SQL injection: use parameterized queries (SQLAlchemy ORM)
- XSS: sanitize user content (bleach library)
- Image uploads: validate file type, size, scan for malware (post-MVP)

### Financial Security
- Database transactions for all balance changes
- Idempotency keys for trades (prevent double-execution)
- Audit log for all financial transactions
- Balance checks before trades (prevent overdraft)

---

## Migration Path to On-Chain

### Phase 1 (Current MVP): Centralized
- PostgreSQL ledger
- Custodial credits
- Fast iteration

### Phase 2: Hybrid
- Keep backend APIs
- Add smart contracts (Base/Solana)
- Users can "withdraw" credits to on-chain tokens
- Markets bridge between DB and chain

### Phase 3: Full On-Chain
- All markets as smart contracts
- Backend becomes indexer + API cache
- Users custody own tokens
- Keep moderation layer off-chain

### Abstraction Boundaries (For Easy Migration)
```python
# Interface
class MarketEngine(ABC):
    def create_market(self, post_id: int) -> Market:
        pass
    
    def execute_trade(self, market_id: int, user_id: int, shares: float, trade_type: str) -> Trade:
        pass

# Implementation 1: Database
class DatabaseMarketEngine(MarketEngine):
    # Current MVP
    pass

# Implementation 2: Blockchain
class BlockchainMarketEngine(MarketEngine):
    # Phase 2/3
    pass

# Swap implementations without changing business logic
```

---

## Deployment Architecture (MVP)

### Local Development
```
Docker Compose:
- FastAPI (port 8001)
- React (port 3000)
- PostgreSQL (port 5432)
- Redis (port 6379)
```

### Production (Post-MVP)
```
- Frontend: Vercel/Netlify (static hosting)
- Backend: Railway/Render/Fly.io (container)
- Database: Supabase/Neon (managed Postgres)
- Redis: Upstash (managed Redis)
- Storage: Cloudinary (images)
```

---

**Next**: Proceed to Build Plan & Services List
