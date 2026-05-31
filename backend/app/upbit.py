from datetime import datetime, timedelta
from typing import Dict, List

import httpx

from .config import UPBIT_BASE_URL


_market_cache: Dict[str, object] = {"expires_at": datetime.min, "items": []}
_ticker_cache: Dict[str, object] = {"expires_at": datetime.min, "items": []}


async def fetch_krw_markets() -> List[dict]:
    now = datetime.utcnow()
    if now < _market_cache["expires_at"]:
        return _market_cache["items"]

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{UPBIT_BASE_URL}/market/all", params={"isDetails": "false"})
        response.raise_for_status()
        markets = [item for item in response.json() if item["market"].startswith("KRW-")]

    _market_cache["items"] = markets
    _market_cache["expires_at"] = now + timedelta(minutes=10)
    return markets


async def fetch_volatility_rankings() -> List[dict]:
    now = datetime.utcnow()
    if now < _ticker_cache["expires_at"]:
        return _ticker_cache["items"]

    markets = await fetch_krw_markets()
    market_map = {item["market"]: item for item in markets}
    codes = ",".join(market_map.keys())

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"{UPBIT_BASE_URL}/ticker", params={"markets": codes})
        response.raise_for_status()
        tickers = response.json()

    rankings = []
    for ticker in tickers:
        trade_price = float(ticker.get("trade_price") or 0)
        high_price = float(ticker.get("high_price") or 0)
        low_price = float(ticker.get("low_price") or 0)
        volatility_pct = ((high_price - low_price) / trade_price * 100) if trade_price else 0
        market_info = market_map[ticker["market"]]
        rankings.append(
            {
                "market": ticker["market"],
                "korean_name": market_info["korean_name"],
                "english_name": market_info["english_name"],
                "trade_price": trade_price,
                "signed_change_rate": float(ticker.get("signed_change_rate") or 0),
                "high_price": high_price,
                "low_price": low_price,
                "acc_trade_price_24h": float(ticker.get("acc_trade_price_24h") or 0),
                "volatility_pct": round(volatility_pct, 2),
            }
        )

    rankings.sort(key=lambda item: item["volatility_pct"], reverse=True)
    _ticker_cache["items"] = rankings
    _ticker_cache["expires_at"] = now + timedelta(seconds=45)
    return rankings


async def fetch_daily_candles(market: str, count: int = 14) -> List[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{UPBIT_BASE_URL}/candles/days",
            params={"market": market, "count": count},
        )
        response.raise_for_status()
        candles = response.json()
    return list(reversed(candles))
