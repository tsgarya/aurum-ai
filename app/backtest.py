from __future__ import annotations
import numpy as np
import pandas as pd
from .market_data import get_prices, normalize_symbol


def run_backtest(symbol: str, period: str = "2y", initial_cash: float = 100000,
                 fee_bps: float = 10, slippage_bps: float = 5) -> dict:
    """Long/cash toy strategy: buy when prior 20-day mean return is positive, else cash.

    Signals are shifted one bar so today's close is not used to trade at that same close.
    This is a baseline for validating the pipeline, not a strategy recommendation.
    """
    frame, source = get_prices(symbol, period)
    close = frame["Close"].astype(float).dropna()
    if len(close) < 80:
        raise ValueError("At least 80 valid daily closes are required for backtesting.")
    returns = close.pct_change().fillna(0.0)
    signal = (returns.rolling(20).mean() > 0).astype(float).shift(1).fillna(0.0)
    turnover = signal.diff().abs().fillna(signal.abs())
    cost_rate = (fee_bps + slippage_bps) / 10000.0
    strategy_returns = signal * returns - turnover * cost_rate
    equity = initial_cash * (1 + strategy_returns).cumprod()
    total_return = float(equity.iloc[-1] / initial_cash - 1)
    ann_vol = float(strategy_returns.std(ddof=1) * np.sqrt(252))
    ann_return = float((equity.iloc[-1] / initial_cash) ** (252 / max(len(equity), 1)) - 1)
    sharpe = float((strategy_returns.mean() * 252) / (strategy_returns.std(ddof=1) * np.sqrt(252) + 1e-12))
    drawdown = equity / equity.cummax() - 1
    buy_hold = float(close.iloc[-1] / close.iloc[0] - 1)
    normalized, market = normalize_symbol(symbol)
    return {
        "symbol": normalized, "market": market, "data_source": source,
        "strategy": "20-day mean-return sign; long/cash; signal delayed one trading bar",
        "bars": int(len(close)), "initial_cash": round(initial_cash, 2),
        "final_equity": round(float(equity.iloc[-1]), 2), "total_return_pct": round(total_return * 100, 3),
        "annualized_return_pct": round(ann_return * 100, 3), "annualized_volatility_pct": round(ann_vol * 100, 3),
        "sharpe_approx": round(sharpe, 3), "max_drawdown_pct": round(float(drawdown.min()) * 100, 3),
        "buy_hold_return_pct": round(buy_hold * 100, 3), "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "warning": "Illustrative baseline only; not a validated strategy. Results depend on data quality and assumptions.",
    }
