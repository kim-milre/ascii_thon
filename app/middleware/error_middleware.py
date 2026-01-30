# app/middleware/error_middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback
import os

async def handle_exceptions(request: Request, call_next):
    try:
        response = await call_next(request)
        return response

    except Exception as exc:
        status_code = getattr(exc, "status_code", 500)
        message = getattr(exc, "detail", str(exc))

        error_response = {
            "error": {
                "message": message or "Internal Server Error"
            }
        }


        if os.getenv("ENV", "development") != "production":
            error_response["error"]["stack"] = traceback.format_exc()

        return JSONResponse(status_code=status_code, content=error_response)