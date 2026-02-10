# InfoFi/SocialFi Platform - MVP Product Specification

## Executive Summary
A social platform where every post becomes a tradable attention asset. Users create content, and markets determine its value through a bonding curve AMM. Creators earn from trading activity, and discovery is driven by market signals.

---

## A) CORE USER STORIES

### 1. Creator
- **Post Content**: Create text + image + link posts
- **Auto-Market Creation**: Each post mints a market with 100 initial shares
- **Earn Fees**: Receive 50% of all trading fees on their post
- **Track Performance**: See post volume, price, holder count
- **Reputation Building**: Gain reputation from successful posts

### 2. Trader
- **Browse Feed**: Discover posts ranked by market signals
- **Buy Shares**: Speculate on post virality (price increases with supply)
- **Sell Shares**: Exit positions at current market price
- **Portfolio View**: Track all holdings, P&L, and transaction history
- **Leaderboard**: Compete on total portfolio value

### 3. Reader
- **Discovery Feed**: View trending content by volume/price/holders
- **Engagement**: Like, comment (post-MVP), share
- **Market Signals**: See price charts, trading activity
- **Following**: Subscribe to creators (post-MVP)

### 4. Moderator
- **Review Queue**: Process user reports
- **Content Actions**: Hide, delete, warn, ban
- **Market Resolution**: Freeze markets, process refunds
- **Audit Trail**: All actions logged

### 5. Admin
- **Dashboard**: DAU, posts/day, volume, revenue, retention
- **Parameter Tuning**: Adjust fees, limits, bonding curve
- **User Management**: Ban/unban, adjust balances
- **Abuse Monitoring**: Detect manipulation, sybil attacks

---

## B) MARKET OBJECT MODEL

### What Gets Tokenized?
**Individual Posts Only** (MVP scope)
- 1 Post = 1 Market = 1 Tradable Asset
- Post-MVP: Creator tokens, topic tokens, community tokens

### Market Lifecycle
1. **Creation**: User posts content → market auto-created
2. **Minting**: 100 shares initially minted to creator at base price (1 credit/share)
3. **Trading**: Users buy/sell shares via bonding curve
4. **Fees**: 2% on each trade, split 50/30/20 (creator/platform/liquidity)
5. **Maturity**: Markets never expire (unless moderated)

### Bonding Curve Mechanics
```
Formula: price = base_price × (total_supply ^ exponent)
Base Price: 0.01 credits
Exponent: 1.5

Example:
Supply 100 → Price = 0.01 × 100^1.5 = 10 credits/share
Supply 200 → Price = 0.01 × 200^1.5 = 28.28 credits/share

Buy Cost: Integral of curve from supply to supply+shares × (1 + 0.02)
Sell Revenue: Integral of curve from supply-shares to supply × (1 - 0.02)
```

### Fee Distribution
- **Trading Fee**: 2% per transaction
- **Creator**: 50% (1% of trade)
- **Platform**: 30% (0.6% of trade)
- **Liquidity Pool**: 20% (0.4% of trade, for future rewards)

---

## C) ANTI-SPAM & SYBIL RESISTANCE

### Post Creation Barriers
1. **Stake Requirement**: 10 credits minimum to create post
2. **Rate Limits**: 
   - 10 posts per day per user
   - 1 post per 5 minutes burst limit
3. **Account Age**: 24-hour seasoning period for new accounts
4. **Reputation Threshold**: Need 5+ reputation to create unlimited posts

### Trading Restrictions
1. **Minimum Trade**: 1 credit minimum per transaction
2. **Rate Limits**: 100 trades per hour
3. **Wash Trading Detection**: Flag users trading own posts excessively
4. **Price Manipulation**: Alert on rapid price swings (>50% in 5min)

### Reputation System
```
Reputation Score Calculation:
- Post created: +0.5 points
- Post reaches 1000 volume: +5 points
- Accurate report: +2 points
- False report: -5 points
- Banned: -50 points
- Trade completed: +0.1 points

Reputation Gates:
- 0-5: Limited posting (5 posts/day)
- 5-20: Normal user
- 20-50: Power user (higher limits)
- 50+: Trusted creator (VIP perks)
```

### Sybil Defenses
1. **Device Fingerprinting**: Track IP, User-Agent, browser fingerprint
2. **Email Verification**: Required for signup
3. **OAuth Integration**: Google login provides identity proof
4. **Behavioral Analysis**: Flag suspicious patterns (multiple accounts, coordinated trading)
5. **Progressive Trust**: New accounts start with limited privileges

---

## D) MODERATION FLOW

### Content Policy (Minimal for MVP)
**Prohibited Content**:
- Illegal activity
- CSAM, extreme violence, terrorism
- Spam/scams
- Impersonation
- Market manipulation schemes

**Allowed Content**:
- Opinions, satire, memes
- Political/controversial topics (with warnings)
- NSFW (tagged, age-gated post-MVP)

### Moderation Pipeline

#### 1. Pre-Publishing AI Screen
```
Post Submitted → OpenAI Moderation API → Decision:
- Pass: Published immediately
- Flag: Queued for manual review, published with "under review" tag
- Block: Rejected, user notified
```

#### 2. User Reporting
```
User Reports Post → Select Reason:
- Spam
- Harassment
- Illegal content
- Manipulation
- Other (text description)

→ Report logged → Queue for moderator
```

#### 3. Moderator Review
```
Moderator Views Report → Context (post, reporter, history) → Actions:
- Dismiss: False report, ding reporter reputation
- Warn: Send warning to creator, no market impact
- Hide: Remove from feed, market continues
- Delete: Remove content, freeze market, refund traders at last price
- Ban: Delete all user posts, ban account
```

#### 4. Appeals Process
```
User Appeals → Submits explanation → Senior mod review → Decision:
- Overturn: Restore content, restore market
- Uphold: Appeal denied
- Partial: Reduce penalty (ban → suspension)

SLA: 48-hour response time
```

### Market Actions on Moderation
- **Deleted Post**: Market frozen, no new trades, existing holders refunded at last traded price
- **Hidden Post**: Market continues, not shown in feed
- **Warned Post**: Market unaffected, warning displayed

---

## E) METRICS DASHBOARD (For Operators)

### Growth Metrics
- **DAU/MAU**: Daily/Monthly Active Users
- **New Signups**: Per day, source attribution
- **Retention**: D1/D7/D30 cohort retention curves
- **Engagement**: Posts/user/day, trades/user/day, session time

### Economic Metrics
- **Total Volume**: Credits traded per day
- **Total Posts**: Created per day
- **Total Markets**: Active markets
- **Fee Revenue**: Platform fees collected (30% of trading fees)
- **Creator Earnings**: Top earners, average per post
- **Average Market Cap**: Average total value locked per market

### Health Metrics
- **Reports per 1000 posts**: Moderation load
- **Report resolution time**: Avg time to moderate
- **False positive rate**: % of dismissed reports
- **Ban rate**: Users banned per week
- **Market manipulation incidents**: Detected wash trading, pump/dump

### Technical Metrics
- **API Latency**: p50/p95/p99 response times
- **Error Rate**: 5xx errors per minute
- **Uptime**: 99.9% target
- **Database Size**: Growth rate, backup status

---

## F) KEY FLOWS

### Flow 1: Create Post & Market
```
1. User clicks "Create Post"
2. Fills form: text (280 chars), optional image, optional link
3. Submits → AI moderation check → Pass
4. Post created in DB
5. Market auto-created:
   - Mint 100 shares to creator at 1 credit/share
   - Deduct 100 credits from creator balance (they own the shares)
   - Set initial supply = 100
6. Post appears in feed
7. Creator notified: "Your post is live! Market created with 100 shares."
```

### Flow 2: Buy Shares
```
1. User sees post in feed, clicks "Buy"
2. Trade drawer opens:
   - Current price: 10 credits/share
   - User inputs: 5 shares
   - Total cost: 52.5 credits (50 base + 2.5 fee)
   - Breakdown shown
3. User confirms
4. Backend:
   - Validate balance (user has ≥52.5 credits)
   - Calculate exact cost using bonding curve integral
   - Deduct credits from buyer
   - Credit fees: 50% to creator, 30% platform, 20% liquidity pool
   - Update market supply
   - Record trade in DB
5. UI updates: "You bought 5 shares for 52.5 credits"
6. Portfolio updated
```

### Flow 3: Sell Shares
```
Similar to buy, but:
- User selects shares to sell from portfolio
- Receives credits minus 2% fee
- Market supply decreases
```

### Flow 4: Report Content
```
1. User clicks "Report" on post
2. Selects reason, optional description
3. Report submitted → Queue
4. Moderator reviews within 24hr
5. User notified of outcome
```

---

## G) MVP SCOPE & POST-MVP

### MVP (Day 14)
✅ Email/OAuth authentication
✅ Create posts (text + image + link)
✅ Auto-market creation per post
✅ Buy/sell shares via bonding curve
✅ Feed ranked by market signals
✅ Portfolio view
✅ Basic moderation (AI + manual queue)
✅ User reporting
✅ Admin dashboard
✅ Reputation system
✅ Rate limiting

### Post-MVP (Phase 2)
- Comments & likes
- Creator tokens (bet on all creator's posts)
- Topic/hashtag markets
- Following/notifications
- Advanced charts (price history, volume)
- Leaderboards
- Referral program
- Mobile app
- Migrate to on-chain (Base/Solana)

---

## H) RISKS & MITIGATIONS

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Regulatory scrutiny (securities law) | Medium | High | Disclaimers, credits (not crypto), avoid derivatives, geo-block if needed |
| Low liquidity (thin markets) | High | Medium | Seed initial posts, invite engaged users, incentivize trading |
| Spam/bot attacks | High | High | Rate limits, reputation, captcha, manual review queue |
| Market manipulation | Medium | Medium | Wash trading detection, price movement alerts, moderator tools |
| AI moderation failures | Medium | Low | Manual review queue, user reports, appeal process |
| Scalability (DB bottleneck) | Low | Medium | Redis caching, DB indexing, horizontal scaling plan |
| User acquisition | High | High | Invite-only launch, seed with engaged creators, viral mechanics |
| Creator payment delays | Low | Medium | Instant credit balance updates, withdraw later (post-MVP) |

---

## I) SUCCESS METRICS (Day 14 MVP)

**Launch Targets**:
- 50-100 active users
- 200+ posts created
- $1000+ credits traded (simulated volume)
- <5% abuse rate
- <10% churn after D7

**Week 2-4 Goals**:
- 500 users
- 2000+ posts
- $50k credits traded
- 20+ DAU
- Viral coefficient >1.2

---

## J) DISCLAIMERS (For Legal Compliance)

**Displayed on signup & trade pages**:
> "This platform uses virtual credits for content markets. Credits have no cash value and cannot be redeemed for money. This is not an investment product, security, or financial instrument. Markets are for entertainment and information discovery only. By using this platform, you agree to our Terms of Service and understand that all credits may be lost."

**Age Gate**: 18+ only (for MVP, honor system; post-MVP: verify via ID)

**Geo-Blocking** (if needed): Block access from jurisdictions with strict securities laws (implement post-MVP if required)

---

## K) NEXT STEPS

1. Review and approve this spec
2. Proceed to technical architecture
3. Generate codebase scaffold
4. Begin Day 1-2 implementation (auth, DB, base API)
5. Daily standups to track against 14-day plan
6. Seed initial users & content on Day 12
7. Soft launch Day 14

---

**Document Version**: 1.0  
**Last Updated**: Jan 2026  
**Status**: APPROVED - Ready for build
