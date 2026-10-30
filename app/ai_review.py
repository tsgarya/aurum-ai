from __future__ import annotations
from .config import get_settings


def review_forecast(forecast: dict, question: str) -> dict:
    settings = get_settings()
    if not settings.nebius_api_key:
        return {
            "status": "not_configured",
            "message": "Set NEBIUS_API_KEY in .env to enable NVIDIA Nemotron through Nebius Token Factory.",
            "model": settings.nebius_model,
            "fallback_review": [
                "Check whether the input data is live or synthetic-demo before interpreting this result.",
                "Compare the forecast with a naive zero-return baseline and a buy-and-hold benchmark.",
                "Inspect recent volatility, event risk, liquidity, and transaction costs.",
                "Do not convert this forecast into an order without independent risk validation.",
            ],
        }
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.nebius_api_key, base_url=settings.nebius_base_url)
        response = client.chat.completions.create(
            model=settings.nebius_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": (
                    "You are AURUM AI's skeptical equity research reviewer. Analyze only the supplied "
                    "data. Do not invent prices, claim certainty, or issue an order. Explicitly flag "
                    "synthetic data, uncertainty, model limitations, and missing evidence. This is "
                    "educational research, not personalized financial advice. Keep the answer concise."
                )},
                {"role": "user", "content": f"Question: {question}\nForecast JSON: {forecast}"},
            ],
        )
        return {"status": "ok", "provider": "Nebius Token Factory", "model": settings.nebius_model,
                "review": response.choices[0].message.content,
                "usage": getattr(response, "usage", None).model_dump() if getattr(response, "usage", None) else None}
    except Exception as exc:
        return {"status": "error", "provider": "Nebius Token Factory", "model": settings.nebius_model,
                "message": f"Model request failed ({type(exc).__name__}). Check credentials, model ID, and API URL."}
