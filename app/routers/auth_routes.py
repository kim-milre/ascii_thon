from fastapi import APIRouter, Depends, Request
from app.controllers.auth_controller import auth_controller
from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.middleware.auth_middleware import is_authenticated, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ==================== 로컬 인증 ====================

@router.post("/register")
async def register(body: RegisterRequest):
    print("REGISTER BODY:", body)
    return await auth_controller.register(body)

@router.post("/login")
async def login(body: LoginRequest):
    return await auth_controller.login(body)

@router.post("/logout")
async def logout(current_user=Depends(is_authenticated)):
    return await auth_controller.logout(current_user)

@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return await auth_controller.get_current_user(current_user)