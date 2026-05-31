from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: EmailStr


class MarketSummary(BaseModel):
    market: str
    korean_name: str
    english_name: str
    trade_price: float
    signed_change_rate: float
    high_price: float
    low_price: float
    acc_trade_price_24h: float
    volatility_pct: float


class FavoriteCreate(BaseModel):
    market: str
    korean_name: str
    english_name: str


class FavoriteOut(BaseModel):
    id: int
    market: str
    korean_name: str
    english_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisOut(BaseModel):
    market: str
    korean_name: str
    summary: str
    trend: str
    volatility_score: float
    risk_note: str
    cached: bool
    created_at: datetime


class ConfigOut(BaseModel):
    app_name: str
    max_favorite_markets: int
    analysis_cache_minutes: int


class AnalyzeResponse(BaseModel):
    analyses: List[AnalysisOut]
