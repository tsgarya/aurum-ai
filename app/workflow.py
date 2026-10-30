from __future__ import annotations
from .forecast import forecast_symbol
from .ai_review import review_forecast
from .database import audit
from .market_data import normalize_symbol


def research_and_simulate(symbol: str, quantity: float = 1.0, question: str = 'Challenge the forecast. What could make it wrong?') -> dict:
    """Auditable orchestration: forecast -> AI critique -> deterministic gate -> optional simulated order."""
    forecast = forecast_symbol(symbol)
    review = review_forecast(forecast, question)
    source_ok = forecast.get('data_source') != 'synthetic-demo'
    # A simple explicit baseline policy; this is a demo policy, not a recommendation.
    proposed_side = 'buy' if forecast['predicted_return_pct'] > 0 and forecast['probability_up'] >= 0.55 else 'sell'
    decision = {'proposed_side': proposed_side, 'eligible': bool(source_ok and proposed_side == 'buy'),
                'reason': 'Live/history data and positive baseline signal required; only long/cash demo policy.' if source_ok else
                          'Blocked: synthetic demo data cannot trigger simulated orders.'}
    result = {'symbol': forecast['symbol'], 'forecast': forecast, 'ai_review': review,
              'policy_decision': decision,
              'next_step': 'Submit a separate paper order after reviewing the forecast and risk limits; workflow never auto-submits.'}
    audit('research_workflow', result, actor='orchestrator')
    return result
