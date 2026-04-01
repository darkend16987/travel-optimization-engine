import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hybrid_search
import ai_advisor

app = FastAPI(title="Travel Optimization Engine API", description="AI Skills API for flight optimization", version="1.0.0")

# Setup CORS to allow Next.js app to fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    origin: str
    destination: str
    depart: str
    return_date: str | None = None
    adults: int = 1
    max_stops: int | None = None

class AIAnalyzeRequest(BaseModel):
    flight_data: dict
    skill_name: str

@app.post("/api/search")
def search_flights(req: SearchRequest):
    try:
        results = hybrid_search.hybrid_search(
            origin=req.origin,
            destination=req.destination,
            departure_date=req.depart,
            return_date=req.return_date,
            adults=req.adults
        )
        
        # If max_stops is specified, filter it
        if req.max_stops is not None:
            results = [r for r in results if r.get('stops', 99) <= req.max_stops]
            
        return {"flights": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-analyze")
def analyze_flight(req: AIAnalyzeRequest):
    try:
        advisory = ai_advisor.generate_advisory(req.flight_data, req.skill_name)
        return {"advisory": advisory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Make sure to run on 8080 as per the plan
    uvicorn.run(app, host="0.0.0.0", port=8080)
