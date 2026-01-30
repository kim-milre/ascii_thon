from app.utils.deps import get_database
from bson import ObjectId

db = get_database()
sites_collection = db["sites"]

async def save_site(data: dict):
    result = await sites_collection.insert_one(data)
    data["_id"] = str(result.inserted_id)
    return data

async def get_sites():
    sites = await sites_collection.find().to_list(100)
    for s in sites:
        s["_id"] = str(s["_id"])
    return {"data": sites}

async def get_site_by_id(site_id: str):
    site = await sites_collection.find_one({"_id": ObjectId(site_id)})
    if site:
        site["_id"] = str(site["_id"])
    return site