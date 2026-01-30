# app/routers/analyze.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.controllers import sites_controller

router = APIRouter(prefix="/api/analyze", tags=["Analyze"])

class AnalyzeRequest(BaseModel):
    url: str

@router.post("/process")
async def analyze_site(req: AnalyzeRequest):
    try:
        return await sites_controller.process_site(req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))