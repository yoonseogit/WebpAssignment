from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    favorites = relationship("FavoriteMarket", back_populates="user", cascade="all, delete-orphan")


class FavoriteMarket(Base):
    __tablename__ = "favorite_markets"
    __table_args__ = (UniqueConstraint("user_id", "market", name="uq_user_market"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market = Column(String(32), nullable=False, index=True)
    korean_name = Column(String(100), nullable=False)
    english_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="favorites")


class AnalysisCache(Base):
    __tablename__ = "analysis_cache"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market = Column(String(32), nullable=False, index=True)
    korean_name = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    trend = Column(String(40), nullable=False)
    volatility_score = Column(Float, nullable=False)
    risk_note = Column(Text, nullable=False)
    source_snapshot = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
