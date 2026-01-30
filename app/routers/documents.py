# app/routers/documents.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_documents():
    return {"message": "Documents endpoint active"}