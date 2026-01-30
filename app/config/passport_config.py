from datetime import datetime, timedelta
import os
import httpx
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException
from app.config.database import users_collection
from bson import ObjectId
from app.config import settings

# 비밀번호 암호화
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# ------------------------------------------------------------
# 로컬 로그인 (LocalStrategy 대체)
# ------------------------------------------------------------
async def local_login(email: str, password: str):
    email = email.lower()
    user = await users_collection.find_one({"email": email, "provider": "local"})
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    if not pwd_context.verify(password, user["password"]):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    if not user.get("isActive", True):
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")

    payload = {
        "sub": user["email"],
        "id": str(user["_id"]),
        "provider": "local",
        "userType": user.get("userType", "user"),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    user.pop("password", None)
    user["_id"] = str(user["_id"])
    return user, token