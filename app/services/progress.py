from datetime import datetime
from bson import ObjectId
from app.config.database import analysis_collection

async def update_progress(site_id: str, step: str, percent: int):
    await analysis_collection.update_one(
        {"_id": ObjectId(site_id)},
        {"$set": {
            "progress": {
                "step": step,
                "percent": percent,
                "updated_at": datetime.utcnow()
            }
        }}
    )