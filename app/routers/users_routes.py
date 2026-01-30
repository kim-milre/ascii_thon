from fastapi import APIRouter, Depends, Request
from app.controllers.users_controller import users_controller, PasswordUpdate
from app.middleware.auth_middleware import (
    is_authenticated,
    is_local_account,
    is_admin
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/profile")
async def get_profile(user=Depends(is_authenticated)):
    return await users_controller.get_profile(user)


@router.put("/profile")
async def update_profile(request: Request, user=Depends(is_authenticated)):
    return await users_controller.update_profile(request, user)


@router.put("/password")
async def change_password(payload: PasswordUpdate, user: dict = Depends(is_authenticated)):
    return await users_controller.change_password(payload, user)


# 계정 삭제
@router.delete("/account")
async def delete_account(user=Depends(is_authenticated)):
    return await users_controller.delete_account(user)


# 모든 사용자 목록 조회 (관리자 전용)
@router.get("/all")
async def get_all_users(admin=Depends(is_admin)):
    return await users_controller.get_all_users(admin)


# 사용자 유형 변경 (관리자 전용)
@router.put("/{userId}/type")
async def change_user_type(userId: str, request: Request, admin=Depends(is_admin)):
    return await users_controller.change_user_type(userId, request, admin)