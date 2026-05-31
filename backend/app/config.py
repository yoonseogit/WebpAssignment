import os


APP_NAME = "CoinSight"

MAX_FAVORITE_MARKETS = int(os.getenv("MAX_FAVORITE_MARKETS", "7"))

ANALYSIS_CACHE_MINUTES = int(os.getenv("ANALYSIS_CACHE_MINUTES", "30"))
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-before-deploy")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://coinsight:coinsight@db:5432/coinsight")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
UPBIT_BASE_URL = "https://api.upbit.com/v1"
