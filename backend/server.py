from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime, timezone
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from database import get_db, init_db, User, Post, Market, Trade, Balance, Report, Transaction, AdminAction
from auth import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_user,
    require_admin,
    require_moderator
)
from amm import calculate_buy_cost, calculate_sell_revenue, distribute_fees, get_price

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

init_db()

app = FastAPI(title="InfoFi/SocialFi API")
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


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    
    @field_validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscore allowed)')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserPublic(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    reputation: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserPrivate(BaseModel):
    id: int
    email: str
    username: str
    avatar_url: Optional[str] = None
    balance_credits: float
    reputation: float
    is_admin: bool
    is_moderator: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    image_url: Optional[str] = None
    link_url: Optional[str] = None

class PostResponse(BaseModel):
    id: int
    user_id: int
    content: str
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    status: str
    view_count: int
    created_at: datetime
    user: UserPublic
    market: Optional['MarketResponse'] = None
    
    class Config:
        from_attributes = True

class MarketResponse(BaseModel):
    id: int
    post_id: int
    total_supply: float
    total_volume: float
    price_current: float
    fees_collected: float
    is_frozen: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TradeRequest(BaseModel):
    market_id: int
    shares: float = Field(gt=0)

class TradeResponse(BaseModel):
    id: int
    market_id: int
    user_id: int
    trade_type: str
    shares: float
    price_per_share: float
    total_cost: float
    fee_amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    id: int
    user_id: int
    market_id: int
    shares_owned: float
    avg_buy_price: float
    current_value: float
    post: PostResponse
    
    class Config:
        from_attributes = True

class ReportCreate(BaseModel):
    post_id: int
    reason: str = Field(min_length=1, max_length=50)
    description: Optional[str] = None

class ReportResponse(BaseModel):
    id: int
    post_id: int
    reporter_id: int
    reason: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


@api_router.get("/")
async def root():
    return {"message": "InfoFi/SocialFi API - Version 1.0"}


@api_router.post("/auth/register", response_model=UserPrivate)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        balance_credits=1000.00,
        oauth_provider='email'
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    transaction = Transaction(
        user_id=new_user.id,
        transaction_type='signup_bonus',
        amount=1000.00,
        balance_after=1000.00,
        description='Welcome bonus'
    )
    db.add(transaction)
    db.commit()
    
    logger.info(f"New user registered: {new_user.username}")
    
    return new_user


@api_router.post("/auth/login")
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account banned: {user.ban_reason}"
        )
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserPrivate.model_validate(user)
    }


@api_router.get("/auth/me", response_model=UserPrivate)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@api_router.post("/posts", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.balance_credits < 10:
        raise HTTPException(status_code=400, detail="Insufficient balance to create post (10 credits required)")
    
    new_post = Post(
        user_id=current_user.id,
        content=post_data.content,
        image_url=post_data.image_url,
        link_url=post_data.link_url,
        status='active'
    )
    
    db.add(new_post)
    db.flush()
    
    new_market = Market(
        post_id=new_post.id,
        total_supply=100.00,
        price_current=get_price(100.00)
    )
    
    db.add(new_market)
    db.flush()
    
    creator_balance = Balance(
        user_id=current_user.id,
        market_id=new_market.id,
        shares_owned=100.00,
        avg_buy_price=1.00
    )
    db.add(creator_balance)
    
    current_user.balance_credits -= 100.00
    current_user.reputation += 0.5
    
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type='post_created',
        amount=-100.00,
        balance_after=current_user.balance_credits,
        description=f'Created post and market (received 100 shares)',
        reference_id=new_post.id
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(new_post)
    
    logger.info(f"Post created by user {current_user.username}: {new_post.id}")
    
    return PostResponse(
        id=new_post.id,
        user_id=new_post.user_id,
        content=new_post.content,
        image_url=new_post.image_url,
        link_url=new_post.link_url,
        status=new_post.status,
        view_count=new_post.view_count,
        created_at=new_post.created_at,
        user=UserPublic.model_validate(current_user),
        market=MarketResponse.model_validate(new_market)
    )


@api_router.get("/posts", response_model=List[PostResponse])
async def list_posts(
    sort: str = 'volume',
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Post).filter(Post.status == 'active')
    
    if sort == 'volume':
        query = query.join(Market).order_by(desc(Market.total_volume))
    elif sort == 'price':
        query = query.join(Market).order_by(desc(Market.price_current))
    elif sort == 'new':
        query = query.order_by(desc(Post.created_at))
    else:
        query = query.join(Market).order_by(desc(Market.total_volume))
    
    posts = query.offset(offset).limit(limit).all()
    
    return [
        PostResponse(
            id=post.id,
            user_id=post.user_id,
            content=post.content,
            image_url=post.image_url,
            link_url=post.link_url,
            status=post.status,
            view_count=post.view_count,
            created_at=post.created_at,
            user=UserPublic.model_validate(post.user),
            market=MarketResponse.model_validate(post.market) if post.market else None
        )
        for post in posts
    ]


@api_router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.view_count += 1
    db.commit()
    
    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        content=post.content,
        image_url=post.image_url,
        link_url=post.link_url,
        status=post.status,
        view_count=post.view_count,
        created_at=post.created_at,
        user=UserPublic.model_validate(post.user),
        market=MarketResponse.model_validate(post.market) if post.market else None
    )


@api_router.get("/markets/{market_id}", response_model=MarketResponse)
async def get_market(market_id: int, db: Session = Depends(get_db)):
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    return market


@api_router.get("/markets/{market_id}/quote")
async def get_quote(market_id: int, shares: float, trade_type: str = 'buy', db: Session = Depends(get_db)):
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if market.is_frozen:
        raise HTTPException(status_code=400, detail="Market is frozen")
    
    try:
        if trade_type == 'buy':
            result = calculate_buy_cost(market.total_supply, shares)
        else:
            result = calculate_sell_revenue(market.total_supply, shares)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/trades/buy", response_model=TradeResponse)
async def buy_shares(
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    market = db.query(Market).filter(Market.id == trade_data.market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if market.is_frozen:
        raise HTTPException(status_code=400, detail="Market is frozen")
    
    try:
        cost_calc = calculate_buy_cost(market.total_supply, trade_data.shares)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if current_user.balance_credits < cost_calc['total_cost']:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    fees = distribute_fees(cost_calc['fee'])
    
    creator = db.query(User).filter(User.id == market.post.user_id).first()
    creator.balance_credits += fees['creator_fee']
    creator.reputation += 0.1
    
    transaction_creator = Transaction(
        user_id=creator.id,
        transaction_type='fee_earned',
        amount=fees['creator_fee'],
        balance_after=creator.balance_credits,
        description=f'Trading fee from market {market.id}',
        reference_id=market.id
    )
    db.add(transaction_creator)
    
    market.total_supply = cost_calc['new_supply']
    market.price_current = cost_calc['new_price']
    market.total_volume += cost_calc['cost_before_fee']
    market.fees_collected += cost_calc['fee']
    market.creator_earnings += fees['creator_fee']
    market.liquidity_pool += fees['liquidity_fee']
    market.last_trade_at = datetime.now(timezone.utc)
    
    current_user.balance_credits -= cost_calc['total_cost']
    current_user.reputation += 0.1
    
    balance = db.query(Balance).filter(
        Balance.user_id == current_user.id,
        Balance.market_id == market.id
    ).first()
    
    if balance:
        total_shares = balance.shares_owned + trade_data.shares
        balance.avg_buy_price = (
            (balance.shares_owned * balance.avg_buy_price + cost_calc['cost_before_fee']) / total_shares
        )
        balance.shares_owned = total_shares
        balance.updated_at = datetime.now(timezone.utc)
    else:
        balance = Balance(
            user_id=current_user.id,
            market_id=market.id,
            shares_owned=trade_data.shares,
            avg_buy_price=cost_calc['avg_price']
        )
        db.add(balance)
    
    trade = Trade(
        market_id=market.id,
        user_id=current_user.id,
        trade_type='buy',
        shares=trade_data.shares,
        price_per_share=cost_calc['avg_price'],
        total_cost=cost_calc['total_cost'],
        fee_amount=cost_calc['fee'],
        supply_before=cost_calc['new_supply'] - trade_data.shares,
        supply_after=cost_calc['new_supply']
    )
    db.add(trade)
    
    transaction_user = Transaction(
        user_id=current_user.id,
        transaction_type='trade_buy',
        amount=-cost_calc['total_cost'],
        balance_after=current_user.balance_credits,
        description=f'Bought {trade_data.shares} shares in market {market.id}',
        reference_id=market.id
    )
    db.add(transaction_user)
    
    db.commit()
    db.refresh(trade)
    
    logger.info(f"User {current_user.username} bought {trade_data.shares} shares in market {market.id}")
    
    return trade


@api_router.post("/trades/sell", response_model=TradeResponse)
async def sell_shares(
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    market = db.query(Market).filter(Market.id == trade_data.market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if market.is_frozen:
        raise HTTPException(status_code=400, detail="Market is frozen")
    
    balance = db.query(Balance).filter(
        Balance.user_id == current_user.id,
        Balance.market_id == market.id
    ).first()
    
    if not balance or balance.shares_owned < trade_data.shares:
        raise HTTPException(status_code=400, detail="Insufficient shares to sell")
    
    try:
        revenue_calc = calculate_sell_revenue(market.total_supply, trade_data.shares)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    fees = distribute_fees(revenue_calc['fee'])
    
    creator = db.query(User).filter(User.id == market.post.user_id).first()
    creator.balance_credits += fees['creator_fee']
    
    transaction_creator = Transaction(
        user_id=creator.id,
        transaction_type='fee_earned',
        amount=fees['creator_fee'],
        balance_after=creator.balance_credits,
        description=f'Trading fee from market {market.id}',
        reference_id=market.id
    )
    db.add(transaction_creator)
    
    market.total_supply = revenue_calc['new_supply']
    market.price_current = revenue_calc['new_price']
    market.total_volume += revenue_calc['revenue_before_fee']
    market.fees_collected += revenue_calc['fee']
    market.creator_earnings += fees['creator_fee']
    market.liquidity_pool += fees['liquidity_fee']
    market.last_trade_at = datetime.now(timezone.utc)
    
    current_user.balance_credits += revenue_calc['total_revenue']
    current_user.reputation += 0.1
    
    balance.shares_owned -= trade_data.shares
    balance.updated_at = datetime.now(timezone.utc)
    
    trade = Trade(
        market_id=market.id,
        user_id=current_user.id,
        trade_type='sell',
        shares=trade_data.shares,
        price_per_share=revenue_calc['avg_price'],
        total_cost=revenue_calc['total_revenue'],
        fee_amount=revenue_calc['fee'],
        supply_before=revenue_calc['new_supply'] + trade_data.shares,
        supply_after=revenue_calc['new_supply']
    )
    db.add(trade)
    
    transaction_user = Transaction(
        user_id=current_user.id,
        transaction_type='trade_sell',
        amount=revenue_calc['total_revenue'],
        balance_after=current_user.balance_credits,
        description=f'Sold {trade_data.shares} shares in market {market.id}',
        reference_id=market.id
    )
    db.add(transaction_user)
    
    db.commit()
    db.refresh(trade)
    
    logger.info(f"User {current_user.username} sold {trade_data.shares} shares in market {market.id}")
    
    return trade


@api_router.get("/users/me/portfolio", response_model=List[BalanceResponse])
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    balances = db.query(Balance).filter(
        Balance.user_id == current_user.id,
        Balance.shares_owned > 0
    ).all()
    
    result = []
    for balance in balances:
        market = balance.market
        post = market.post
        current_value = balance.shares_owned * market.price_current
        
        result.append(BalanceResponse(
            id=balance.id,
            user_id=balance.user_id,
            market_id=balance.market_id,
            shares_owned=balance.shares_owned,
            avg_buy_price=balance.avg_buy_price,
            current_value=current_value,
            post=PostResponse(
                id=post.id,
                user_id=post.user_id,
                content=post.content,
                image_url=post.image_url,
                link_url=post.link_url,
                status=post.status,
                view_count=post.view_count,
                created_at=post.created_at,
                user=UserPublic.model_validate(post.user),
                market=MarketResponse.model_validate(market)
            )
        ))
    
    return result


@api_router.get("/trades/history", response_model=List[TradeResponse])
async def get_trade_history(
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    trades = db.query(Trade).filter(
        Trade.user_id == current_user.id
    ).order_by(desc(Trade.created_at)).limit(limit).all()
    
    return trades


@api_router.post("/reports", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == report_data.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    new_report = Report(
        post_id=report_data.post_id,
        reporter_id=current_user.id,
        reason=report_data.reason,
        description=report_data.description,
        status='pending'
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    logger.info(f"Report created by user {current_user.username} for post {report_data.post_id}")
    
    return new_report


@api_router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    query = db.query(Report)
    
    if status_filter:
        query = query.filter(Report.status == status_filter)
    
    reports = query.order_by(desc(Report.created_at)).all()
    
    return reports


@api_router.patch("/reports/{report_id}")
async def resolve_report(
    report_id: int,
    resolution: str,
    action: str,
    current_user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = 'actioned' if action != 'dismiss' else 'dismissed'
    report.resolution = resolution
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.now(timezone.utc)
    
    if action == 'hide':
        post = db.query(Post).filter(Post.id == report.post_id).first()
        post.status = 'hidden'
        post.moderation_note = resolution
    elif action == 'delete':
        post = db.query(Post).filter(Post.id == report.post_id).first()
        post.status = 'deleted'
        post.moderation_note = resolution
        if post.market:
            post.market.is_frozen = True
    
    admin_action = AdminAction(
        admin_id=current_user.id,
        action_type=f'report_{action}',
        target_type='post',
        target_id=report.post_id,
        reason=resolution
    )
    db.add(admin_action)
    
    db.commit()
    
    logger.info(f"Report {report_id} resolved by {current_user.username}: {action}")
    
    return {"message": "Report resolved", "action": action}


@api_router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(func.count(User.id)).scalar()
    total_posts = db.query(func.count(Post.id)).scalar()
    total_trades = db.query(func.count(Trade.id)).scalar()
    total_volume = db.query(func.sum(Market.total_volume)).scalar() or 0
    total_fees = db.query(func.sum(Market.fees_collected)).scalar() or 0
    pending_reports = db.query(func.count(Report.id)).filter(Report.status == 'pending').scalar()
    
    return {
        "total_users": total_users,
        "total_posts": total_posts,
        "total_trades": total_trades,
        "total_volume": round(total_volume, 2),
        "total_fees": round(total_fees, 2),
        "pending_reports": pending_reports
    }


@api_router.post("/admin/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    reason: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot ban admin users")
    
    user.is_banned = True
    user.ban_reason = reason
    
    admin_action = AdminAction(
        admin_id=current_user.id,
        action_type='ban_user',
        target_type='user',
        target_id=user_id,
        reason=reason
    )
    db.add(admin_action)
    
    db.commit()
    
    logger.info(f"User {user_id} banned by admin {current_user.username}")
    
    return {"message": "User banned successfully"}


app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    logger.info("InfoFi/SocialFi API started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("InfoFi/SocialFi API shutting down")
