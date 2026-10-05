from fastapi import FastAPI, HTTPException
from praxis_os.core.models import DecisionRequest
from praxis_os.core.engine import analyze
from praxis_os.connectors.world_bank import indicator

app = FastAPI(title="Praxis OS", version="0.1.0", description="Evidence-first public policy decision support")

@app.get("/health")
def health():
    return {"status": "ok", "service": "praxis-os"}

@app.post("/v1/decisions/analyze")
def analyze_decision(request: DecisionRequest):
    return analyze(request)

@app.get("/v1/data/world-bank/{country_code}/{indicator_code}")
async def world_bank(country_code: str, indicator_code: str, mrv: int = 10):
    try:
        return {"country": country_code.upper(), "indicator": indicator_code, "data": await indicator(country_code, indicator_code, mrv)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"World Bank data request failed: {exc}")
