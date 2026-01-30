from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config.database import users_collection
from app.config.settings import settings
from bson import ObjectId
import httpx

print("SECRET_KEY =>", settings.SECRET_KEY)

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class AuthService:
    # ------------------------------------------------------------
    # 로컬 회원가입
    # ------------------------------------------------------------
    async def register_user(self, email: str, password: str, name: str):
        email = email.lower()
        existing_user = await users_collection.find_one({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 이메일입니다."
            )

        try:
            hashed_pw = pwd_context.hash(password)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="비밀번호는 72자 이하로 입력해주세요."
            )
        new_user = {
            "email": email,
            "password": hashed_pw,
            "name": name,
            "provider": "local",
            "userType": "user",
            "isActive": True,
            "createdAt": datetime.utcnow(),
        }

        result = await users_collection.insert_one(new_user)
        new_user["_id"] = str(result.inserted_id)
        del new_user["password"]
        new_user["createdAt"] = str(new_user["createdAt"])
        return new_user

    # ------------------------------------------------------------
    # 로컬 로그인
    # ------------------------------------------------------------
    async def authenticate_user(self, email: str, password: str):
        user = await users_collection.find_one({"email": email.lower(), "provider": "local"})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다."
            )

        if not pwd_context.verify(password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다."
            )

        if not user.get("isActive", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다."
            )

        token_data = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "provider": user.get("provider", "local"),
            "userType": user.get("userType", "user"),
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        user.pop("password", None)
        user["_id"] = str(user["_id"])
        if isinstance(user.get("createdAt"), datetime):
            user["createdAt"] = user["createdAt"].isoformat()

        return user, access_token

    # ------------------------------------------------------------
    # 로그아웃
    # ------------------------------------------------------------
    async def logout_user(self, user_id: str):
        return True

    # ------------------------------------------------------------
    # 현재 로그인한 사용자 정보 조회
    # ------------------------------------------------------------
    async def get_current_user_info(self, user_id: str):
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return user

auth_service = AuthService()