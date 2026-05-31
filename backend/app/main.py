import json
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .ai import summarize_market
from .config import ANALYSIS_CACHE_MINUTES, APP_NAME, MAX_FAVORITE_MARKETS
from .database import get_db, init_db
from .models import AnalysisCache, FavoriteMarket, User
from .schemas import (
    AnalyzeResponse,
    ConfigOut,
    FavoriteCreate,
    FavoriteOut,
    MarketSummary,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from .security import create_access_token, get_current_user, hash_password, verify_password
from .upbit import fetch_daily_candles, fetch_volatility_rankings


app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": APP_NAME}


@app.get("/api/config", response_model=ConfigOut)
def get_config():
    return {
        "app_name": APP_NAME,
        "max_favorite_markets": MAX_FAVORITE_MARKETS,
        "analysis_cache_minutes": ANALYSIS_CACHE_MINUTES,
    }


@app.post("/api/auth/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="비밀번호는 6자 이상이어야 합니다.")
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user), "email": user.email}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    return {"access_token": create_access_token(user), "email": user.email}


@app.get("/api/markets/volatility", response_model=list[MarketSummary])
async def markets_volatility():
    return await fetch_volatility_rankings()


@app.get("/api/favorites", response_model=list[FavoriteOut])
def list_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(FavoriteMarket)
        .filter(FavoriteMarket.user_id == current_user.id)
        .order_by(FavoriteMarket.created_at.asc())
        .all()
    )


@app.post("/api/favorites", response_model=FavoriteOut)
def add_favorite(
    payload: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exists = (
        db.query(FavoriteMarket)
        .filter(FavoriteMarket.user_id == current_user.id, FavoriteMarket.market == payload.market)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="이미 관심 종목에 추가되어 있습니다.")

    count = db.query(FavoriteMarket).filter(FavoriteMarket.user_id == current_user.id).count()
    if count >= MAX_FAVORITE_MARKETS:
        raise HTTPException(status_code=400, detail=f"관심 종목은 최대 {MAX_FAVORITE_MARKETS}개까지 등록할 수 있습니다.")

    favorite = FavoriteMarket(
        user_id=current_user.id,
        market=payload.market,
        korean_name=payload.korean_name,
        english_name=payload.english_name,
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@app.delete("/api/favorites/{market}")
def remove_favorite(
    market: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = (
        db.query(FavoriteMarket)
        .filter(FavoriteMarket.user_id == current_user.id, FavoriteMarket.market == market)
        .first()
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="관심 종목을 찾을 수 없습니다.")
    db.delete(favorite)
    db.commit()
    return {"ok": True}


@app.post("/api/analysis/favorites", response_model=AnalyzeResponse)
async def analyze_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorites = (
        db.query(FavoriteMarket)
        .filter(FavoriteMarket.user_id == current_user.id)
        .order_by(FavoriteMarket.created_at.asc())
        .all()
    )
    if not favorites:
        raise HTTPException(status_code=400, detail="관심 종목을 먼저 추가해 주세요.")

    expires_after = datetime.utcnow() - timedelta(minutes=ANALYSIS_CACHE_MINUTES)
    analyses = []
    for favorite in favorites:
        cached = (
            db.query(AnalysisCache)
            .filter(
                AnalysisCache.user_id == current_user.id,
                AnalysisCache.market == favorite.market,
                AnalysisCache.created_at >= expires_after,
            )
            .order_by(AnalysisCache.created_at.desc())
            .first()
        )
        if cached:
            analyses.append(
                {
                    "market": cached.market,
                    "korean_name": cached.korean_name,
                    "summary": cached.summary,
                    "trend": cached.trend,
                    "volatility_score": cached.volatility_score,
                    "risk_note": cached.risk_note,
                    "cached": True,
                    "created_at": cached.created_at,
                }
            )
            continue

        candles = await fetch_daily_candles(favorite.market)
        result = await summarize_market(favorite.market, favorite.korean_name, candles)
        record = AnalysisCache(
            user_id=current_user.id,
            market=favorite.market,
            korean_name=favorite.korean_name,
            summary=result["summary"],
            trend=result["trend"],
            volatility_score=float(result["volatility_score"]),
            risk_note=result["risk_note"],
            source_snapshot=json.dumps(candles, ensure_ascii=False),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        analyses.append(
            {
                "market": record.market,
                "korean_name": record.korean_name,
                "summary": record.summary,
                "trend": record.trend,
                "volatility_score": record.volatility_score,
                "risk_note": record.risk_note,
                "cached": False,
                "created_at": record.created_at,
            }
        )

    return {"analyses": analyses}
