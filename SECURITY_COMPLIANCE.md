# InfoFi/SocialFi Platform - Security & Compliance

## E) SECURITY & COMPLIANCE (PRACTICAL)

**Goal**: Secure the MVP without over-engineering. Focus on practical protections that prevent the most common attacks and regulatory issues.

---

## THREAT MODEL

### 1. Wallet/Account Security

**Threats**:
- Password theft (phishing, credential stuffing)
- Session hijacking (XSS, CSRF)
- Account takeover

**Mitigations**:
- ✅ bcrypt password hashing (cost factor 12)
- ✅ JWT tokens with short expiry (1 hour access, 7 day refresh)
- ✅ HTTPOnly cookies for refresh tokens (prevent XSS)
- ✅ CSRF tokens for state-changing requests
- ✅ Rate limit login attempts (5 per minute per IP)
- ❌ Post-MVP: 2FA (TOTP, SMS)
- ❌ Post-MVP: Email alerts for suspicious logins

---

### 2. API Abuse

**Threats**:
- Spam posts (botting)
- Wash trading (fake volume)
- DDoS attacks
- Scraping user data

**Mitigations**:
- ✅ Rate limiting per user + IP:
  - 10 posts per day per user
  - 100 trades per hour per user
  - 60 requests per minute per IP
- ✅ CAPTCHA on signup (hCaptcha, invisible for good users)
- ✅ Reputation gating (new users have lower limits)
- ✅ Device fingerprinting (IP + User-Agent)
- ✅ Cloudflare DDoS protection (post-MVP, production)
- ❌ Post-MVP: Require email verification before posting
- ❌ Post-MVP: SMS verification for high-value actions

**Implementation (Rate Limiting)**:
```python
# backend/middleware/rate_limit.py
import redis
from fastapi import HTTPException

redis_client = redis.Redis.from_url(os.environ['REDIS_URL'])

def rate_limit(user_id: int, action: str, limit: int, window: int):
    """Rate limit a user action.
    
    Args:
        user_id: User ID
        action: Action name (e.g., 'post_create', 'trade')
        limit: Max actions allowed
        window: Time window in seconds
    
    Raises:
        HTTPException: 429 if limit exceeded
    """
    key = f"rate_limit:{user_id}:{action}"
    count = redis_client.incr(key)
    
    if count == 1:
        redis_client.expire(key, window)
    
    if count > limit:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Try again later.")
```

---

### 3. Trade Manipulation

**Threats**:
- Wash trading (user trades own posts to inflate volume)
- Front-running (see pending trades, jump ahead)
- Market manipulation (coordinate pumps/dumps)
- Sybil attacks (multiple accounts)

**Mitigations**:
- ✅ Detect self-trading: Flag if user buys their own post >3 times
- ✅ Monitor rapid price changes: Alert if price moves >50% in 5 minutes
- ✅ Cooldown periods: 5-second delay between trades on same market
- ✅ Volume analysis: Flag markets with 1-2 users accounting for >80% volume
- ✅ Reputation penalties: Reduce reputation for wash trading
- ❌ Post-MVP: Trade batching (execute trades in batches every 10s to prevent front-running)
- ❌ Post-MVP: KYC for high-volume traders (>$10k credits traded)

**Implementation (Self-Trading Detection)**:
```python
def check_self_trading(user_id: int, post_id: int):
    # Get post creator
    post = db.posts.find_one({"id": post_id})
    creator_id = post["user_id"]
    
    if user_id == creator_id:
        # Count how many times user has traded own post
        trade_count = db.trades.count_documents({
            "user_id": user_id,
            "market.post_id": post_id
        })
        
        if trade_count > 3:
            # Flag for review
            create_report(
                post_id=post_id,
                reporter_id=0,  # System report
                reason="self_trading",
                description=f"User has traded own post {trade_count} times"
            )
            
            # Optionally block trade
            raise HTTPException(status_code=403, detail="Self-trading limit exceeded")
```

---

### 4. SQL Injection & XSS

**Threats**:
- SQL injection (malicious queries)
- XSS (script injection in posts)
- NoSQL injection (for MongoDB, if used)

**Mitigations**:
- ✅ Use ORM (SQLAlchemy) for all DB queries (parameterized queries)
- ✅ Sanitize user input (bleach library for HTML, or strip all HTML)
- ✅ Escape output in frontend (React does this by default)
- ✅ Content Security Policy (CSP) headers
- ✅ Validate all inputs with Pydantic models
- ✅ Whitelist allowed characters in usernames (alphanumeric + underscore only)

**Implementation (Input Sanitization)**:
```python
import bleach

ALLOWED_TAGS = []  # No HTML allowed in posts
ALLOWED_ATTRIBUTES = {}

def sanitize_content(text: str) -> str:
    """Remove all HTML tags from user content."""
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

# In post creation:
post_content = sanitize_content(request.content)
```

---

### 5. Data Leaks & Privacy

**Threats**:
- Exposure of user emails, passwords
- Leaking trade history of other users
- Scraping user data via API

**Mitigations**:
- ✅ Never return password hashes in API responses
- ✅ Exclude sensitive fields from public user profiles (email, IP)
- ✅ Require authentication for portfolio/balance endpoints
- ✅ Paginate all list endpoints (prevent bulk scraping)
- ✅ HTTPS only (enforce in production)
- ✅ Encrypt database backups
- ❌ Post-MVP: GDPR compliance (data export, deletion)
- ❌ Post-MVP: Privacy policy, cookie consent

**Implementation (Exclude Sensitive Fields)**:
```python
class UserPublic(BaseModel):
    """Public user profile (safe to expose)."""
    id: int
    username: str
    avatar_url: str
    reputation: float
    created_at: datetime
    # Email, password_hash, IP excluded

class UserPrivate(BaseModel):
    """Private user profile (only for self)."""
    id: int
    username: str
    email: str  # Only visible to self
    avatar_url: str
    balance_credits: float
    reputation: float
    created_at: datetime
```

---

### 6. Admin Access & Privilege Escalation

**Threats**:
- Non-admin users accessing admin endpoints
- Privilege escalation (user makes self admin)
- Admin account compromise

**Mitigations**:
- ✅ Role-based access control (RBAC):
  - `is_admin` flag in users table
  - `is_moderator` flag in users table
- ✅ Middleware to check admin role on admin endpoints
- ✅ Audit log for all admin actions (who, what, when)
- ✅ Cannot change own admin status (requires another admin)
- ❌ Post-MVP: 2FA required for admin accounts
- ❌ Post-MVP: IP whitelist for admin access

**Implementation (Admin Middleware)**:
```python
from fastapi import Depends, HTTPException

def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.post("/api/admin/users/{user_id}/ban")
async def ban_user(user_id: int, admin: User = Depends(require_admin)):
    # Ban logic
    log_admin_action(admin.id, "ban_user", user_id)
    ...
```

---

### 7. Secrets Management

**Threats**:
- API keys leaked in code
- Database credentials in git
- JWTs exposed in logs

**Mitigations**:
- ✅ All secrets in `.env` files (never committed to git)
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment variables in code (`os.environ.get(...)`)
- ✅ Rotate secrets regularly (quarterly)
- ✅ Use different secrets for dev/staging/prod
- ❌ Post-MVP: Use secret manager (AWS Secrets Manager, HashiCorp Vault)

---

## COMPLIANCE

### 1. Avoiding Securities Law

**Risk**: Platform could be classified as an unregistered securities exchange.

**Mitigations**:
- ✅ **Credits, not currency**: Call them "credits" (virtual, no cash value), not "tokens" or "coins"
- ✅ **No redemption**: Credits cannot be cashed out (MVP)
- ✅ **Entertainment only**: Disclaimers state "for entertainment and information discovery"
- ✅ **No leverage/derivatives**: No margin, no options, no futures
- ✅ **No real-world events**: Markets are on posts, not stocks/commodities/elections
- ❌ Post-MVP: Consult lawyer before allowing withdrawals or real-money purchases

**Disclaimer Text** (show on signup and trade pages):
> **Important Notice**: This platform uses virtual credits for content prediction markets. Credits have no cash value and cannot be exchanged for money. This is not an investment product, security, commodity, or financial instrument. Markets are for entertainment and community engagement only. You may lose all credits. By using this platform, you agree to our Terms of Service.

---

### 2. Age Gating

**Requirement**: Most jurisdictions require 18+ for gambling-like activities.

**Implementation**:
- ✅ MVP: Honor system (checkbox "I am 18 or older" on signup)
- ❌ Post-MVP: Age verification via ID (if required by law)
- ✅ Terms of Service: "You must be 18+ to use this platform"

---

### 3. Geo-Blocking

**Risk**: Some jurisdictions ban prediction markets or gambling.

**Jurisdictions to Watch**:
- USA: Varies by state (some ban prediction markets)
- China: Strict controls on online markets
- India: Gambling laws vary

**Implementation**:
- ❌ MVP: No geo-blocking (global access)
- ❌ Post-MVP: If legal issues arise, block via IP geolocation (Cloudflare)
- ✅ Consult lawyer if expanding to regulated markets

---

### 4. Terms of Service & Privacy Policy

**Required Documents**:
- **Terms of Service**:
  - What the platform does
  - User responsibilities
  - Disclaimers (no cash value, lose credits, not financial advice)
  - Moderation policy
  - Dispute resolution
- **Privacy Policy**:
  - What data we collect (email, IP, usage)
  - How it's used (authentication, analytics, moderation)
  - Third parties (Google OAuth, Cloudinary, Sentry)
  - User rights (GDPR: export, delete)

**MVP Approach**:
- Use template from [Termly](https://termly.io/) or [Iubenda](https://www.iubenda.com/)
- Customize for platform specifics
- Require checkbox on signup: "I agree to Terms and Privacy Policy"
- Link in footer of every page

---

### 5. Content Moderation Policy

**Why**: Platforms can be liable for illegal content (CSAM, terrorism, etc.).

**Policy** (see PRODUCT_SPEC.md for full details):
- ✅ AI pre-screening (OpenAI Moderation API)
- ✅ User reporting system
- ✅ Human moderator review queue
- ✅ Clear content policy (no illegal, violent, hateful content)
- ✅ Appeals process
- ✅ Compliance with DMCA (copyright takedowns)

**Legal Shield**:
- ✅ Section 230 (USA): Platforms not liable for user content if moderate in good faith
- ✅ E-Commerce Directive (EU): Similar protections for intermediaries
- ❌ Consult lawyer for specific jurisdiction compliance

---

### 6. Anti-Money Laundering (AML) / Know Your Customer (KYC)

**Risk**: Platform used for money laundering (if real money involved).

**MVP Status**: ✅ **Not Applicable** (no real money, credits only)

**Post-MVP** (if adding credit purchases):
- ❌ Require KYC for purchases >$1000
- ❌ Use Stripe or Coinbase (they handle KYC)
- ❌ Report suspicious activity (>$10k transactions)
- ❌ Consult AML lawyer before launching real-money features

---

## INCIDENT RESPONSE

### 1. Security Breach

**If user data leaked**:
1. Immediately revoke all active sessions (invalidate JWTs)
2. Force password reset for all users
3. Notify affected users within 72 hours (GDPR requirement)
4. Investigate root cause, patch vulnerability
5. Publish transparency report

**If admin account compromised**:
1. Disable admin account
2. Review admin action logs for unauthorized changes
3. Revert unauthorized changes (restore from backup if needed)
4. Enable 2FA for all admins

---

### 2. Abuse/Spam Attack

**If bot network floods platform**:
1. Temporarily increase rate limits (stricter)
2. Require CAPTCHA for all signups/posts
3. Ban IP ranges of attackers
4. Review and ban fake accounts
5. Implement device fingerprinting

---

### 3. Legal Demand

**If receive subpoena/court order**:
1. Consult lawyer immediately
2. Preserve requested data (do not delete)
3. Verify legitimacy of request
4. Respond within required timeframe
5. Notify user if legally allowed

---

## SECURE DEFAULTS CHECKLIST

- [x] Passwords hashed with bcrypt (cost 12)
- [x] JWTs with short expiry (1 hour)
- [x] HTTPOnly cookies for refresh tokens
- [x] CORS configured (whitelist origins)
- [x] Rate limiting on all endpoints
- [x] Input validation (Pydantic models)
- [x] SQL injection protection (ORM)
- [x] XSS protection (sanitize inputs, escape outputs)
- [x] HTTPS enforced (production)
- [x] Secrets in environment variables
- [x] Admin actions logged
- [x] Content moderation (AI + manual)
- [x] User reporting system
- [x] Terms of Service & Privacy Policy
- [x] Age gate (18+)
- [ ] Post-MVP: 2FA for admins
- [ ] Post-MVP: GDPR compliance (data export/deletion)
- [ ] Post-MVP: Geo-blocking (if needed)

---

## PRODUCTION HARDENING (Post-MVP)

1. **Web Application Firewall (WAF)**:
   - Cloudflare WAF (blocks common attacks)
   - Rules for SQL injection, XSS, DDoS

2. **Database Security**:
   - Enable SSL for DB connections
   - Restrict DB access to backend IPs only
   - Regular backups (daily, encrypted)
   - Read replicas for analytics queries

3. **API Security**:
   - API versioning (/api/v1/...)
   - Request signing (HMAC) for critical endpoints
   - Webhook signature verification

4. **Monitoring**:
   - Real-time alerts for:
     - High error rates (>5% 5xx)
     - Unusual traffic spikes
     - Failed login attempts (>100/min)
     - Admin actions
   - Log aggregation (Sentry, Datadog)

5. **Penetration Testing**:
   - Hire security firm to test platform
   - Bug bounty program (HackerOne)
   - Regular vulnerability scans

---

## NEXT STEPS

1. Implement all ✅ items from checklist
2. Draft Terms of Service & Privacy Policy
3. Setup Sentry for error monitoring
4. Test rate limiting under load
5. Consult lawyer re: securities law (before launch)
6. Proceed to codebase generation

---

**Document Version**: 1.0  
**Last Updated**: Jan 2026  
**Status**: APPROVED - Security measures defined
