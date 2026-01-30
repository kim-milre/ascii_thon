# app/middleware/notFound_middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse


async def not_found_handler(request: Request, call_next):
    response = await call_next(request)

    if response.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"error": {"message": "Resource not found"}}
        )
    return response