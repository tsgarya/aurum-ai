from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    nebius_api_key: str | None = os.getenv("NEBIUS_API_KEY") or None
    nebius_base_url: str = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.us-central1.nebius.com/v1/")
    nebius_model: str = os.getenv("NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b")
    data_mode: str = os.getenv("AURUM_DATA_MODE", "auto")
    initial_cash: float = float(os.getenv("AURUM_INITIAL_CASH", "1000000"))

@lru_cache

def get_settings() -> Settings:
    return Settings()
