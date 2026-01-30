# app/routers/sites.py
from fastapi import APIRouter, HTTPException, Depends
from app.config.database import analysis_collection
from app.controllers import sites_controller
from app.controllers.sites_controller import to_json_safe
from app.controllers.sites_controller import (
    list_sites,
    process_site,
    get_site_detail,
    delete_site,
    delete_all_sites,
)
from bson import ObjectId
from app.middleware.auth_middleware import get_current_user
from app.models.user_model import UserInDB

router = APIRouter(prefix="/api/sites", tags=["Sites"])

@router.get("/")
async def get_sites(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    data = await sites_controller.list_sites(user_id=user_id)
    return {"data": data}

@router.get("/{site_id}/progress")
async def get_site_progress(site_id: str, user=Depends(get_current_user)):
    site = await analysis_collection.find_one(
        {"_id": ObjectId(site_id), "user_id": str(user["_id"])},
        {"progress": 1}
    )

    if not site or "progress" not in site:
        return {
            "step": "PREPARING",
            "percent": 0
        }

    return site["progress"]

@router.get("/{id}")
async def get_site_detail_route(id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    user_id = str(current_user.get("_id") or current_user.get("sub"))
    doc = await sites_controller.get_site_detail(id, user_id=user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Result not found for this user")
    return {"data": doc}

@router.delete("/{id}")
async def delete_site_route(id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id") or current_user.get("sub"))
    return await sites_controller.delete_site(id, user_id)

@router.post("/process")
async def process_site_route(payload: dict, user=Depends(get_current_user)):
    url = payload.get("url")
    return await sites_controller.process_site(url, user_id=str(user["_id"]))


@router.delete("/all")
async def delete_all_sites(current_user: dict = Depends(get_current_user)):
    return await sites_controller.delete_all_sites(user_id=current_user.get("sub"))

@router.delete("/")
async def delete_all_sites(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    result = await sites_controller.delete_all_sites(user_id=user_id)
    return {"success": True, **result}
