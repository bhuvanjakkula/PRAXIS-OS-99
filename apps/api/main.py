from fastapi import FastAPI
from praxis.core.models import Decision, InquiryReport
from praxis.services.orchestrator import PraxisOrchestrator

app=FastAPI(title="PRAXIS OS",version="0.1.0")
orchestrator=PraxisOrchestrator()

@app.get("/health")
def health(): return {"status":"ok","system":"PRAXIS OS"}

@app.post("/v1/inquiry",response_model=InquiryReport)
def inquiry(decision:Decision): return orchestrator.inquire(decision)
