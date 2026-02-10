# InfoFi/SocialFi Platform - 14-Day Build Plan

## C) RADICAL EXECUTION: 0→1 IN 2 WEEKS

---

## OVERVIEW

**Goal**: Ship a working MVP with real users creating/trading posts by Day 14.

**Team**: 1-2 developers (assuming full-stack capability)

**Daily Rhythm**:
- Morning: Ship features from plan
- Afternoon: Test, iterate, fix bugs
- Evening: Demo progress, plan next day

**Demos**:
- **Day 3**: Auth working, users can sign up
- **Day 7**: Full trading flow (create post, buy/sell shares)
- **Day 14**: MVP launch with 50-100 test users

---

## PARALLEL WORKSTREAMS

### Stream 1: Backend API (Priority 1)
- Days 1-3: Auth, database, base API
- Days 4-6: Posts, markets, AMM engine
- Days 7-9: Trading, balances, transactions
- Days 10-12: Moderation, reports, admin
- Days 13-14: Performance, monitoring, hardening

### Stream 2: Frontend (Priority 1)
- Days 1-3: Auth UI, layout, nav
- Days 4-6: Feed, post composer, market cards
- Days 7-9: Trade drawer, portfolio, charts
- Days 10-12: Admin dashboard, moderation UI
- Days 13-14: Polish, mobile responsive, UX improvements

### Stream 3: Infrastructure (Priority 2)
- Days 1-2: Docker setup, local dev environment
- Days 3-4: Database migrations, seed data
- Days 5-7: Redis integration, rate limiting
- Days 8-10: Image upload (Cloudinary), AI moderation
- Days 11-14: Monitoring, logging, error tracking

### Stream 4: Compliance & Safety (Priority 2)
- Days 1-7: Disclaimers, terms of service, privacy policy
- Days 8-10: Rate limiting, anti-spam measures
- Days 11-14: Content moderation flow, reporting

---

## DAY-BY-DAY BREAKDOWN

### 🚀 DAY 1-2: FOUNDATION

**Backend**:
- [x] Setup FastAPI project structure
- [x] PostgreSQL connection & schema design
- [x] User model & auth endpoints:
  - POST /api/auth/register (email/password)
  - POST /api/auth/login (returns JWT)
  - GET /api/auth/me
- [x] JWT middleware for protected routes
- [x] Password hashing (bcrypt)
- [x] Database migrations (Alembic)

**Frontend**:
- [x] Setup React project with routing
- [x] Auth pages: Login, Register, OAuth callback
- [x] Protected route wrapper
- [x] Auth context/store (store JWT in localStorage)
- [x] Basic layout: Navbar, sidebar (for later)

**Infra**:
- [x] Docker Compose: Postgres, Redis, FastAPI, React
- [x] Environment variables setup
- [x] Local dev README with setup instructions

**Output**: Users can sign up, log in, see empty dashboard.

---

### 🎯 DAY 3 DEMO: "Authentication Working"

**Demo Script**:
1. Open app at localhost:3000
2. Click "Sign Up" → enter email/password → success
3. Log in → see dashboard with "Welcome, [username]!"
4. Refresh page → still logged in (JWT persisted)
5. Click "Logout" → redirected to login

**Metrics**: Auth flow works end-to-end.

---

### 📝 DAY 4-6: CORE CONTENT & MARKETS

**Backend**:
- [x] Posts model & endpoints:
  - POST /api/posts (create post)
  - GET /api/posts (list, paginated)
  - GET /api/posts/:id (single post)
- [x] Markets model & auto-creation:
  - When post created → create market
  - Mint 100 shares to creator
  - Set initial price
- [x] AMM engine module:
  - `get_price(supply)` function
  - `calculate_buy_cost(supply, shares)` with fees
  - `calculate_sell_revenue(supply, shares)` with fees
- [x] GET /api/markets/:id (market details)
- [x] GET /api/markets/:id/quote (price quote for X shares)

**Frontend**:
- [x] Feed page:
  - Infinite scroll list of posts
  - Each post shows: content, image, creator, market stats (price, volume)
  - Sorted by volume desc (trending)
- [x] Post composer:
  - Modal/drawer with text input (500 char limit)
  - Image upload (Cloudinary integration)
  - Optional link input
  - Submit button → POST /api/posts
- [x] Post card component:
  - Content display
  - Market mini-card: current price, supply, volume
  - "Buy" button

**Infra**:
- [x] Cloudinary setup for image uploads
- [x] Seed database with 10 sample posts/markets

**Output**: Users can create posts, see feed with market data.

---

### 💰 DAY 7: TRADING FLOW

**Backend**:
- [x] Trades endpoints:
  - POST /api/trades/buy (market_id, shares)
  - POST /api/trades/sell (market_id, shares)
  - GET /api/trades/history (user's trades)
- [x] Trade execution logic:
  - Validate user balance
  - Calculate cost using AMM
  - Update market supply
  - Update user balance
  - Record trade in DB
  - Distribute fees (creator, platform, liquidity)
  - Create balance record if new
- [x] Balances model & queries
- [x] Transactions model (audit trail)

**Frontend**:
- [x] Trade drawer:
  - Opens on "Buy" click from post card
  - Shows market details
  - Input: number of shares
  - Real-time cost calculation
  - Confirm button
  - Success/error toast
- [x] Portfolio page:
  - List of all holdings (market, shares owned, current value, P&L)
  - Total portfolio value
  - Recent trades list
- [x] Balance display in navbar (e.g., "1,234 credits")

**Output**: Users can buy/sell shares, see portfolio update in real-time.

---

### 🏆 DAY 7 DEMO: "Full Trading Flow"

**Demo Script**:
1. Log in as User A (1000 credits)
2. Create a post: "Prediction: Bitcoin hits 100k in 2026"
3. Post appears in feed with market (100 shares, 1 credit/share)
4. User B logs in, sees post, clicks "Buy"
5. Trade drawer: buy 10 shares for ~10.5 credits (with fees)
6. Confirm → balance updates (989.5 credits left)
7. User B sees post in portfolio: 10 shares, worth ~10 credits
8. User A (creator) sees balance increased by fee earnings (~0.5 credits)
9. User B sells 5 shares → receives ~5 credits back
10. Portfolio updates automatically

**Metrics**: End-to-end trading works, balances accurate, fees distributed.

---

### 🔍 DAY 8-9: DISCOVERY & RANKING

**Backend**:
- [x] Feed ranking algorithms:
  - Sort by volume (default)
  - Sort by price change (% last 24h)
  - Sort by holders (unique users)
  - Sort by recent activity
- [x] Add filters:
  - Timeframe: 1h, 24h, 7d, all-time
  - Category (post-MVP)
- [x] GET /api/posts?sort=volume&timeframe=24h

**Frontend**:
- [x] Feed controls:
  - Tabs: Trending (volume), Rising (price change), New (recent)
  - Infinite scroll pagination
- [x] Search bar (basic text search, post-MVP: full-text)
- [x] User profile page:
  - Show user's posts
  - Show user's reputation
  - Show user's portfolio (if viewing self)

**Output**: Feed has multiple views, users can discover trending posts.

---

### 🛡️ DAY 10-11: MODERATION & SAFETY

**Backend**:
- [x] AI moderation integration (OpenAI Moderation API):
  - Check on post creation
  - Flag if policy violation
  - Queue for manual review if borderline
- [x] Reports endpoints:
  - POST /api/reports (user reports post)
  - GET /api/reports (moderators only)
  - PATCH /api/reports/:id (resolve report)
- [x] Moderation actions:
  - POST /api/admin/posts/:id/hide
  - POST /api/admin/posts/:id/delete (freezes market)
  - POST /api/admin/users/:id/ban
- [x] Rate limiting middleware:
  - 10 posts per day per user
  - 100 trades per hour
  - 10 reports per day

**Frontend**:
- [x] Report button on posts:
  - Modal with reason dropdown + text input
  - Submit → toast confirmation
- [x] Moderator queue (for moderators/admins):
  - List of pending reports
  - Each report shows: post, reporter, reason, history
  - Actions: Dismiss, Warn, Hide, Delete, Ban
- [x] Admin nav section (only visible to admins)

**Output**: Content can be reported, moderators can review and action.

---

### 📈 DAY 12: ADMIN DASHBOARD

**Backend**:
- [x] Admin metrics endpoints:
  - GET /api/admin/dashboard:
    - DAU (unique users last 24h)
    - Posts created today
    - Total volume today
    - Total fees collected
    - Active markets count
    - Pending reports count
  - GET /api/admin/users (list with filters)
  - GET /api/admin/logs (recent admin actions)

**Frontend**:
- [x] Admin dashboard page:
  - Key metrics cards (DAU, volume, posts, revenue)
  - Charts: volume over time, posts per day (simple bar/line)
  - Recent activity feed
  - Quick actions: view reports, ban user, adjust balance
- [x] User management table:
  - Search users
  - View profile, ban, adjust balance

**Output**: Admins have visibility into platform health and can take actions.

---

### 💅 DAY 13-14: POLISH & LAUNCH PREP

**Backend**:
- [x] Optimize queries (add indexes)
- [x] Add request logging
- [x] Error handling improvements
- [x] Rate limiting refinements
- [x] API documentation (auto-generated Swagger)

**Frontend**:
- [x] Mobile responsive design (TailwindCSS breakpoints)
- [x] Loading states & skeletons
- [x] Error boundaries
- [x] Toast notifications for all actions
- [x] Onboarding flow:
  - Welcome modal on first login
  - "How it works" tooltips
  - Sample posts in empty feed
- [x] Favicon, meta tags, OG images
- [x] Dark mode toggle (optional)

**Infra**:
- [x] Monitoring setup (logs, errors)
- [x] Backup database scripts
- [x] Health check endpoints
- [x] Load testing (simulate 100 users)

**Launch Prep**:
- [x] Seed database with 50 quality posts from fake users
- [x] Invite 20-30 beta testers
- [x] Create launch materials:
  - Landing page with demo video
  - Twitter/Discord announcement
  - Invite codes (optional, for exclusivity)

**Output**: Polished app ready for real users.

---

### 🚀 DAY 14 DEMO: "MVP LAUNCH"

**Launch Checklist**:
- [ ] All core features working
- [ ] 50+ seed posts in feed
- [ ] 20+ beta testers invited
- [ ] Monitoring active
- [ ] Terms of service & disclaimers live
- [ ] Moderation queue monitored
- [ ] Social posts published

**Launch Script**:
1. Soft launch to beta testers (invite-only)
2. Monitor for bugs/issues in first 4 hours
3. Hot-fix any critical issues
4. Expand to wider audience (Twitter, Discord)
5. First 100 signups get bonus credits
6. Track metrics hourly: signups, posts, trades, errors

**Success Metrics (Day 14)**:
- 50-100 registered users
- 200+ posts created
- $1,000+ credits traded
- <5% error rate
- <10% bounce rate
- At least 3 users create >5 posts (power users)

---

## RISKS & MITIGATIONS

| Risk | Mitigation |
|------|------------|
| **Scope creep**: Adding features mid-build | Strict MVP scope, defer all non-essentials to Phase 2 |
| **Technical blockers**: API integration failures | Have backup plans (e.g., skip AI moderation, use manual only) |
| **Time overruns**: Features take longer than planned | Cut non-critical features (e.g., charts, search) |
| **Low user engagement**: Users don't trade | Seed with engaging content, gamify with leaderboards |
| **Bugs in production**: Critical issues on launch | Extensive testing on Day 13, have rollback plan |
| **Regulatory concerns**: Legal questions arise | Consult lawyer early, have disclaimers ready |

---

## POST-LAUNCH (Week 3-4)

### Week 3: Iterate & Improve
- Fix bugs reported by users
- Add most-requested features (comments, likes, notifications)
- Optimize performance (caching, query optimization)
- Improve moderation tools based on moderator feedback

### Week 4: Growth & Retention
- Launch referral program (invite friends, earn credits)
- Add leaderboards (top traders, top creators)
- Email notifications (your post is trending, someone bought your shares)
- Mobile app (React Native or PWA)
- Analytics dashboard for creators (views, volume, earnings)

---

## TOOLS & RESOURCES

### Development
- **IDE**: VSCode with Python & React extensions
- **API Testing**: Postman/Insomnia
- **Database**: DBeaver (GUI for Postgres)
- **Version Control**: Git + GitHub
- **Project Management**: Linear/Notion (track daily tasks)

### Communication
- **Daily Standups**: 15min sync on progress & blockers
- **Demo Videos**: Record 2min demos for Days 3, 7, 14
- **Slack/Discord**: Async updates

### References
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Router Docs](https://reactrouter.com/)
- [Postgres Schema Design](https://www.postgresql.org/docs/)
- [Bonding Curves Explained](https://yos.io/2018/11/10/bonding-curves/)
- [Content Moderation Best Practices](https://www.openai.com/moderation)

---

## NEXT STEPS

1. Review and approve this build plan
2. Setup development environment (Docker, IDE, tools)
3. Kickoff Day 1: Create first PR with auth backend
4. Ship daily, demo frequently
5. Launch on Day 14 🚀

---

**Plan Version**: 1.0  
**Last Updated**: Jan 2026  
**Status**: APPROVED - Let's build!
