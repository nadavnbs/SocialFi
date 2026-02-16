from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from database import get_db, init_db
from auth import create_access_token, get_current_user, require_admin, generate_challenge
from amm import calculate_buy_cost, calculate_sell_revenue, distribute_fees, get_price
from signature_verification import SignatureVerifier

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title="InfoFi Web3 SocialFi API")
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


class WalletChallengeRequest(BaseModel):
    wallet_address: str = Field(min_length=26, max_length=200)
    chain_type: str = Field(pattern="^(ethereum|base|polygon|bnb|solana)$")

class SignatureVerifyRequest(BaseModel):
    wallet_address: str
    challenge: str
    signature: str
    chain_type: str

class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    image_url: Optional[str] = None
    link_url: Optional[str] = None

class TradeRequest(BaseModel):
    market_id: str
    shares: float = Field(gt=0)


@api_router.get("/")
async def root():
    return {"message": "InfoFi Web3 SocialFi API - Wallet Auth"}


@api_router.post("/auth/challenge")
async def get_challenge(request: WalletChallengeRequest, db=Depends(get_db)):
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
            "balance_credits": 1000.00,
            "level": 1,
            "xp": 0,
            "reputation": 0.00,
            "is_admin": False,
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        }
        await db.users.insert_one(user)
        logger.info(f"New user: {request.wallet_address}")
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
            "wallet_address": request.wallet_address.lower(),
            "balance_credits": user.get("balance_credits", 1000),
            "level": user.get("level", 1),
            "xp": user.get("xp", 0),
            "reputation": user.get("reputation", 0)
        }
    }


@api_router.get("/auth/me")
async def get_me(current_wallet: str = Depends(get_current_user), db=Depends(get_db)):
    user = await db.users.find_one({"wallet_address": current_wallet.lower()})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["_id"] = str(user["_id"])
    return user


@api_router.post("/posts")
async def create_post(
    post_data: PostCreate,
    current_wallet: str = Depends(get_current_user),
    db=Depends(get_db)
):
    user = await db.users.find_one({"wallet_address": current_wallet.lower()})
    if user["balance_credits"] < 10:
        raise HTTPException(status_code=400, detail="Insufficient balance (10 credits required)")
    
    post = {
        "user_wallet": current_wallet.lower(),
        "content": post_data.content,
        "image_url": post_data.image_url,
        "link_url": post_data.link_url,
        "status": "active",
        "view_count": 0,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.posts.insert_one(post)
    post_id = str(result.inserted_id)
    
    market = {
        "post_id": post_id,
        "total_supply": 100.00,
        "total_volume": 0.00,
        "price_current": get_price(100.00),
        "fees_collected": 0.00,
        "creator_earnings": 0.00,
        "liquidity_pool": 0.00,
        "is_frozen": False,
        "created_at": datetime.now(timezone.utc)
    }
    
    market_result = await db.markets.insert_one(market)
    market_id = str(market_result.inserted_id)
    
    await db.balances.insert_one({
        "user_wallet": current_wallet.lower(),
        "market_id": market_id,
        "shares_owned": 100.00,
        "avg_buy_price": 1.00,
        "created_at": datetime.now(timezone.utc)
    })
    
    await db.users.update_one(
        {"wallet_address": current_wallet.lower()},
        {
            "$inc": {"balance_credits": -100, "reputation": 0.5, "xp": 50},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    logger.info(f"Post created: {post_id} by {current_wallet}")
    
    post["_id"] = post_id
    post["market"] = market
    post["market"]["_id"] = market_id
    return post


@api_router.get("/posts")
async def list_posts(sort: str = 'volume', limit: int = 50, db=Depends(get_db)):
    pipeline = [
        {"$match": {"status": "active"}},
        {"$lookup": {
            "from": "markets",
            "localField": "_id",
            "foreignField": "post_id",
            "as": "market"
        }},
        {"$unwind": "$market"},
        {"$sort": {"market.total_volume": -1 if sort == 'volume' else 1}},
        {"$limit": limit}
    ]
    
    posts = []
    async for post in db.posts.aggregate(pipeline):
        post["_id"] = str(post["_id"])
        post["market"]["_id"] = str(post["market"]["_id"])
        posts.append(post)
    
    return posts


@api_router.post("/trades/buy")
async def buy_shares(
    trade_data: TradeRequest,
    current_wallet: str = Depends(get_current_user),
    db=Depends(get_db)
):
    from bson import ObjectId
    
    market = await db.markets.find_one({"_id": ObjectId(trade_data.market_id)})
    if not market or market.get("is_frozen"):
        raise HTTPException(status_code=400, detail="Market not available")
    
    cost_calc = calculate_buy_cost(market["total_supply"], trade_data.shares)
    
    user = await db.users.find_one({"wallet_address": current_wallet.lower()})
    if user["balance_credits"] < cost_calc["total_cost"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    fees = distribute_fees(cost_calc["fee"])
    
    post = await db.posts.find_one({"_id": ObjectId(market["post_id"])})
    creator_wallet = post["user_wallet"]
    
    await db.users.update_one(
        {"wallet_address": creator_wallet},
        {"$inc": {"balance_credits": fees["creator_fee"], "xp": 10}}
    )
    
    await db.markets.update_one(
        {"_id": ObjectId(trade_data.market_id)},
        {
            "$set": {
                "total_supply": cost_calc["new_supply"],
                "price_current": cost_calc["new_price"],
                "last_trade_at": datetime.now(timezone.utc)
            },
            "$inc": {
                "total_volume": cost_calc["cost_before_fee"],
                "fees_collected": cost_calc["fee"],
                "creator_earnings": fees["creator_fee"],
                "liquidity_pool": fees["liquidity_fee"]
            }
        }
    )
    
    await db.users.update_one(
        {"wallet_address": current_wallet.lower()},
        {"$inc": {"balance_credits": -cost_calc["total_cost"], "xp": 20}}
    )
    
    balance = await db.balances.find_one({
        "user_wallet": current_wallet.lower(),
        "market_id": trade_data.market_id
    })
    
    if balance:
        total_shares = balance["shares_owned"] + trade_data.shares
        new_avg = (balance["shares_owned"] * balance["avg_buy_price"] + cost_calc["cost_before_fee"]) / total_shares
        await db.balances.update_one(
            {"_id": balance["_id"]},
            {"$set": {"shares_owned": total_shares, "avg_buy_price": new_avg}}
        )
    else:
        await db.balances.insert_one({
            "user_wallet": current_wallet.lower(),
            "market_id": trade_data.market_id,
            "shares_owned": trade_data.shares,
            "avg_buy_price": cost_calc["avg_price"],
            "created_at": datetime.now(timezone.utc)
        })
    
    await db.trades.insert_one({
        "market_id": trade_data.market_id,
        "user_wallet": current_wallet.lower(),
        "trade_type": "buy",
        "shares": trade_data.shares,
        "price_per_share": cost_calc["avg_price"],
        "total_cost": cost_calc["total_cost"],
        "fee_amount": cost_calc["fee"],
        "created_at": datetime.now(timezone.utc)
    })
    
    logger.info(f"Buy trade: {current_wallet} bought {trade_data.shares} shares")
    
    return {"success": True, "cost": cost_calc["total_cost"]}


@api_router.get("/users/me/portfolio")
async def get_portfolio(current_wallet: str = Depends(get_current_user), db=Depends(get_db)):
    from bson import ObjectId
    
    balances = []
    async for balance in db.balances.find({"user_wallet": current_wallet.lower(), "shares_owned": {"$gt": 0}}):
        market = await db.markets.find_one({"_id": ObjectId(balance["market_id"])})
        post = await db.posts.find_one({"_id": ObjectId(market["post_id"])})
        
        balance["_id"] = str(balance["_id"])
        balance["current_value"] = balance["shares_owned"] * market["price_current"]
        balance["market"] = market
        balance["market"]["_id"] = str(market["_id"])
        balance["post"] = post
        balance["post"]["_id"] = str(post["_id"])
        
        balances.append(balance)
    
    return balances


@api_router.get("/admin/dashboard")
async def admin_dashboard(current_wallet: str = Depends(require_admin), db=Depends(get_db)):
    total_users = await db.users.count_documents({})
    total_posts = await db.posts.count_documents({})
    total_trades = await db.trades.count_documents({})
    
    volume_result = await db.markets.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_volume"}}}
    ]).to_list(1)
    total_volume = volume_result[0]["total"] if volume_result else 0
    
    return {
        "total_users": total_users,
        "total_posts": total_posts,
        "total_trades": total_trades,
        "total_volume": round(total_volume, 2)
    }


app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("InfoFi Web3 SocialFi API started")
