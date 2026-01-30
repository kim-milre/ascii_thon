from fastapi import APIRouter, Request
from app.services.detect_service import detect_risks

router = APIRouter()

@router.post("")
async def detect_text(request: Request):
    data = await request.json()
    text = data.get("text", "")
    results = detect_risks(text)
    return {"count": len(results), "results": results}