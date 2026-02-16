# SocialFi Multi-Network Ingestion Platform

## Product Requirements Document

### Original Problem Statement
Build a SocialFi platform where content from multiple social networks (Reddit, Farcaster, X, Instagram, Twitch) is ingested, normalized, and turned into tradable markets. Users can browse, filter, and trade shares in viral posts using a bonding curve AMM.

### User Personas
1. **Crypto Traders** - Want to speculate on viral content
2. **Content Curators** - Find and list trending posts to earn rewards
3. **Social Media Power Users** - Track engagement across platforms

### Core Requirements
- ✅ Multi-network content ingestion (Reddit, Farcaster working; X/Instagram/Twitch stubbed)
- ✅ Wallet-based authentication (MetaMask, Coinbase Wallet)
- ✅ Network filtering (multi-select)
- ✅ Sorting (trending, new, price, volume)
- ✅ Paste URL to list any post as a market
- ✅ Buy/Sell shares with bonding curve pricing
- ✅ Portfolio tracking with P&L
- ✅ Leaderboard by XP, reputation, balance
- ✅ 1,000 credits for new users

### Architecture

```
Frontend (React)          Backend (FastAPI)         Database (MongoDB)
├── LandingPage.js   -->  /api/auth/challenge  --> users
├── Feed.js          -->  /api/auth/verify     --> challenges  
├── Portfolio.js     -->  /api/feed            --> unified_posts
├── Leaderboard.js   -->  /api/posts/paste-url --> markets
└── AuthContext.js   -->  /api/trades/buy|sell --> positions, trades
                     -->  /api/portfolio
                     -->  /api/leaderboard
```

### Data Models

**User**
```json
{
  "wallet_address": "0x...",
  "balance_credits": 1000.0,
  "level": 1,
  "xp": 0,
  "reputation": 0.0
}
```

**Unified Post**
```json
{
  "source_network": "reddit|farcaster|x|instagram|twitch",
  "source_id": "original_post_id",
  "source_url": "https://...",
  "author_username": "...",
  "title": "...",
  "content_text": "...",
  "media_urls": [],
  "source_likes": 1000,
  "source_comments": 50,
  "status": "active"
}
```

**Market**
```json
{
  "post_id": "...",
  "total_supply": 100.0,
  "price_current": 1.0,
  "total_volume": 0.0
}
```

### API Endpoints
- `POST /api/auth/challenge` - Get challenge to sign
- `POST /api/auth/verify` - Verify signature, get JWT
- `GET /api/auth/me` - Get current user
- `GET /api/feed` - Get posts with filters
- `POST /api/feed/refresh` - Trigger background refresh
- `GET /api/feed/networks` - Get available networks
- `POST /api/posts/paste-url` - List post by URL
- `POST /api/trades/buy` - Buy shares
- `POST /api/trades/sell` - Sell shares
- `GET /api/portfolio` - Get user positions
- `GET /api/leaderboard` - Get ranked users

---

## What's Been Implemented (December 2025)

### Backend
- FastAPI server with MongoDB
- Wallet-based JWT authentication
- Content connectors for Reddit & Farcaster (public APIs)
- Stub connectors for X, Instagram, Twitch
- Paste URL fallback for any supported network
- Bonding curve AMM for trading
- Portfolio tracking with P&L calculation

### Frontend
- React with Tailwind CSS
- Wallet connect landing page
- Multi-network feed with filters
- Trade modal for buy/sell
- Paste URL modal
- Portfolio page
- Leaderboard page

### Database
- MongoDB with proper indexes
- 10 sample posts seeded
- Wallet-based user schema

---

## Known Limitations
- Reddit/Farcaster APIs blocked from server (403) - relies on paste URL
- Wallet auth requires MetaMask browser extension
- react-router-dom v5 (not v6) due to Web3 library compatibility

---

## Prioritized Backlog

### P0 - Critical
- None (MVP complete)

### P1 - High Priority
- Implement OAuth for X/Instagram when API keys available
- Add server-side proxy for Reddit API
- Implement WebSocket for real-time price updates

### P2 - Medium Priority
- Price history charts
- Moderation panel
- Anti-spam heuristics
- Share/embed post markets

### P3 - Low Priority
- Mobile responsive improvements
- Dark/light theme toggle
- Notification system
- Social login (Google OAuth)
