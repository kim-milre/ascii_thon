from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
async def list_policies():
    return {"message": "Policies endpoint is active"}