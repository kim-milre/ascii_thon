from fastapi import HTTPException, status, Depends, Request, Body
from pydantic import BaseModel, StringConstraints, Field
from typing import Annotated
from app.services.users_service import users_service
from app.middleware.auth_middleware import is_authenticated, is_admin
from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password_pattern = r'^[\w!@#$%^&*()\-_=+{}$begin:math:display$$end:math:display$|;:<>,.?/~`]+$'
PasswordStr = Annotated[
    str,
    StringConstraints(min_length=8, max_length=64, pattern=password_pattern)
]

class PasswordUpdate(BaseModel):
    currentPassword: PasswordStr = Field(..., description="현재 비밀번호 (8~64자)")
    newPassword: PasswordStr = Field(..., description="새 비밀번호 (8~64자)")


class UsersController:

    # ------------------------------------------------------------
    # 내 프로필 조회 (GET /api/users/profile)
    # ------------------------------------------------------------
    async def get_profile(self, user: dict = Depends(is_authenticated)):
        user_data = await users_service.get_profile(user["_id"])
        return {
            "success": True,
            "data": {"user": user_data},
        }

    # ------------------------------------------------------------
    # 내 프로필 수정 (PUT /api/users/profile)
    # ------------------------------------------------------------
    async def update_profile(self, request: Request, user: dict = Depends(is_authenticated)):
        body = await request.json()
        name = body.get("name")
        avatar = body.get("avatar")

        updated_user = await users_service.update_profile(str(user.get("_id")), {"name": name, "avatar": avatar})

        return {
            "success": True,
            "message": "프로필이 수정되었습니다.",
            "data": {"user": updated_user},
        }

    # ------------------------------------------------------------
    # 비밀번호 변경 (PUT /api/users/password)
    # ------------------------------------------------------------
    async def change_password(
        self,
        payload: PasswordUpdate = Body(...),
        user: dict = Depends(is_authenticated)
    ):
        # [1] 요청 파라미터 자동 검증 (FastAPI + Pydantic)
        current_password = payload.currentPassword
        new_password = payload.newPassword

        # [2] 비밀번호 동일성 검증
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호와 새 비밀번호는 달라야 합니다."
            )

        # [3] 추가 정책: 공백 금지
        if " " in new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비밀번호에 공백은 사용할 수 없습니다."
            )

        # [4] 보안 수준 검사 (대문자, 소문자, 숫자, 특수문자 조합)
        if not re.search(r'[A-Z]', new_password) or not re.search(r'[a-z]', new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비밀번호에는 대소문자가 모두 포함되어야 합니다."
            )
        if not re.search(r'[0-9]', new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비밀번호에는 숫자가 포함되어야 합니다."
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비밀번호에는 특수문자가 포함되어야 합니다."
            )
        await users_service.change_password(user["_id"], current_password, new_password)

        return {
            "success": True,
            "message": "비밀번호가 변경되었습니다.",
        }

    # ------------------------------------------------------------
    # 계정 삭제 (DELETE /api/users/account)
    # ------------------------------------------------------------
    async def delete_account(self, user: dict = Depends(is_authenticated)):
        await users_service.delete_account(user["_id"])
        # FastAPI에서는 세션 기반 로그아웃이 없으므로 단순 성공 응답
        return {
            "success": True,
            "message": "계정이 삭제되었습니다.",
        }

    # ------------------------------------------------------------
    # 모든 사용자 목록 조회 (GET /api/users/all) - 관리자 전용
    # ------------------------------------------------------------
    async def get_all_users(self, admin: dict = Depends(is_admin)):
        users = await users_service.get_all_users()
        return {
            "success": True,
            "data": {"users": users},
        }

    # ------------------------------------------------------------
    # 사용자 유형 변경 (PUT /api/users/{userId}/type) - 관리자 전용
    # ------------------------------------------------------------
    async def change_user_type(self, userId: str, request: Request, admin: dict = Depends(is_admin)):
        body = await request.json()
        user_type = body.get("userType")

        if not user_type or user_type not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효한 사용자 유형을 입력해주세요. (user 또는 admin)"
            )

        user = await users_service.change_user_type(userId, user_type)

        return {
            "success": True,
            "message": "사용자 유형이 변경되었습니다.",
            "data": {"user": user},
        }


users_controller = UsersController()