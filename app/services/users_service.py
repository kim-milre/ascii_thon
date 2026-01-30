from fastapi import HTTPException, status
from passlib.context import CryptContext
from bson import ObjectId
from app.config.database import users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UsersService:
    # ------------------------------------------------------------
    # 사용자 프로필 조회
    # ------------------------------------------------------------
    async def get_profile(self, user_id: str):
        user = await users_collection.find_one({"_id": ObjectId(user_id), "isActive": True})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return user

    # ------------------------------------------------------------
    # 사용자 프로필 수정
    # ------------------------------------------------------------
    async def update_profile(self, user_id: str, update_data: dict):
        fields = {}
        if update_data.get("name"):
            fields["name"] = update_data["name"]
        if "avatar" in update_data:
            fields["avatar"] = update_data["avatar"]

        if not fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="수정할 데이터가 없습니다."
            )

        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": fields}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )

        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return user

    # ------------------------------------------------------------
    # 비밀번호 변경 (로컬 계정만)
    # ------------------------------------------------------------
    async def change_password(self, user_id: str, current_password: str, new_password: str):
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        if user.get("provider") != "local":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="소셜 로그인 계정은 비밀번호를 변경할 수 없습니다."
            )

        if not pwd_context.verify(current_password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="현재 비밀번호가 올바르지 않습니다."
            )

        hashed_pw = pwd_context.hash(new_password)
        await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": hashed_pw}}
        )

        return {"success": True, "message": "비밀번호가 변경되었습니다."}

    # ------------------------------------------------------------
    # 계정 삭제 (비활성화)
    # ------------------------------------------------------------
    async def delete_account(self, user_id: str):
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"isActive": False}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        return {"success": True, "message": "계정이 비활성화되었습니다."}

    # ------------------------------------------------------------
    # 모든 사용자 목록 조회 (관리자 전용)
    # ------------------------------------------------------------
    async def get_all_users(self):
        users_cursor = users_collection.find({"isActive": True})
        users = []
        async for u in users_cursor:
            u["_id"] = str(u["_id"])
            u.pop("password", None)
            users.append(u)

        users.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return users

    # ------------------------------------------------------------
    # 사용자 유형 변경 (관리자 전용)
    # ------------------------------------------------------------
    async def change_user_type(self, user_id: str, new_user_type: str):
        if new_user_type not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 사용자 유형입니다."
            )

        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"userType": new_user_type}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return user


users_service = UsersService()