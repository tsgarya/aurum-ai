from dataclasses import dataclass

@dataclass
class RiskDecision:
    approved: bool
    reason: str
    notional: float


def validate_order(side: str, quantity: float, price: float, cash: float,
                   current_position: float, max_order_notional: float,
                   max_position_notional: float) -> RiskDecision:
    """Deterministic risk gate; intentionally separate from any LLM."""
    if side not in {"buy", "sell"}:
        return RiskDecision(False, "Side must be buy or sell.", 0.0)
    if quantity <= 0 or price <= 0:
        return RiskDecision(False, "Quantity and price must be positive.", 0.0)
    notional = quantity * price
    if notional > max_order_notional:
        return RiskDecision(False, "Order exceeds maximum order notional.", notional)
    if side == "buy":
        if notional > cash:
            return RiskDecision(False, "Insufficient paper cash.", notional)
        if (current_position + quantity) * price > max_position_notional:
            return RiskDecision(False, "Order exceeds maximum position notional.", notional)
    elif quantity > current_position:
        return RiskDecision(False, "Cannot sell more shares than the paper position holds.", notional)
    return RiskDecision(True, "Approved by deterministic paper-trading risk rules.", notional)
