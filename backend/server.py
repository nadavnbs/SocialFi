"""
Main FastAPI server for SocialFi Multi-Network Ingestion Platform.
Production-ready with security hardening, rate limiting, and atomic operations.
"""
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone
import logging
import uuid
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from bson import ObjectId
from bson.errors import InvalidId

from database import get_db, init_db
from models import NetworkSource, PostStatus, UnifiedPost, PasteURLRequest
from connectors import connector_registry
from amm import calculate_buy_cost, calculate_sell_revenue, distribute_fees, get_price
from auth import create_access_token, get_current_user
from signature_verification import SignatureVerifier
from siwe import create_auth_message, validate_siwe_fields
from security import get_security_config
from rate_limit import limiter, setup_rate_limiting, RATE_LIMITS

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize security config (will fail fast if misconfigured)
security_config = get_security_config()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="SocialFi Multi-Network Ingestion API",
    version="1.0.0",
    docs_url="/api/docs" if security_config.env != "production" else None,
    redoc_url="/api/redoc" if security_config.env != "production" else None,
)
api_router = APIRouter(prefix="/api")

# Setup CORS with validated config
cors_config = security_config.get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Setup rate limiting
setup_rate_limiting(app)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if security_config.env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)


# ============== HELPERS ==============

def validate_object_id(id_str: str, field_name: str = "id") -> ObjectId:
    """Validate and convert string to ObjectId."""
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} format"
        )


def get_domain_from_request(request: Request) -> str:
    """Extract domain from request for SIWE."""
    origin = request.headers.get('origin', '')
    if origin:
        parsed = urlparse(origin)
        return parsed.netloc or parsed.path
    host = request.headers.get('host', 'localhost')
    return host.split(':')[0]


# ============== REQUEST MODELS ==============

class WalletChallengeRequest(BaseModel):
    wallet_address: str = Field(min_length=26, max_length=200)
    chain_type: str
    
    @field_validator('chain_type')
    @classmethod
    def validate_chain(cls, v):
        allowed = {'ethereum', 'base', 'polygon', 'bnb', 'solana'}
        if v.lower() not in allowed:
            raise ValueError(f"chain_type must be one of: {', '.join(allowed)}")
        return v.lower()
    
    @field_validator('wallet_address')
    @classmethod
    def validate_address(cls, v):
        # Basic validation - more thorough check happens during signature verification
        v = v.strip()
        if v.startswith('0x'):
            if len(v) != 42:
                raise ValueError("Invalid EVM address length")
        return v


class SignatureVerifyRequest(BaseModel):
    wallet_address: str
    nonce: str = Field(min_length=10)
    signature: str = Field(min_length=64)
    chain_type: str
    
    @field_validator('chain_type')
    @classmethod
    def validate_chain(cls, v):
        allowed = {'ethereum', 'base', 'polygon', 'bnb', 'solana'}
        if v.lower() not in allowed:
            raise ValueError(f"chain_type must be one of: {', '.join(allowed)}")
        return v.lower()


class TradeRequest(BaseModel):
    market_id: str = Field(min_length=24, max_length=24)
    shares: float = Field(gt=0, le=10000)
    idempotency_key: Optional[str] = Field(default=None, min_length=16, max_length=64)
    
    @field_validator('market_id')
    @classmethod
    def validate_market_id(cls, v):
        try:
            ObjectId(v)
        except:
            raise ValueError("Invalid market_id format")
        return v


# ============== AUTH ENDPOINTS (SIWE) ==============

@api_router.post("/auth/challenge")
@limiter.limit(RATE_LIMITS['auth_challenge'])
async def get_challenge(
    request: Request,
    data: WalletChallengeRequest,
    db=Depends(get_db)
):
    """
    Get a SIWE challenge message to sign with wallet.
    Implements EIP-4361 for EVM chains, structured message for Solana.
    """
    domain = get_domain_from_request(request)
    uri = str(request.url).split('/api')[0]
    
    # Create SIWE message
    message, message_data = create_auth_message(
        domain=domain,
        uri=uri,
        address=data.wallet_address,
        chain_type=data.chain_type
    )
    
    # Store challenge with expiration
    challenge_doc = {
        **message_data,
        "wallet_address": data.wallet_address.lower(),
        "chain_type": data.chain_type,
        "created_at": datetime.now(timezone.utc),
        "used": False
    }
    
    await db.challenges.insert_one(challenge_doc)
    
    return {
        "message": message,
        "nonce": message_data['nonce'],
        "expires_at": message_data['expiration_time'].isoformat()
    }


@api_router.post("/auth/verify")
@limiter.limit(RATE_LIMITS['auth_verify'])
async def verify_signature(
    request: Request,
    data: SignatureVerifyRequest,
    db=Depends(get_db)
):
    """
    Verify wallet signature and issue JWT.
    Validates SIWE message fields and nonce for replay protection.
    """
    # Find unused challenge by nonce
    challenge_doc = await db.challenges.find_one({
        "wallet_address": data.wallet_address.lower(),
        "nonce": data.nonce,
        "used": False,
        "expiration_time": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not challenge_doc:
        raise HTTPException(
            status_code=401,
            detail="Challenge not found, expired, or already used"
        )
    
    # Validate SIWE fields
    is_valid, error_msg = validate_siwe_fields(
        challenge_doc,
        data.wallet_address,
        data.nonce
    )
    if not is_valid:
        raise HTTPException(status_code=401, detail=error_msg)
    
    # Verify cryptographic signature
    stored_message = challenge_doc.get('message', '')
    verifier = SignatureVerifier()
    signature_valid = verifier.verify_signature(
        stored_message,
        data.signature,
        data.wallet_address,
        data.chain_type
    )
    
    if not signature_valid:
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Mark challenge as used (atomic update)
    result = await db.challenges.update_one(
        {"_id": challenge_doc["_id"], "used": False},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}}
    )
    
    if result.modified_count == 0:
        # Challenge was used by concurrent request
        raise HTTPException(status_code=401, detail="Challenge already used")
    
    # Get or create user
    user = await db.users.find_one({"wallet_address": data.wallet_address.lower()})
    
    if not user:
        user = {
            "wallet_address": data.wallet_address.lower(),
            "chain_type": data.chain_type,
            "balance_credits": 1000.0,
            "level": 1,
            "xp": 0,
            "reputation": 0.0,
            "is_admin": False,
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        }
        result = await db.users.insert_one(user)
        user["_id"] = result.inserted_id
        logger.info(f"New user created: {data.wallet_address[:10]}...")
    else:
        await db.users.update_one(
            {"wallet_address": data.wallet_address.lower()},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
    
    access_token = create_access_token(data.wallet_address.lower())
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "wallet_address": data.wallet_address.lower(),
            "balance_credits": user.get("balance_credits", 1000),
            "level": user.get("level", 1),
            "xp": user.get("xp", 0),
            "reputation": user.get("reputation", 0)
        }
    }


@api_router.get("/auth/me")
@limiter.limit(RATE_LIMITS['portfolio'])
async def get_me(
    request: Request,
    wallet_address: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Get current user profile."""
    user = await db.users.find_one({"wallet_address": wallet_address.lower()})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "wallet_address": user["wallet_address"],
        "balance_credits": user["balance_credits"],
        "level": user.get("level", 1),
        "xp": user.get("xp", 0),
        "reputation": user.get("reputation", 0),
        "is_admin": user.get("is_admin", False),
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None
    }


# ============== FEED ENDPOINTS ==============

VALID_NETWORKS = {ns.value for ns in NetworkSource}
VALID_SORT_OPTIONS = {'trending', 'new', 'price', 'volume'}


@api_router.get("/feed")
@limiter.limit(RATE_LIMITS['feed_read'])
async def get_feed(
    request: Request,
    networks: str = Query(default="", description="Comma-separated network filters"),
    sort: str = Query(default="trending"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_db)
):
    """
    Get unified feed from all networks with filtering.
    Uses aggregation pipeline to avoid N+1 queries.
    """
    # Validate and parse network filter
    network_filter = []
    if networks:
        for n in networks.split(","):
            n = n.strip().lower()
            if n in VALID_NETWORKS:
                network_filter.append(n)
    
    # Validate sort option
    if sort not in VALID_SORT_OPTIONS:
        sort = "trending"
    
    # Build query
    match_stage = {"status": PostStatus.ACTIVE.value}
    if network_filter:
        match_stage["source_network"] = {"$in": network_filter}
    
    # Sort mapping
    sort_stage = {
        "trending": {"source_likes": -1, "source_comments": -1},
        "new": {"ingested_at": -1},
        "price": {"market_data.price_current": -1},
        "volume": {"market_data.total_volume": -1}
    }[sort]
    
    # Aggregation pipeline with $lookup to avoid N+1
    pipeline = [
        {"$match": match_stage},
        {
            "$lookup": {
                "from": "markets",
                "let": {"post_id": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$post_id", "$$post_id"]}}}
                ],
                "as": "market_data"
            }
        },
        {"$unwind": {"path": "$market_data", "preserveNullAndEmptyArrays": True}},
        {"$sort": sort_stage},
        {"$skip": offset},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "id": {"$toString": "$_id"},
                "source_network": 1,
                "source_url": 1,
                "source_id": 1,
                "author_username": 1,
                "author_display_name": 1,
                "author_avatar_url": 1,
                "content_text": 1,
                "title": 1,
                "subreddit": 1,
                "farcaster_channel": 1,
                "media_urls": 1,
                "media_type": 1,
                "source_likes": 1,
                "source_comments": 1,
                "source_shares": 1,
                "source_created_at": 1,
                "ingested_at": 1,
                "market": {
                    "$cond": {
                        "if": {"$ifNull": ["$market_data._id", False]},
                        "then": {
                            "id": {"$toString": "$market_data._id"},
                            "price_current": "$market_data.price_current",
                            "total_supply": "$market_data.total_supply",
                            "total_volume": "$market_data.total_volume",
                            "is_frozen": {"$ifNull": ["$market_data.is_frozen", False]}
                        },
                        "else": "$$REMOVE"
                    }
                }
            }
        }
    ]
    
    posts = await db.unified_posts.aggregate(pipeline).to_list(length=limit)
    
    # Convert datetime fields to strings
    for post in posts:
        for dt_field in ['source_created_at', 'ingested_at']:
            val = post.get(dt_field)
            if val and hasattr(val, 'isoformat'):
                post[dt_field] = val.isoformat()
    
    # Get total count
    total = await db.unified_posts.count_documents(match_stage)
    
    return {
        "posts": posts,
        "total": total,
        "has_more": (offset + limit) < total
    }


@api_router.post("/feed/refresh")
@limiter.limit(RATE_LIMITS['feed_refresh'])
async def refresh_feed(
    request: Request,
    background_tasks: BackgroundTasks,
    networks: str = Query(default="reddit,farcaster"),
    db=Depends(get_db)
):
    """Trigger a feed refresh from specified networks."""
    # Validate networks
    network_list = []
    for n in networks.split(","):
        n = n.strip().lower()
        if n in VALID_NETWORKS:
            network_list.append(n)
    
    if not network_list:
        network_list = ['reddit', 'farcaster']
    
    async def _do_refresh():
        """Background task to refresh feed."""
        for network_name in network_list:
            try:
                network = NetworkSource(network_name)
                connector = connector_registry.get_connector(network)
                if not connector:
                    continue
                
                posts = await connector.fetch_trending(limit=30)
                
                for post in posts:
                    try:
                        existing = await db.unified_posts.find_one({
                            "source_network": post.source_network.value,
                            "source_id": post.source_id
                        })
                        
                        if not existing:
                            post_dict = post.model_dump()
                            post_dict["source_network"] = post.source_network.value
                            post_dict["status"] = PostStatus.ACTIVE.value
                            
                            result = await db.unified_posts.insert_one(post_dict)
                            post_id = str(result.inserted_id)
                            
                            market = {
                                "post_id": post_id,
                                "total_supply": 100.0,
                                "total_volume": 0.0,
                                "price_current": get_price(100.0),
                                "fees_collected": 0.0,
                                "is_frozen": False,
                                "version": 0,
                                "created_at": datetime.now(timezone.utc)
                            }
                            await db.markets.insert_one(market)
                    except Exception as e:
                        logger.error(f"Error inserting post: {type(e).__name__}")
                
                logger.info(f"Refreshed {len(posts)} posts from {network_name}")
                
            except Exception as e:
                logger.error(f"Error refreshing {network_name}: {type(e).__name__}")
    
    background_tasks.add_task(_do_refresh)
    
    return {"message": "Feed refresh started", "networks": network_list}


@api_router.get("/feed/networks")
async def get_available_networks():
    """Get list of available networks with their status."""
    return {
        "networks": [
            {"id": "reddit", "name": "Reddit", "status": "active", "icon": "reddit"},
            {"id": "farcaster", "name": "Farcaster", "status": "active", "icon": "farcaster"},
            {"id": "x", "name": "X (Twitter)", "status": "stub", "icon": "x"},
            {"id": "instagram", "name": "Instagram", "status": "stub", "icon": "instagram"},
            {"id": "twitch", "name": "Twitch", "status": "stub", "icon": "twitch"}
        ]
    }


# ============== PASTE URL ENDPOINT ==============

@api_router.post("/posts/paste-url")
@limiter.limit(RATE_LIMITS['paste_url'])
async def paste_url(
    request: Request,
    data: PasteURLRequest,
    wallet_address: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """List a market by pasting a social media post URL."""
    url = data.url.strip()
    
    connector = connector_registry.find_connector_for_url(url)
    if not connector:
        raise HTTPException(
            status_code=400,
            detail="Unsupported URL. Supported: Reddit, Farcaster, X, Instagram, Twitch"
        )
    
    # Check if already listed
    existing = await db.unified_posts.find_one({"source_url": url})
    if existing:
        market = await db.markets.find_one({"post_id": str(existing["_id"])})
        return {
            "success": True,
            "post_id": str(existing["_id"]),
            "market_id": str(market["_id"]) if market else None,
            "network": existing["source_network"],
            "message": "Post already listed",
            "already_exists": True
        }
    
    # Fetch post data with fallback
    try:
        post = await connector.fetch_by_url(url)
    except Exception as e:
        logger.warning(f"Connector fetch failed: {type(e).__name__}")
        post = None
    
    if not post:
        post = UnifiedPost(
            source_network=connector.network,
            source_id=url.split("/")[-1] or str(uuid.uuid4())[:8],
            source_url=url,
            author_username="unknown",
            content_text=f"[Content from {connector.network.value} - preview only]",
            media_type="embed",
            ingested_at=datetime.now(timezone.utc)
        )
    
    # Save post
    post_dict = post.model_dump()
    post_dict["source_network"] = post.source_network.value
    post_dict["status"] = PostStatus.ACTIVE.value
    post_dict["listed_by"] = wallet_address
    
    result = await db.unified_posts.insert_one(post_dict)
    post_id = str(result.inserted_id)
    
    # Create market with version for optimistic locking
    market = {
        "post_id": post_id,
        "total_supply": 100.0,
        "total_volume": 0.0,
        "price_current": get_price(100.0),
        "fees_collected": 0.0,
        "is_frozen": False,
        "version": 0,
        "listed_by": wallet_address,
        "created_at": datetime.now(timezone.utc)
    }
    
    market_result = await db.markets.insert_one(market)
    market_id = str(market_result.inserted_id)
    
    # Reward user
    await db.users.update_one(
        {"wallet_address": wallet_address.lower()},
        {"$inc": {"xp": 25, "reputation": 0.1}}
    )
    
    return {
        "success": True,
        "post_id": post_id,
        "market_id": market_id,
        "network": post.source_network.value,
        "message": f"Successfully listed {post.source_network.value} post",
        "already_exists": False
    }


# ============== TRADING ENDPOINTS (ATOMIC) ==============

@api_router.post("/trades/buy")
@limiter.limit(RATE_LIMITS['trade'])
async def buy_shares(
    request: Request,
    trade: TradeRequest,
    wallet_address: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Buy shares in a post's market.
    Uses optimistic locking with version field for concurrency safety.
    """
    market_oid = validate_object_id(trade.market_id, "market_id")
    
    # Check idempotency
    if trade.idempotency_key:
        existing_trade = await db.trades.find_one({
            "idempotency_key": trade.idempotency_key,
            "wallet_address": wallet_address.lower()
        })
        if existing_trade:
            return {
                "success": True,
                "trade_type": "buy",
                "shares": existing_trade["shares"],
                "price_per_share": existing_trade["price_per_share"],
                "total_cost": existing_trade["total_cost"],
                "fee_amount": existing_trade["fee_amount"],
                "new_balance": existing_trade.get("resulting_balance", 0),
                "idempotent": True
            }
    
    # Get market with version
    market = await db.markets.find_one({"_id": market_oid})
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    if market.get("is_frozen"):
        raise HTTPException(status_code=400, detail="Market is frozen")
    
    # Get user
    user = await db.users.find_one({"wallet_address": wallet_address.lower()})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate costs
    cost_calc = calculate_buy_cost(market["total_supply"], trade.shares)
    
    if user["balance_credits"] < cost_calc["total_cost"]:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Need {cost_calc['total_cost']:.2f}, have {user['balance_credits']:.2f}"
        )
    
    fees = distribute_fees(cost_calc["fee"])
    current_version = market.get("version", 0)
    new_balance = user["balance_credits"] - cost_calc["total_cost"]
    
    # Invariant checks
    if cost_calc["new_supply"] < 0:
        raise HTTPException(status_code=400, detail="Invalid trade: would result in negative supply")
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Invalid trade: would result in negative balance")
    
    # Atomic market update with optimistic locking
    market_update = await db.markets.find_one_and_update(
        {
            "_id": market_oid,
            "version": current_version,
            "is_frozen": {"$ne": True}
        },
        {
            "$set": {
                "total_supply": cost_calc["new_supply"],
                "price_current": cost_calc["new_price"],
                "last_trade_at": datetime.now(timezone.utc)
            },
            "$inc": {
                "version": 1,
                "total_volume": cost_calc["cost_before_fee"],
                "fees_collected": cost_calc["fee"]
            }
        }
    )
    
    if not market_update:
        raise HTTPException(
            status_code=409,
            detail="Trade conflict: market was modified by another transaction. Please retry."
        )
    
    # Update user balance atomically
    user_update = await db.users.find_one_and_update(
        {
            "wallet_address": wallet_address.lower(),
            "balance_credits": {"$gte": cost_calc["total_cost"]}
        },
        {
            "$inc": {
                "balance_credits": -cost_calc["total_cost"],
                "xp": 10
            }
        }
    )
    
    if not user_update:
        # Rollback market change
        await db.markets.update_one(
            {"_id": market_oid},
            {
                "$set": {
                    "total_supply": market["total_supply"],
                    "price_current": market["price_current"]
                },
                "$inc": {
                    "version": 1,
                    "total_volume": -cost_calc["cost_before_fee"],
                    "fees_collected": -cost_calc["fee"]
                }
            }
        )
        raise HTTPException(status_code=400, detail="Insufficient balance (concurrent modification)")
    
    # Update/create position
    position_result = await db.positions.find_one_and_update(
        {
            "wallet_address": wallet_address.lower(),
            "market_id": trade.market_id
        },
        {
            "$inc": {"shares": trade.shares},
            "$setOnInsert": {
                "wallet_address": wallet_address.lower(),
                "market_id": trade.market_id,
                "created_at": datetime.now(timezone.utc)
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        upsert=True
    )
    
    # Update average price for position
    if position_result:
        old_shares = position_result.get("shares", 0)
        old_avg = position_result.get("avg_price", 0)
        new_shares = old_shares + trade.shares
        new_avg = ((old_shares * old_avg) + cost_calc["cost_before_fee"]) / new_shares if new_shares > 0 else cost_calc["avg_price"]
        await db.positions.update_one(
            {"wallet_address": wallet_address.lower(), "market_id": trade.market_id},
            {"$set": {"avg_price": new_avg}}
        )
    else:
        await db.positions.update_one(
            {"wallet_address": wallet_address.lower(), "market_id": trade.market_id},
            {"$set": {"avg_price": cost_calc["avg_price"]}}
        )
    
    # Record trade
    trade_record = {
        "wallet_address": wallet_address.lower(),
        "market_id": trade.market_id,
        "trade_type": "buy",
        "shares": trade.shares,
        "price_per_share": cost_calc["avg_price"],
        "total_cost": cost_calc["total_cost"],
        "fee_amount": cost_calc["fee"],
        "resulting_balance": new_balance,
        "market_version": current_version + 1,
        "created_at": datetime.now(timezone.utc)
    }
    if trade.idempotency_key:
        trade_record["idempotency_key"] = trade.idempotency_key
    
    await db.trades.insert_one(trade_record)
    
    return {
        "success": True,
        "trade_type": "buy",
        "shares": trade.shares,
        "price_per_share": round(cost_calc["avg_price"], 6),
        "total_cost": round(cost_calc["total_cost"], 2),
        "fee_amount": round(cost_calc["fee"], 4),
        "new_balance": round(new_balance, 2)
    }


@api_router.post("/trades/sell")
@limiter.limit(RATE_LIMITS['trade'])
async def sell_shares(
    request: Request,
    trade: TradeRequest,
    wallet_address: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Sell shares in a post's market.
    Uses optimistic locking with version field for concurrency safety.
    """
    market_oid = validate_object_id(trade.market_id, "market_id")
    
    # Check idempotency
    if trade.idempotency_key:
        existing_trade = await db.trades.find_one({
            "idempotency_key": trade.idempotency_key,
            "wallet_address": wallet_address.lower()
        })
        if existing_trade:
            return {
                "success": True,
                "trade_type": "sell",
                "shares": existing_trade["shares"],
                "price_per_share": existing_trade["price_per_share"],
                "total_revenue": existing_trade.get("total_revenue", 0),
                "fee_amount": existing_trade["fee_amount"],
                "new_balance": existing_trade.get("resulting_balance", 0),
                "idempotent": True
            }
    
    # Get market
    market = await db.markets.find_one({"_id": market_oid})
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    if market.get("is_frozen"):
        raise HTTPException(status_code=400, detail="Market is frozen")
    
    # Check position
    position = await db.positions.find_one({
        "wallet_address": wallet_address.lower(),
        "market_id": trade.market_id
    })
    
    if not position or position.get("shares", 0) < trade.shares:
        available = position.get("shares", 0) if position else 0
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient shares. Have {available}, trying to sell {trade.shares}"
        )
    
    # Calculate revenue
    revenue_calc = calculate_sell_revenue(market["total_supply"], trade.shares)
    fees = distribute_fees(revenue_calc["fee"])
    current_version = market.get("version", 0)
    
    # Invariant checks
    if revenue_calc["new_supply"] < 0:
        raise HTTPException(status_code=400, detail="Invalid trade: would result in negative supply")
    
    # Get user for balance calculation
    user = await db.users.find_one({"wallet_address": wallet_address.lower()})
    new_balance = user["balance_credits"] + revenue_calc["net_revenue"]
    
    # Atomic market update with optimistic locking
    market_update = await db.markets.find_one_and_update(
        {
            "_id": market_oid,
            "version": current_version,
            "is_frozen": {"$ne": True},
            "total_supply": {"$gte": trade.shares}
        },
        {
            "$set": {
                "total_supply": revenue_calc["new_supply"],
                "price_current": revenue_calc["new_price"],
                "last_trade_at": datetime.now(timezone.utc)
            },
            "$inc": {
                "version": 1,
                "total_volume": revenue_calc["revenue_before_fee"],
                "fees_collected": revenue_calc["fee"]
            }
        }
    )
    
    if not market_update:
        raise HTTPException(
            status_code=409,
            detail="Trade conflict: market was modified by another transaction. Please retry."
        )
    
    # Update user balance atomically
    await db.users.update_one(
        {"wallet_address": wallet_address.lower()},
        {
            "$inc": {
                "balance_credits": revenue_calc["net_revenue"],
                "xp": 10
            }
        }
    )
    
    # Update position atomically
    new_shares = position["shares"] - trade.shares
    if new_shares > 0:
        await db.positions.update_one(
            {"_id": position["_id"]},
            {
                "$inc": {"shares": -trade.shares},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
    else:
        await db.positions.delete_one({"_id": position["_id"]})
    
    # Record trade
    trade_record = {
        "wallet_address": wallet_address.lower(),
        "market_id": trade.market_id,
        "trade_type": "sell",
        "shares": trade.shares,
        "price_per_share": revenue_calc["avg_price"],
        "total_revenue": revenue_calc["net_revenue"],
        "fee_amount": revenue_calc["fee"],
        "resulting_balance": new_balance,
        "market_version": current_version + 1,
        "created_at": datetime.now(timezone.utc)
    }
    if trade.idempotency_key:
        trade_record["idempotency_key"] = trade.idempotency_key
    
    await db.trades.insert_one(trade_record)
    
    return {
        "success": True,
        "trade_type": "sell",
        "shares": trade.shares,
        "price_per_share": round(revenue_calc["avg_price"], 6),
        "total_revenue": round(revenue_calc["net_revenue"], 2),
        "fee_amount": round(revenue_calc["fee"], 4),
        "new_balance": round(new_balance, 2)
    }


# ============== PORTFOLIO ENDPOINTS ==============

@api_router.get("/portfolio")
@limiter.limit(RATE_LIMITS['portfolio'])
async def get_portfolio(
    request: Request,
    wallet_address: str = Depends(get_current_user),
    db=Depends(get_db)
):
    """Get user's portfolio with all positions using aggregation."""
    # Use aggregation to avoid N+1
    pipeline = [
        {"$match": {"wallet_address": wallet_address.lower(), "shares": {"$gt": 0}}},
        {
            "$lookup": {
                "from": "markets",
                "let": {"market_id": "$market_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": [{"$toString": "$_id"}, "$$market_id"]}}}
                ],
                "as": "market"
            }
        },
        {"$unwind": {"path": "$market", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "unified_posts",
                "let": {"post_id": "$market.post_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": [{"$toString": "$_id"}, "$$post_id"]}}}
                ],
                "as": "post"
            }
        },
        {"$unwind": {"path": "$post", "preserveNullAndEmptyArrays": True}}
    ]
    
    positions = []
    total_value = 0.0
    
    async for doc in db.positions.aggregate(pipeline):
        market = doc.get("market")
        post = doc.get("post")
        
        if not market:
            continue
        
        current_value = doc["shares"] * market["price_current"]
        cost_basis = doc["shares"] * doc.get("avg_price", 0)
        pnl = current_value - cost_basis
        pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        positions.append({
            "market_id": doc["market_id"],
            "shares": doc["shares"],
            "avg_price": round(doc.get("avg_price", 0), 6),
            "current_price": round(market["price_current"], 6),
            "current_value": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "post": {
                "id": str(post["_id"]) if post else None,
                "source_network": post.get("source_network") if post else None,
                "title": post.get("title") if post else None,
                "content_text": post.get("content_text", "")[:100] if post else None,
                "author_username": post.get("author_username") if post else None
            } if post else None
        })
        
        total_value += current_value
    
    user = await db.users.find_one({"wallet_address": wallet_address.lower()})
    cash_balance = user["balance_credits"] if user else 0
    
    return {
        "positions": positions,
        "total_value": round(total_value, 2),
        "cash_balance": round(cash_balance, 2),
        "total_portfolio": round(total_value + cash_balance, 2)
    }


# ============== LEADERBOARD ==============

@api_router.get("/leaderboard")
@limiter.limit(RATE_LIMITS['leaderboard'])
async def get_leaderboard(
    request: Request,
    sort_by: str = Query(default="xp"),
    limit: int = Query(default=50, ge=1, le=100),
    db=Depends(get_db)
):
    """Get global leaderboard."""
    sort_field = {
        "xp": "xp",
        "reputation": "reputation",
        "balance": "balance_credits"
    }.get(sort_by, "xp")
    
    users = []
    cursor = db.users.find({}).sort(sort_field, -1).limit(limit)
    
    rank = 1
    async for user in cursor:
        wallet = user.get("wallet_address", "")
        users.append({
            "rank": rank,
            "wallet_address": f"{wallet[:6]}...{wallet[-4:]}" if len(wallet) > 10 else wallet,
            "level": user.get("level", 1),
            "xp": user.get("xp", 0),
            "reputation": round(user.get("reputation", 0), 2),
            "balance_credits": round(user.get("balance_credits", 0), 2)
        })
        rank += 1
    
    return {"leaderboard": users}


# ============== HEALTH CHECK ==============

@api_router.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "SocialFi Multi-Network Ingestion API",
        "version": "1.0.0",
        "status": "operational"
    }


@api_router.get("/health")
async def health_check(db=Depends(get_db)):
    """Health check endpoint."""
    try:
        await db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": type(e).__name__
        }


# Include router
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    await init_db()
    logger.info(f"✅ SocialFi API started (env={security_config.env})")
