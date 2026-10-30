# AURUM AI

**Auditable AI-assisted quantitative research and paper trading for Indian and US equities.** Built as a hackathon prototype for the NVIDIA × Nebius ecosystem.

> Paper trading only. No live broker is connected. This is an educational software prototype, not investment advice. Forecasts are uncertain and may be wrong.

## What is implemented

- Mobile-friendly browser dashboard served by FastAPI at `/`.
- Daily adjusted-price ingestion through `yfinance`, with a deterministic synthetic fallback explicitly marked `synthetic-demo`.
- Transparent EWMA-weighted return baseline and probability/volatility estimates.
- Long/cash moving-average backtest with delayed signals, fee and slippage assumptions, buy-and-hold comparison, approximate Sharpe and drawdown.
- Persistent SQLite paper ledger, with separate INR and USD cash accounts (no implicit FX conversion).
- Deterministic order checks: valid side/quantity/price, cash availability, maximum order notional, maximum position notional, and no short selling.
- Audit trail for forecasts, backtests, AI reviews, research workflow decisions, and paper orders.
- Optional NVIDIA Nemotron review through Nebius Token Factory using the OpenAI-compatible client.
- Dockerfile and Docker Compose deployment path.
- Tests for forecast math, risk controls, paper execution, persistence-oriented account behavior and API routes.

## Architecture

```text
Browser dashboard
      │
      ▼
FastAPI API ─────── SQLite ledger + audit events
      │
      ├── Market data adapter ── yfinance / clearly flagged synthetic fallback
      ├── Quant engine ───────── EWMA forecast baseline
      ├── Backtest engine ────── shifted signals + cost assumptions
      ├── Nebius client ──────── NVIDIA Nemotron critique (optional)
      └── Deterministic risk gate ── Paper broker only
```

The LLM can review and challenge supplied evidence. It cannot change a forecast's underlying numbers, bypass deterministic risk checks, or execute orders. `/api/workflow/{symbol}` runs a forecast/review/policy trace and deliberately does **not** submit an order automatically.

## Quick start (Python 3.11+)

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env   # On Windows, copy the file manually if needed
uvicorn app.main:app --reload --port 8000
```

Open:
- Dashboard: http://127.0.0.1:8000/
- Interactive API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

Try symbols such as `AAPL`, `NVDA`, `RELIANCE.NS`, `TCS.NS`, `INFY.NS`.

## Nebius Token Factory + NVIDIA Nemotron

1. Sign in to the [Nebius Token Factory portal](https://dev.nebius.com/token-factory) and create an API key.
2. Confirm the endpoint and exact Nemotron model identifier available to your account in the current console/docs.
3. Set these in `.env` (never commit `.env`):

```dotenv
NEBIUS_API_KEY=your_key_here
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b
```

The model ID above is an example/default and may need to be changed to a currently available model ID in your account. Restart the server. In the dashboard, forecast a ticker then select **Critique latest forecast**. Or call `POST /api/agent/review` using `/docs`.

A successful live provider call is only verified when the endpoint returns `status: "ok"`. Without credentials the app remains useful locally and returns `not_configured`; that does **not** satisfy a requirement to demonstrate actual use of Nebius/NVIDIA. Save a screenshot/log of a real successful call for the hackathon submission. Do not publish secrets or unredacted environment files.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service status and provider configuration state |
| GET | `/api/markets` | Example symbols by market |
| GET | `/api/forecast/{symbol}` | Quantitative forecast and provenance |
| POST | `/api/backtest` | Historical long/cash baseline evaluation |
| GET | `/api/paper/account` | INR/USD paper accounts, positions and recent orders |
| POST | `/api/paper/orders` | Risk-checked simulated order |
| POST | `/api/agent/review` | Nemotron review of supplied forecast |
| POST | `/api/workflow/{symbol}` | Forecast → critique → policy decision; never auto-orders |
| GET | `/api/audit?limit=50` | Recent auditable events |

Example paper order body:

```json
{
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 1,
  "reference_price": 100,
  "max_order_notional": 100000,
  "max_position_notional": 250000
}
```

Prices and limits use the currency of the symbol's account: USD for US symbols, INR for `.NS`/`.BO` symbols. This prototype does not validate the reference price against a real-time quote before an order; the user must verify it. A future version should make quote validation mandatory.

## Persistence and deployment

Local default database: `./aurum.db` (SQLite). Override with `AURUM_DB_PATH`. The ledger persists across process restarts. The database is for a single-user demo; there is no authentication or tenant isolation yet.

Run with Docker:

```bash
cp .env.example .env
# edit .env as needed
docker compose up --build
```

Then open `http://localhost:8000`. The Compose volume persists SQLite data. Keep this service private until authentication, HTTPS, per-user authorization, secret management, rate limits, and production database backups are implemented. Do not expose the unauthenticated order endpoints to the public internet.

## Tests

```bash
pytest -q
```

## Evaluation caveats

- `synthetic-demo` means fabricated data; never treat those outputs as market signals.
- Yahoo Finance data access can be delayed, rate-limited, revised or unavailable; this is not an exchange-grade market data feed.
- The EWMA estimator is a transparent baseline, not a validated predictor. Its probability is a normal approximation, not a calibrated probability.
- The backtest is illustrative, not production-grade: it does not fully model dividends/taxes, corporate actions, market impact, order book execution, survivorship bias or point-in-time universe membership. Validate these before making performance claims.
- A forecast or backtest cannot establish future returns. Avoid optimizing solely on the historical period.
- INR and USD accounts are kept separate; portfolio totals are not combined without FX conversion.

## Hackathon demo checklist

- [ ] Confirm official submission requirements and category.
- [ ] Capture successful `/health` response.
- [ ] Capture a real successful Nemotron response via Nebius Token Factory and record model ID/latency/usage.
- [ ] Show a live-data forecast and label its source; do not use synthetic fallback for performance claims.
- [ ] Run backtest and compare with buy-and-hold, including drawdown and cost assumptions.
- [ ] Submit one accepted and one rejected paper order to demonstrate the risk gate.
- [ ] Show the audit trail and separate INR/USD ledgers.
- [ ] Record a short demo; redact API keys and personal information.
- [ ] Include limitations and model-evaluation methodology in the submission.
