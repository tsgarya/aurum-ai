from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd


def normalize_symbol(symbol: str) -> tuple[str, str]:
    """Accept AAPL, RELIANCE.NS, TCS.NS, etc. Market is inferred for display only."""
    value = symbol.strip().upper()
    if not value or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-^=" for ch in value):
        raise ValueError("Invalid ticker. Use symbols such as AAPL, RELIANCE.NS, or TCS.NS.")
    market = "India (NSE/BSE)" if value.endswith((".NS", ".BO")) else "US / international"
    return value, market


def synthetic_prices(symbol: str, days: int = 520) -> pd.DataFrame:
    """Deterministic fallback data for development only; never represents real market prices."""
    seed = int(hashlib.sha256(symbol.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.utcnow().normalize(), periods=days)
    drift = 0.00025
    returns = rng.normal(drift, 0.012, size=days)
    close = 100 * np.exp(np.cumsum(returns))
    return pd.DataFrame({"Close": close}, index=dates)


def get_prices(symbol: str, period: str = "2y") -> tuple[pd.DataFrame, str]:
    """Try Yahoo Finance history, then use deterministic demo data if unavailable."""
    normalized, _ = normalize_symbol(symbol)
    try:
        import yfinance as yf
        frame = yf.download(normalized, period=period, interval="1d", auto_adjust=True,
                            progress=False, threads=False)
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        if frame is not None and not frame.empty and "Close" in frame.columns:
            result = frame[["Close"]].dropna().copy()
            result.index = pd.to_datetime(result.index)
            if len(result) >= 80:
                return result, "yfinance"
    except Exception:
        pass
    return synthetic_prices(normalized), "synthetic-demo"
