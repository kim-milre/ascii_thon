# app/middleware/auth_middleware.py

from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from bson import ObjectId
from app.config.database import users_collection
from app.config.settings import settings
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier = payload.get("sub")

        if not user_identifier:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        query = (
            {"_id": ObjectId(user_identifier)}
            if ObjectId.is_valid(user_identifier)
            else {"email": user_identifier}
        )

        user = await users_collection.find_one(query)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        user["_id"] = str(user["_id"])
        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def is_authenticated(user: dict = Depends(get_current_user)):
    return user


async def is_local_account(user: dict = Depends(get_current_user)):
    if user.get("provider") != "local":
        raise HTTPException(status_code=403, detail="로컬 계정만 사용할 수 있습니다")
    return user


async def is_admin(user: dict = Depends(get_current_user)):
    if user.get("userType") != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return user