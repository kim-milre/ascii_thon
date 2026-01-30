# app/models/user_model.py
from datetime import datetime
from typing import Optional, Literal
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import os
from app.config import settings
from app.config.settings import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# MongoDB 연결 (Motor)
# -----------------------------
client = AsyncIOMotorClient(settings.DATABASE_URL)
db = client[settings.DB_NAME]
users_collection = db["users"]

# -----------------------------
# 유틸 함수: 비밀번호 해싱 및 검증
# -----------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# -----------------------------
# Pydantic 모델 정의
# -----------------------------
class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar: Optional[str] = None
    provider: Literal["local", "google", "naver"] = "local"
    providerId: Optional[str] = None
    isActive: bool = True
    userType: Literal["user", "admin"] = "user"

class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=6)

class UserInDB(UserBase):
    id: Optional[str] = Field(alias="_id")
    password: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        json_encoders = {ObjectId: str}
        orm_mode = True


# -----------------------------
# CRUD 함수
# -----------------------------
async def create_user(email: str, password: str, name: str, provider: str = "local", avatar: Optional[str] = None):
    # 이메일 중복 체크
    existing = await users_collection.find_one({"email": email, "provider": provider})
    if existing:
        raise ValueError("이미 사용 중인 이메일입니다.")

    hashed_pw = hash_password(password) if password else None

    user_doc = {
        "email": email.lower(),
        "password": hashed_pw,
        "name": name,
        "avatar": avatar,
        "provider": provider,
        "isActive": True,
        "userType": "user",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }

    result = await users_collection.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    user_doc.pop("password", None)
    return user_doc


async def get_user_by_email(email: str, provider: str = "local"):
    user = await users_collection.find_one({"email": email.lower(), "provider": provider})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def get_user_by_id(user_id: str):
    from bson import ObjectId
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.get("password", "")):
        return None
    if not user.get("isActive", True):
        raise ValueError("비활성화된 계정입니다.")
    user.pop("password", None)
    return user


async def update_user(user_id: str, update_data: dict):
    from bson import ObjectId
    update_data["updatedAt"] = datetime.utcnow()
    await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    updated_user = await get_user_by_id(user_id)
    return updated_user