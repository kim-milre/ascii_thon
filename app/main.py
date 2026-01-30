import os
import sys
import asyncio
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from app.config.database import db, analysis_collection
from app.config.database import db, ensure_policy_indexes, log_collections

# ── 0) .env 로드
load_dotenv()

# ── 1) Windows: Proactor 정책 강제 (Playwright/서브프로세스 안전)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ── 2) 내부 import (사이드이펙트 없는 것만)
from app.config.database import db, ensure_policy_indexes, log_collections  # <-- 중복 제거
from app.utils.file_utils import ensure_result_dir, short_hash, write_text, write_json, html_to_text
from app.middleware import error_middleware  # , notFound_middleware
from app.routers import analyze, sites, policies, documents, health, detect

# ── 3) FastAPI App

from app.routers import (
    analyze,
    sites,
    policies,
    documents,
    health,
    detect,
    auth_routes,
    users_routes,
)
from app.middleware import error_middleware, notFound_middleware

app = FastAPI(
    title="SDUCOSS Compliance Risk Analysis API",
    description="AI 기반 웹 컴플라이언스 리스크 분석 및 마스킹 서비스",
    version="1.0.0",
)

# ── 4) CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://0.0.0.0:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "https://sducoss-client.vercel.app",
        "https://sducoss.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print("❌ INTERNAL SERVER ERROR ❌")
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": str(e)})


# ── 5) 미들웨어
app.middleware("http")(error_middleware.handle_exceptions)
# app.middleware("http")(notFound_middleware.not_found_handler)

# ── 6) 라우터
app.include_router(health.router, prefix="/api/health", tags=["Health"])
# app.include_router(analyze.router)  # 필요 시 활성화
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(sites.router)
app.include_router(auth_routes.router)
app.include_router(users_routes.router)
app.include_router(detect.router, prefix="/api/detect", tags=["Detection"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

# ── 7) Playwright 설치/디버그 태스크는 startup에서만!
async def ensure_playwright_installed():
    """배포(리눅스)일 때만 크로미움 설치. 윈도우 개발 환경에선 스킵."""
    if sys.platform.startswith("linux"):
        path = "/opt/render/.cache/ms-playwright/chromium-1187/chrome-linux/chrome"
        if not os.path.exists(path):
            print("⚙️ Installing Playwright Chromium browser (linux)...")
            # --with-deps는 리눅스에서만 의미 있음
            os.system("playwright install --with-deps chromium")
        else:
            print("✅ Chromium already installed.")
    else:
        # 윈도우/맥 개발환경은 보통 'playwright install chromium' 한 번 수동 실행 권장
        print("ℹ️ Skipping Playwright auto-install on non-Linux dev environment.")

async def debug_db():
    print("✅ DB 이름:", db.name)
    collections = await db.list_collection_names()
    print("✅ collections in DB:", collections)
    docs = db["analysis_results"].find().limit(3)
    print("✅ 예시 문서들:")
    async for d in docs:
        print(" -", d.get("_id"), d.get("url"))

async def debug_one_doc():
    from app.config.database import analysis_collection
    doc = await analysis_collection.find_one()
    if doc:
        print("🔎 샘플 문서 _id:", doc.get("_id"), type(doc.get("_id")))

# ── 8) startup 이벤트에서만 모든 사이드이펙트 실행
@app.on_event("startup")
async def startup_event():
    print("🚀 FastAPI startup: initializing MongoDB indexes...")
    await ensure_policy_indexes()
    await log_collections()
    print("✅ MongoDB 초기화 및 인덱스 확인 완료.")

    # Playwright 설치 및 디버그 태스크는 여기서 스케줄
    await ensure_playwright_installed()
    asyncio.create_task(debug_db())
    asyncio.create_task(debug_one_doc())

# ── 9) 간단 루트/헬스
@app.get("/")
async def root():
    return {
        "service": "SDUCOSS Compliance API",
        "status": "running",
        "routes": [
            # "/api/analyze",
            "/api/sites",
            "/api/policies",
            "/api/documents",
            "/api/detect",  # 슬래시 빠진거 보정
        ],
    }

@app.get("/api/healthcheck")
async def healthcheck():
    return {"status": "ok", "service": "SDUCOSS"}


# ── 10) 개발 실행
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # 문자열 경로 대신 직접 app 전달도 가능: uvicorn.run(app, host=..., port=..., reload=False)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


# # === 임시용 코드
# # robots → crawl → detect를 한 번에 돌리고,
# # 결과를 app/services/result에 저장한 뒤 API 응답으로도 보여주는 엔드포인트
# @app.post("/api/run", tags=["Analyze"])
# async def run_once(req: RunRequest):
#     """
#     robots → crawl → detect 실행 후:
#       - 원본 HTML: app/services/result/page_<hash>_<ts>.html 저장
#       - 탐지 결과:  app/services/result/detect_<hash>_<ts>.json 저장
#     그리고 요약을 응답으로 반환
#     """
#     url = str(req.url or DEFAULT_URL)
#
#     # 1) robots.txt 체크
#     robots_txt = await fetch_robots_txt(url)  # :contentReference[oaicite:0]{index=0}
#     if robots_txt:
#         rules = parse_robots_txt(robots_txt)  # :contentReference[oaicite:1]{index=1}
#         path = urlparse(url).path or "/"
#         if not is_allowed(path, rules):       # :contentReference[oaicite:2]{index=2}
#             raise HTTPException(status_code=451, detail="Blocked by robots.txt")
#
#     # 2) 크롤링 (반환 타입을 유연하게 처리)
#     try:
#         crawl_ret = await crawl_and_save(url)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Crawl failed: {e}")
#
#     # 2-1) 반환 타입 흡수: (html, metadata) | dict | json path
#     html, metadata = "", {}
#     if isinstance(crawl_ret, tuple) and len(crawl_ret) == 2:
#         html, metadata = crawl_ret
#     elif isinstance(crawl_ret, dict):
#         # crawl_service가 dict로 넘길 때 키 후보들 케어
#         html = crawl_ret.get("html") or crawl_ret.get("a_div_html") or ""
#         metadata = crawl_ret.get("metadata") or {}
#     elif isinstance(crawl_ret, str) and os.path.isfile(crawl_ret):
#         # crawl_service가 파일 경로를 넘길 때
#         with open(crawl_ret, "r", encoding="utf-8") as f:
#             payload = json.load(f)
#         html = payload.get("html") or payload.get("a_div_html") or ""
#         metadata = payload.get("metadata") or {}
#     else:
#         raise HTTPException(status_code=500, detail="Unexpected crawl return type from crawl_service")
#
#     # 3) 탐지용 텍스트 생성 (HTML → 텍스트)
#     text_for_detect = _html_to_text(html)
#     if not text_for_detect:
#         raise HTTPException(status_code=422,
#                             detail="No analyzable text extracted from HTML (empty page or blocked by robots). Try another URL, e.g., https://example.com")
#
#     # 4) 위험 탐지 (Regex + spaCy NER)
#     findings = detect_risks(text_for_detect)       # :contentReference[oaicite:4]{index=4}
#
#     # 5) 파일 저장
#     result_dir = _ensure_result_dir()
#     stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     base = f"{_hash(url)}_{stamp}"
#
#     html_path = os.path.join(result_dir, f"page_{base}.html")
#     _write_text(html_path, html or "")
#
#     detect_path = os.path.join(result_dir, f"detect_{base}.json")
#     _write_json(detect_path, {
#         "url": url,
#         "detected_at": datetime.now().isoformat(),
#         "count": findings.get("count", 0),
#         "results": findings.get("results", []),
#         "meta": {
#             "title": (metadata or {}).get("title"),
#         }
#     })
#
#     # 6) API 응답 (요약 + 저장 경로 반환)
#     return {
#         "ok": True,
#         "url": url,
#         "robots_checked": bool(robots_txt),
#         "count": findings.get("count", 0),
#         "saved": {
#             "html": html_path,
#             "detect_json": detect_path
#         }
#     }
#
# # ===================
#
#
