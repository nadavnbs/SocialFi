# Multi-Network SocialFi Platform - Product Specification

## A) PRODUCT SPEC EXTENSION

### New User Stories

#### 1. Content Discovery User
**As a trader**, I want to:
- Browse posts from multiple social networks in one unified feed
- Filter by specific networks (X, Instagram, Reddit, Farcaster, Twitch)
- Sort by trending, newest, or biggest movers
- See market data for each post (price, volume, 24h change)
- Trade on any post from any network

#### 2. Social Account Connector
**As a content creator**, I want to:
- Connect my Reddit/Farcaster/Twitch accounts
- See my posts automatically listed for trading
- Earn fees when others trade my content
- Track earnings across all networks

#### 3. Post Lister (Manual)
**As any user**, I want to:
- Submit a post URL from any supported network
- Have the system fetch and list it (if compliant)
- Create a market for that post
- Trade on submitted posts

#### 4. Market Trader
**As a trader**, I want to:
- Buy shares in posts I think will go viral
- Sell shares to take profits
- See live price updates
- Track my portfolio across all networks

#### 5. Watchlist Manager
**As an active trader**, I want to:
- Add posts to my watchlist
- Get alerts when price moves >X%
- See aggregated metrics for watched posts

---

### Market Object Mapping for External Posts

#### URL Canonicalization
Each external post must have a unique canonical URL:
- **Reddit**: `https://reddit.com/r/{subreddit}/comments/{post_id}`
- **Farcaster**: `https://warpcast.com/{username}/{cast_hash}`
- **Twitch**: `https://twitch.tv/videos/{video_id}` or `clips/{clip_slug}`
- **X/Twitter**: `https://x.com/{username}/status/{tweet_id}`
- **Instagram**: `https://instagram.com/p/{shortcode}`

#### Deduplication Strategy
1. Hash the canonical URL → unique ID
2. Before creating market, check if UnifiedPost exists with that URL
3. If exists, return existing market
4. If new, create UnifiedPost + PostMarket atomically

#### Market Lifecycle
- **Creation**: Auto-created when post first ingested or manually listed
- **Initial Supply**: 100 shares minted to platform (later: to creator if verified)
- **Trading**: Bonding curve AMM (same as before)
- **Expiry**: Posts don't expire (unless deleted/removed at source)

---

### Listing Rules

#### Who Can List?
1. **Automated Ingestion**: System ingests public posts from connected networks
2. **Manual Submission**: Any authenticated user can submit a post URL
3. **Connected Accounts**: Users who connect their social accounts get auto-listings

#### Spam Prevention
1. **Rate Limits**:
   - Max 10 manual submissions per user per day
   - Max 100 posts ingested per network per hour (system-wide)
   
2. **Minimum Requirements**:
   - Post must be at least 10 minutes old (prevent instant gaming)
   - Author must have minimum follower/karma threshold (network-specific)
   - Content must pass basic text moderation

3. **Stake to List** (optional, post-MVP):
   - User can stake 50 credits to list any post
   - Stake returned if post reaches 100 volume
   - Stake lost if post flagged as spam

4. **Duplicate Prevention**:
   - URL hash uniqueness enforced
   - Similar content detection (cosine similarity >0.95 = reject)

---

### Network Filtering UX Spec

#### Multi-Select Filter
**Location**: Top of feed, below header

**UI Design**:
```
[All Networks ▼] [Trending ▼] [24h ▼]

☑ Reddit      ☑ Farcaster    ☑ Twitch
☐ X           ☐ Instagram
```

**Behavior**:
- Default: All networks selected
- Click network to toggle on/off
- Must have at least 1 network selected
- Filter persisted to localStorage
- Real-time feed update (no page reload)

#### Filter Combinations
- **Networks** (multi-select): Reddit, Farcaster, Twitch, X, Instagram
- **Sort** (single): Trending (volume), Newest (time), Movers (24h price change)
- **Time Range** (single): 1h, 24h, 7d, All

#### Visual Indicators
Each post card shows:
- Network badge (icon + name) - color-coded
- Reddit: Orange
- Farcaster: Purple
- Twitch: Purple
- X: Black
- Instagram: Pink gradient

---

### Anti-Spam & Anti-Manipulation

#### Sybil Resistance
1. **Wallet-based**: One wallet = one account
2. **Activity Threshold**: Need 5 trades OR 1 post with 50 volume to unlock full features
3. **Reputation System**: Score based on:
   - Successful trades (profitable)
   - Created posts that gained traction
   - Reports accuracy

#### Wash Trading Detection
1. **Self-Trading**: Flag if user trades own listed posts >3 times
2. **Circular Trading**: Detect patterns where A→B→C→A with same post
3. **Volume Manipulation**: Alert if 80% of volume comes from 2-3 wallets
4. **Cooldown**: 5-minute delay between trades on same market

#### Rate Limits (Per User)
- **Trading**: 100 trades/hour
- **Listing**: 10 posts/day
- **Reports**: 20 reports/day
- **API Calls**: 60/minute

---

### Moderation Flow

#### Report Reasons
1. Spam / Bot content
2. Stolen/Reposted content
3. Inappropriate content (NSFW without tag)
4. Manipulation (fake engagement)
5. Copyright violation
6. Other (text field)

#### Moderation Actions
1. **Dismiss**: False report, no action
2. **Hide**: Remove from feed, market continues
3. **Delist**: Freeze market, refund traders
4. **Ban User**: Ban wallet from platform

#### AI Moderation (Minimal)
- Use OpenAI Moderation API for text content
- Flag posts with:
  - Hate speech
  - Sexual content
  - Violence
  - Self-harm
- Flagged posts go to manual review queue
- Auto-hide posts with confidence >0.9

---

### Creator Fee Capture

#### Fee Split (Per Trade)
**2% trading fee split**:
- **50% Creator** (external social account owner, if verified)
- **30% Platform** (protocol revenue)
- **20% Liquidity Pool** (for future rewards)

#### Creator Verification
1. **Phase 1 (MVP)**: All creator fees go to platform
2. **Phase 2**: Users can link social accounts (OAuth)
3. **Phase 3**: Verified creators get fees deposited to their wallet

#### Unclaimed Fees
- If creator not verified: fees accumulate in escrow
- Creator can claim by verifying ownership (OAuth + signature)
- Unclaimed fees after 90 days → platform treasury

---

### Success Metrics

**MVP Launch Targets (Week 1)**:
- 100+ posts ingested across 2+ networks
- 50+ active traders
- $10k+ trading volume
- <5% spam rate
- 10+ creator accounts connected

**Growth Metrics (Month 1)**:
- 1000+ posts
- 500+ active traders
- $100k+ volume
- 3+ networks fully integrated
- <2% spam rate

---

## Next: Data + Connector Design →
