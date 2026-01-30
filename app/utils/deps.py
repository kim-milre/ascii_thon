from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("DATABASE_URL", "mongodb+srv://<user>:<pass>@cluster.mongodb.net")

_client = AsyncIOMotorClient(MONGO_URI)
_db = _client["sducoss"]

def get_database():
    return _db