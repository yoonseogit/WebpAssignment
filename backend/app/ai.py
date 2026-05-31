import json
from typing import List

from openai import AsyncOpenAI, OpenAIError

from .config import OPENAI_API_KEY, OPENAI_MODEL


def fallback_analysis(market: str, korean_name: str, candles: List[dict]) -> dict:
    first = candles[0]["trade_price"]
    last = candles[-1]["trade_price"]
    highs = [item["high_price"] for item in candles]
    lows = [item["low_price"] for item in candles]
    change_pct = ((last - first) / first * 100) if first else 0
    volatility_pct = ((max(highs) - min(lows)) / last * 100) if last else 0
    trend = "상승" if change_pct > 1 else "하락" if change_pct < -1 else "횡보"
    return {
        "summary": f"{korean_name}({market})은 최근 14일 기준 {change_pct:.2f}% 변동했습니다. 최고가와 최저가 기준 변동폭은 약 {volatility_pct:.2f}%입니다.",
        "trend": trend,
        "volatility_score": round(min(volatility_pct, 100), 2),
        "risk_note": "OpenAI API를 사용할 수 없어 로컬 계산 기반 요약을 표시합니다. 이 내용은 투자 조언이 아닌 학습용 데이터 요약입니다.",
    }


async def summarize_market(market: str, korean_name: str, candles: List[dict]) -> dict:
    if not OPENAI_API_KEY:
        return fallback_analysis(market, korean_name, candles)

    compact_candles = [
        {
            "date": item["candle_date_time_kst"][:10],
            "open": item["opening_price"],
            "high": item["high_price"],
            "low": item["low_price"],
            "close": item["trade_price"],
            "volume": item["candle_acc_trade_volume"],
        }
        for item in candles
    ]
    prompt = {
        "market": market,
        "korean_name": korean_name,
        "candles": compact_candles,
        "instruction": "투자 조언, 매수/매도 추천, 확정적 예측 없이 학습용 데이터 요약만 작성한다.",
    }

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        response = await client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": "You summarize cryptocurrency candle data in Korean for an educational web programming project. Never provide investment advice.",
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt, ensure_ascii=False),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "market_analysis",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "summary": {"type": "string"},
                            "trend": {"type": "string", "enum": ["상승", "하락", "횡보", "혼조"]},
                            "volatility_score": {"type": "number", "minimum": 0, "maximum": 100},
                            "risk_note": {"type": "string"},
                        },
                        "required": ["summary", "trend", "volatility_score", "risk_note"],
                    },
                    "strict": True,
                }
            },
        )
        return json.loads(response.output_text)
    except (OpenAIError, json.JSONDecodeError, KeyError):
        return fallback_analysis(market, korean_name, candles)
