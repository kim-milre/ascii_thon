import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.middleware("http")
async def log_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logging.exception(f"🔥 Unhandled exception: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})