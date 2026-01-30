# app/controllers/auth_controller.py
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from app.services.auth_service import auth_service
from app.middleware.auth_middleware import is_authenticated
from app.schemas.auth_schema import RegisterRequest, LoginRequest


class AuthController:
    # 회원가입
    async def register(self, body: RegisterRequest):
        email = body.email
        password = body.password
        name = body.name

        if not email or not password or not name:
            raise HTTPException(status_code=400, detail="이메일, 비밀번호, 이름은 필수입니다.")
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="비밀번호는 최소 6자 이상이어야 합니다.")

        user = await auth_service.register_user(email=email, password=password, name=name)

        return JSONResponse(
            content={
                "success": True,
                "message": "회원가입이 완료되었습니다.",
                "data": {"user": user},
            },
            status_code=status.HTTP_201_CREATED,
        )

    # 로그인
    async def login(self, body: LoginRequest):
        email = body.email
        password = body.password

        user, access_token = await auth_service.authenticate_user(email, password)

        response = JSONResponse(
            content={
                "success": True,
                "message": "로그인되었습니다.",
                "data": {"user": user,
                         "access_token": access_token},
            }
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=False,  # HTTPS 환경이라면 True로
            max_age=60 * 60 * 24 * 7  # 7일
        )
        return response

    # 로그아웃
    async def logout(self, user: dict = is_authenticated):
        user_id = user.get("sub") or user.get("_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 사용자입니다.")

        await auth_service.logout_user(user_id)

        response = JSONResponse({"success": True, "message": "로그아웃되었습니다."})
        response.delete_cookie("access_token")
        return response

    # 현재 사용자 정보 조회
    async def get_current_user(self, user: dict = is_authenticated):
        user_data = await auth_service.get_current_user_info(user["_id"])
        return {"success": True, "data": {"user": user_data}}


auth_controller = AuthController()