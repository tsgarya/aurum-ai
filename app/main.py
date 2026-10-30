from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .config import get_settings
from .schemas import ForecastResponse, BacktestRequest, OrderRequest, AgentReviewRequest
from .forecast import forecast_symbol
from .backtest import run_backtest
from .market_data import normalize_symbol
from .paper import PaperBroker
from .ai_review import review_forecast
from .workflow import research_and_simulate
from .database import recent_audit, audit

settings = get_settings()
broker = PaperBroker(settings.initial_cash)
app = FastAPI(title='AURUM AI API', version='0.2.0',
              description='Auditable AI-assisted equity research and simulated paper trading. Paper only; no live execution.')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False,
                   allow_methods=['GET','POST'], allow_headers=['*'])
STATIC = Path(__file__).parent / 'static'

@app.get('/', include_in_schema=False)
def dashboard():
    return FileResponse(STATIC / 'index.html')

@app.get('/health')
def health():
    return {'status':'ok','app':'AURUM AI','version':'0.2.0','nebius_configured':bool(settings.nebius_api_key),
            'trading_mode':'paper_only','persistence':'sqlite','live_broker_connected':False}

@app.get('/api/forecast/{symbol}', response_model=ForecastResponse)
def get_forecast(symbol: str):
    try:
        result = forecast_symbol(symbol)
        audit('forecast', result, actor='quant_engine')
        return result
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=502, detail=f'Forecast failed: {type(exc).__name__}') from exc

@app.post('/api/backtest')
def backtest(request: BacktestRequest):
    try:
        result = run_backtest(request.symbol, request.period, request.initial_cash, request.fee_bps, request.slippage_bps)
        audit('backtest', result, actor='backtest_engine')
        return result
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=502, detail=f'Backtest failed: {type(exc).__name__}') from exc

@app.get('/api/paper/account')
def paper_account(): return broker.snapshot()

@app.post('/api/paper/orders')
def place_paper_order(request: OrderRequest):
    try:
        symbol, _ = normalize_symbol(request.symbol)
        return broker.submit(symbol, request.side, request.quantity, request.reference_price,
                             request.max_order_notional, request.max_position_notional)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post('/api/agent/review')
def agent_review(request: AgentReviewRequest):
    result = review_forecast(request.forecast.model_dump(), request.question)
    audit('nemotron_review', {'symbol':request.forecast.symbol,'status':result.get('status'),
                              'model':result.get('model'),'result':result}, actor='nebius_nemotron')
    return result

@app.post('/api/workflow/{symbol}')
def workflow(symbol: str, quantity: float = 1.0):
    try: return research_and_simulate(symbol, quantity)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=502, detail=f'Workflow failed: {type(exc).__name__}') from exc

@app.get('/api/audit')
def audit_log(limit: int = 50):
    return {'events':recent_audit(max(1,min(limit,200)))}

@app.get('/api/markets')
def markets():
    return {'india':['RELIANCE.NS','TCS.NS','INFY.NS','HDFCBANK.NS'],'us':['AAPL','MSFT','NVDA','GOOGL'],
            'note':'Examples only; availability and data quality depend on the provider.'}
