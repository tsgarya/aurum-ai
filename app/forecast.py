from __future__ import annotations
import math
import numpy as np
import pandas as pd
from .market_data import get_prices, normalize_symbol

CAVEATS = [
    "This is an experimental statistical estimate, not investment advice or a guaranteed outcome.",
    "Forecasts can fail under regime changes, news shocks, illiquidity, and market gaps.",
    "If data_source is synthetic-demo, prices are fabricated for software testing and must not inform a real trade.",
]

def forecast_from_frame(symbol: str, frame: pd.DataFrame, data_source: str, horizon: int = 5) -> dict:
    close = frame["Close"].astype(float).dropna()
    if len(close) < 60:
        raise ValueError("At least 60 valid daily closes are required.")
    returns = close.pct_change().dropna()
    # A transparent, conservative baseline: exponentially weighted mean daily return.
    recent = returns.tail(60).to_numpy()
    weights = np.exp(np.linspace(-2.0, 0.0, len(recent)))
    weights /= weights.sum()
    daily_mu = float(np.sum(recent * weights))
    daily_vol = float(returns.tail(60).std(ddof=1))
    predicted_return = float(np.clip(daily_mu * horizon, -0.15, 0.15))
    last_close = float(close.iloc[-1])
    # Normal approximation for P(cumulative return > 0); intentionally explicit baseline.
    denom = max(daily_vol * math.sqrt(horizon), 1e-9)
    z = (daily_mu * horizon) / denom
    probability_up = float(np.clip(0.5 * (1.0 + math.erf(z / math.sqrt(2.0))), 0.01, 0.99))
    symbol, market = normalize_symbol(symbol)
    as_of = pd.Timestamp(close.index[-1]).isoformat()
    return {
        "symbol": symbol, "market": market, "data_source": data_source, "as_of": as_of,
        "last_close": round(last_close, 4), "horizon_trading_days": horizon,
        "predicted_return_pct": round(predicted_return * 100, 4),
        "predicted_price": round(last_close * (1 + predicted_return), 4),
        "probability_up": round(probability_up, 4),
        "volatility_annualized_pct": round(daily_vol * math.sqrt(252) * 100, 4),
        "method": "EWMA-weighted mean of trailing 60 daily returns; capped 5-day estimate",
        "caveats": CAVEATS,
    }

def forecast_symbol(symbol: str, period: str = "2y", horizon: int = 5) -> dict:
    frame, source = get_prices(symbol, period)
    return forecast_from_frame(symbol, frame, source, horizon)
