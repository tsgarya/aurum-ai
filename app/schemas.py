from typing import Literal
from pydantic import BaseModel, Field

class ForecastResponse(BaseModel):
    symbol: str
    market: str
    data_source: str
    as_of: str
    last_close: float
    horizon_trading_days: int
    predicted_return_pct: float
    predicted_price: float
    probability_up: float
    volatility_annualized_pct: float
    method: str
    caveats: list[str]

class BacktestRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    period: str = "2y"
    initial_cash: float = Field(default=100000, gt=0)
    fee_bps: float = Field(default=10, ge=0, le=500)
    slippage_bps: float = Field(default=5, ge=0, le=500)

class OrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0, le=1_000_000)
    reference_price: float = Field(gt=0)
    max_order_notional: float = Field(default=100_000, gt=0)
    max_position_notional: float = Field(default=250_000, gt=0)

class AgentReviewRequest(BaseModel):
    forecast: ForecastResponse
    question: str = Field(default="Critique this forecast and list key uncertainties.", max_length=2000)
