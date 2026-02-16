"""
Main FastAPI server for SocialFi Multi-Network Ingestion Platform
"""
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import os
import logging
import re
from pathlib import Path
from dotenv import load_dotenv
from bson import ObjectId

from database import get_db, init_db
from models import (
    NetworkSource, PostStatus,
    UnifiedPost, TradeRequest, PasteURLRequest, FeedFilter
)
from connectors import connector_registry
from amm import calculate_buy_cost, calculate_sell_revenue, distribute_fees, get_price
from auth import create_access_token, get_current_user_optional, generate_challenge
from signature_verification import SignatureVerifier

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title="SocialFi Multi-Network Ingestion API")
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============== AUTH ENDPOINTS (WALLET-BASED) ==============

class WalletChallengeRequest(BaseModel):
    wallet_address: str = Field(min_length=26, max_length=200)
    chain_type: str = Field(pattern="^(ethereum|base|polygon|bnb|solana)$")


class SignatureVerifyRequest(BaseModel):
    wallet_address: str
    challenge: str
    signature: str
    chain_type: str


@api_router.post("/auth/challenge")
async def get_challenge(request: WalletChallengeRequest, db=Depends(get_db)):
    """Get a challenge message to sign with wallet"""
    challenge = generate_challenge()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    await db.challenges.insert_one({
        "wallet_address": request.wallet_address.lower(),
        "chain_type": request.chain_type,
        "challenge": challenge,
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "used": False
    })
    
    return {
        "challenge": challenge,
        "message": f"Sign this message to authenticate:\n\n{challenge}",
        "expires_at": expires_at
    }


@api_router.post("/auth/verify")
async def verify_signature(request: SignatureVerifyRequest, db=Depends(get_db)):
    """Verify wallet signature and issue JWT"""
    logger.info(f"Verify request for wallet: {request.wallet_address}")
    
    challenge_doc = await db.challenges.find_one({
        "wallet_address": request.wallet_address.lower(),
        "challenge": request.challenge,
        "used": False,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not challenge_doc:
        raise HTTPException(status_code=401, detail="Challenge expired or already used")
    
    verifier = SignatureVerifier()
    is_valid = verifier.verify_signature(
        request.challenge,
        request.signature,
        request.wallet_address,
        request.chain_type
    )
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    await db.challenges.update_one(
        {"_id": challenge_doc["_id"]},
        {"$set": {"used": True}}
    )
    
    user = await db.users.find_one({"wallet_address": request.wallet_address.lower()})
    
    if not user:
        user = {
            "wallet_address": request.wallet_address.lower(),
            "chain_type": request.chain_type,
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
        logger.info(f"New user created: {request.wallet_address}")
    else:
        await db.users.update_one(
            {"wallet_address": request.wallet_address.lower()},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
    
    access_token = create_access_token(request.wallet_address.lower())
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "wallet_address": request.wallet_address.lower(),
            "balance_credits": user.get("balance_credits", 1000),
            "level": user.get("level", 1),
            "xp": user.get("xp", 0),
            "reputation": user.get("reputation", 0)
        }
    }


@api_router.get("/auth/me")
async def get_me(wallet_address: str = Depends(get_current_user_optional), db=Depends(get_db)):
    """Get current user profile"""
    if not wallet_address:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
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

@api_router.get("/feed")
async def get_feed(
    networks: str = Query(default="", description="Comma-separated network filters: reddit,farcaster,x,instagram,twitch"),
    sort: str = Query(default="trending", description="Sort by: trending, new, price, volume"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    db=Depends(get_db)
):
    """
    Get unified feed from all networks with filtering.
    Networks can be filtered by comma-separated list.
    """
    # Parse network filters
    network_filter = []
    if networks:
        for n in networks.split(","):
            n = n.strip().lower()
            if n in [ns.value for ns in NetworkSource]:
                network_filter.append(n)
    
    # Build query
    query = {"status": PostStatus.ACTIVE.value}
    if network_filter:
        query["source_network"] = {"$in": network_filter}
    
    # Sort mapping
    sort_map = {
        "trending": [("source_likes", -1), ("source_comments", -1)],
        "new": [("ingested_at", -1)],
        "price": [("market.price_current", -1)],
        "volume": [("market.total_volume", -1)]
    }
    sort_order = sort_map.get(sort, sort_map["trending"])
    
    # Fetch posts with market data
    posts = []
    cursor = db.unified_posts.find(query).sort(sort_order).skip(offset).limit(limit)
    
    async for post in cursor:
        post_id = str(post["_id"])
        
        # Get market for this post
        market = await db.markets.find_one({"post_id": post_id})
        
        post_data = {
            "id": post_id,
            "source_network": post["source_network"],
            "source_url": post.get("source_url"),
            "author_username": post.get("author_username"),
            "author_display_name": post.get("author_display_name"),
            "author_avatar_url": post.get("author_avatar_url"),
            "content_text": post.get("content_text"),
            "title": post.get("title"),
            "subreddit": post.get("subreddit"),
            "farcaster_channel": post.get("farcaster_channel"),
            "media_urls": post.get("media_urls", []),
            "media_type": post.get("media_type"),
            "source_likes": post.get("source_likes", 0),
            "source_comments": post.get("source_comments", 0),
            "source_shares": post.get("source_shares", 0),
            "source_created_at": post.get("source_created_at").isoformat() if post.get("source_created_at") else None,
            "ingested_at": post.get("ingested_at").isoformat() if post.get("ingested_at") else None,
        }
        
        if market:
            post_data["market"] = {
                "id": str(market["_id"]),
                "price_current": market["price_current"],
                "total_supply": market["total_supply"],
                "total_volume": market["total_volume"],
                "is_frozen": market.get("is_frozen", False)
            }
        
        posts.append(post_data)
    
    # Get total count
    total = await db.unified_posts.count_documents(query)
    
    return {
        "posts": posts,
        "total": total,
        "has_more": (offset + limit) < total
    }


@api_router.post("/feed/refresh")
async def refresh_feed(
    background_tasks: BackgroundTasks,
    networks: str = Query(default="reddit,farcaster"),
    db=Depends(get_db)
):
    """
    Trigger a feed refresh from specified networks.
    This runs in background and returns immediately.
    """
    network_list = [n.strip() for n in networks.split(",") if n.strip()]
    
    async def _do_refresh():
        try:
            for network_name in network_list:
                try:
                    network = NetworkSource(network_name)
                    connector = connector_registry.get_connector(network)
                    if not connector:
                        continue
                    
                    posts = await connector.fetch_trending(limit=30)
                    
                    for post in posts:
                        # Check if already exists
                        existing = await db.unified_posts.find_one({
                            "source_network": post.source_network.value,
                            "source_id": post.source_id
                        })
                        
                        if not existing:
                            # Insert new post
                            post_dict = post.model_dump()
                            post_dict["source_network"] = post.source_network.value
                            post_dict["status"] = PostStatus.ACTIVE.value
                            
                            result = await db.unified_posts.insert_one(post_dict)
                            post_id = str(result.inserted_id)
                            
                            # Create market for post
                            market = {
                                "post_id": post_id,
                                "total_supply": 100.0,
                                "total_volume": 0.0,
                                "price_current": get_price(100.0),
                                "fees_collected": 0.0,
                                "creator_earnings": 0.0,
                                "liquidity_pool": 0.0,
                                "is_frozen": False,
                                "created_at": datetime.now(timezone.utc)
                            }
                            await db.markets.insert_one(market)
                            
                    logger.info(f"Refreshed {len(posts)} posts from {network_name}")
                    
                except Exception as e:
                    logger.error(f"Error refreshing {network_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Feed refresh error: {e}")
    
    background_tasks.add_task(_do_refresh)
    
    return {"message": "Feed refresh started", "networks": network_list}


@api_router.get("/feed/networks")
async def get_available_networks():
    """Get list of available networks with their status"""
    return {
        "networks": [
            {"id": "reddit", "name": "Reddit", "status": "active", "icon": "🔴"},
            {"id": "farcaster", "name": "Farcaster", "status": "active", "icon": "🟣"},
            {"id": "x", "name": "X (Twitter)", "status": "stub", "icon": "⚫"},
            {"id": "instagram", "name": "Instagram", "status": "stub", "icon": "📷"},
            {"id": "twitch", "name": "Twitch", "status": "stub", "icon": "🟣"}
        ]
    }


# ============== PASTE URL ENDPOINT ==============

@api_router.post("/posts/paste-url")
async def paste_url(
    data: PasteURLRequest,
    wallet_address: str = Depends(get_current_user_optional),
    db=Depends(get_db)
):
    """
    List a market by pasting a social media post URL.
    Works for any supported network. Falls back to embed preview if full fetch fails.
    """
    if not wallet_address:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    url = data.url.strip()
    
    # Find appropriate connector
    connector = connector_registry.find_connector_for_url(url)
    if not connector:
        raise HTTPException(status_code=400, detail="Unsupported URL. Supported: Reddit, Farcaster, X, Instagram, Twitch")
    
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
    
    # Fetch post data
    try:
        post = await connector.fetch_by_url(url)
    except Exception as e:
        logger.error(f"Connector fetch error: {e}")
        post = None
    
    # Fallback: create minimal post from URL
    if not post:
        post = UnifiedPost(
            source_network=connector.network,
            source_id=url.split("/")[-1] or "unknown",
            source_url=url,
            author_username="unknown",
            content_text=f"[Content from {connector.network.value}]",
            media_type="embed",
            ingested_at=datetime.now(timezone.utc)
        )
    
    # Save to database
    post_dict = post.model_dump()
    post_dict["source_network"] = post.source_network.value
    post_dict["status"] = PostStatus.ACTIVE.value
    post_dict["listed_by"] = wallet_address
    
    result = await db.unified_posts.insert_one(post_dict)
    post_id = str(result.inserted_id)
    
    # Create market
    market = {
        "post_id": post_id,
        "total_supply": 100.0,
        "total_volume": 0.0,
        "price_current": get_price(100.0),
        "fees_collected": 0.0,
        "creator_earnings": 0.0,
        "liquidity_pool": 0.0,
        "is_frozen": False,
        "listed_by": wallet_address,
        "created_at": datetime.now(timezone.utc)
    }
    
    market_result = await db.markets.insert_one(market)
    market_id = str(market_result.inserted_id)
    
    # Reward user for listing
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


# ============== TRADING ENDPOINTS ==============

@api_router.post("/trades/buy")
async def buy_shares(
    trade: TradeRequest,
    wallet_address: str = Depends(get_current_user_optional),
    db=Depends(get_db)
):
    """Buy shares in a post's market"""
    if not wallet_address:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    market = await db.markets.find_one({"_id": ObjectId(trade.market_id)})
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    if market.get("is_frozen"):
        raise HTTPException(status_code=400, detail="Market is frozen")
    
    user = await db.users.find_one({"wallet_address": wallet_address.lower()})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    cost_calc = calculate_buy_cost(market["total_supply"], trade.shares)
    
    if user["balance_credits"] < cost_calc["total_cost"]:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Need {cost_calc['total_cost']:.2f} credits")
    
    fees = distribute_fees(cost_calc["fee"])
    
    # Update market
    await db.markets.update_one(
        {"_id": ObjectId(trade.market_id)},
        {
            "$set": {
                "total_supply": cost_calc["new_supply"],
                "price_current": cost_calc["new_price"],
                "last_trade_at": datetime.now(timezone.utc)
            },
            "$inc": {
                "total_volume": cost_calc["cost_before_fee"],
                "fees_collected": cost_calc["fee"],
                "liquidity_pool": fees["liquidity_fee"]
            }
        }
    )
    
    # Update user balance
    new_balance = user["balance_credits"] - cost_calc["total_cost"]
    await db.users.update_one(
        {"wallet_address": wallet_address.lower()},
        {
            "$set": {"balance_credits": new_balance},
            "$inc": {"xp": 10}
        }
    )
    
    # Update/create position
    position = await db.positions.find_one({
        "wallet_address": wallet_address.lower(),
        "market_id": trade.market_id
    })
    
    if position:
        new_shares = position["shares"] + trade.shares
        new_avg_price = (position["shares"] * position["avg_price"] + cost_calc["cost_before_fee"]) / new_shares
        await db.positions.update_one(
            {"_id": position["_id"]},
            {"$set": {"shares": new_shares, "avg_price": new_avg_price}}
        )
    else:
        await db.positions.insert_one({
            "wallet_address": wallet_address.lower(),
            "market_id": trade.market_id,
            "shares": trade.shares,
            "avg_price": cost_calc["avg_price"],
            "created_at": datetime.now(timezone.utc)
        })
    
    # Record trade
    await db.trades.insert_one({
        "wallet_address": wallet_address.lower(),
        "market_id": trade.market_id,
        "trade_type": "buy",
        "shares": trade.shares,
        "price_per_share": cost_calc["avg_price"],
        "total_cost": cost_calc["total_cost"],
        "fee_amount": cost_calc["fee"],
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "trade_type": "buy",
        "shares": trade.shares,
        "price_per_share": round(cost_calc["avg_price"], 4),
        "total_cost": round(cost_calc["total_cost"], 2),
        "fee_amount": round(cost_calc["fee"], 2),
        "new_balance": round(new_balance, 2)
    }


@api_router.post("/trades/sell")
async def sell_shares(
    trade: TradeRequest,
    wallet_address: str = Depends(get_current_user_optional),
    db=Depends(get_db)
):
    """Sell shares in a post's market"""
    if not wallet_address:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    market = await db.markets.find_one({"_id": ObjectId(trade.market_id)})
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    if market.get("is_frozen"):
        raise HTTPException(status_code=400, detail="Market is frozen")
    
    position = await db.positions.find_one({
        "wallet_address": wallet_address.lower(),
        "market_id": trade.market_id
    })
    
    if not position or position["shares"] < trade.shares:
        raise HTTPException(status_code=400, detail="Insufficient shares")
    
    revenue_calc = calculate_sell_revenue(market["total_supply"], trade.shares)
    fees = distribute_fees(revenue_calc["fee"])
    
    # Update market
    await db.markets.update_one(
        {"_id": ObjectId(trade.market_id)},
        {
            "$set": {
                "total_supply": revenue_calc["new_supply"],
                "price_current": revenue_calc["new_price"],
                "last_trade_at": datetime.now(timezone.utc)
            },
            "$inc": {
                "total_volume": revenue_calc["revenue_before_fee"],
                "fees_collected": revenue_calc["fee"],
                "liquidity_pool": fees["liquidity_fee"]
            }
        }
    )
    
    # Update user balance
    user = await db.users.find_one({"wallet_address": wallet_address.lower()})
    new_balance = user["balance_credits"] + revenue_calc["net_revenue"]
    await db.users.update_one(
        {"wallet_address": wallet_address.lower()},
        {
            "$set": {"balance_credits": new_balance},
            "$inc": {"xp": 10}
        }
    )
    
    # Update position
    new_shares = position["shares"] - trade.shares
    if new_shares > 0:
        await db.positions.update_one(
            {"_id": position["_id"]},
            {"$set": {"shares": new_shares}}
        )
    else:
        await db.positions.delete_one({"_id": position["_id"]})
    
    # Record trade
    await db.trades.insert_one({
        "wallet_address": wallet_address.lower(),
        "market_id": trade.market_id,
        "trade_type": "sell",
        "shares": trade.shares,
        "price_per_share": revenue_calc["avg_price"],
        "total_revenue": revenue_calc["net_revenue"],
        "fee_amount": revenue_calc["fee"],
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "trade_type": "sell",
        "shares": trade.shares,
        "price_per_share": round(revenue_calc["avg_price"], 4),
        "total_revenue": round(revenue_calc["net_revenue"], 2),
        "fee_amount": round(revenue_calc["fee"], 2),
        "new_balance": round(new_balance, 2)
    }


# ============== PORTFOLIO ENDPOINTS ==============

@api_router.get("/portfolio")
async def get_portfolio(
    wallet_address: str = Depends(get_current_user_optional),
    db=Depends(get_db)
):
    """Get user's portfolio with all positions"""
    if not wallet_address:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    positions = []
    total_value = 0.0
    
    async for pos in db.positions.find({"wallet_address": wallet_address.lower(), "shares": {"$gt": 0}}):
        market = await db.markets.find_one({"_id": ObjectId(pos["market_id"])})
        if not market:
            continue
            
        post = await db.unified_posts.find_one({"_id": ObjectId(market["post_id"])})
        
        current_value = pos["shares"] * market["price_current"]
        cost_basis = pos["shares"] * pos["avg_price"]
        pnl = current_value - cost_basis
        pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        positions.append({
            "market_id": pos["market_id"],
            "shares": pos["shares"],
            "avg_price": round(pos["avg_price"], 4),
            "current_price": round(market["price_current"], 4),
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
    
    return {
        "positions": positions,
        "total_value": round(total_value, 2),
        "cash_balance": round(user["balance_credits"], 2) if user else 0,
        "total_portfolio": round(total_value + (user["balance_credits"] if user else 0), 2)
    }


# ============== LEADERBOARD ==============

@api_router.get("/leaderboard")
async def get_leaderboard(
    sort_by: str = Query(default="xp", description="Sort by: xp, reputation, balance"),
    limit: int = Query(default=50, le=100),
    db=Depends(get_db)
):
    """Get global leaderboard"""
    sort_field = {
        "xp": "xp",
        "reputation": "reputation",
        "balance": "balance_credits"
    }.get(sort_by, "xp")
    
    users = []
    cursor = db.users.find({}).sort(sort_field, -1).limit(limit)
    
    rank = 1
    async for user in cursor:
        users.append({
            "rank": rank,
            "wallet_address": user.get("wallet_address", "")[:10] + "...",
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
    return {"message": "SocialFi Multi-Network Ingestion API", "status": "operational"}


@api_router.get("/health")
async def health_check(db=Depends(get_db)):
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("SocialFi Multi-Network Ingestion API started")
