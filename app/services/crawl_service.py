# app/services/crawl_service.py
import asyncio
import os
import hashlib
import logging
from datetime import datetime
from bs4 import BeautifulSoup, Comment
from crawl4ai import AsyncWebCrawler
from app.config.database import analysis_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _ensure_result_dir() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, "result")  # ← 규칙: result 폴더
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

def _extract_a_div(html: str) -> dict:
    """HTML에서 <a>, <div>만 모아 부분 HTML/텍스트 생성"""
    soup = BeautifulSoup(html or "", "html.parser")
    tags = soup.select("a, div")
    partial_html = "".join(str(t) for t in tags)
    partial_text = " ".join(
        t.get_text(" ", strip=True) for t in tags if t.get_text(strip=True)
    )
    return {"partial_html": partial_html, "partial_text": partial_text}

def _extract_body_only(html: str):
    """
    <body> 내부만 HTML로 추려서 반환.
    - <script>/<style>/<noscript> 제거
    - body가 없으면 원문 그대로 반환(안전 fallback)
    """
    try:
        soup = BeautifulSoup(html or "", "lxml")  # lxml이 있으면 더 정확
    except Exception:
        soup = BeautifulSoup(html or "", "html.parser")

    body = soup.body
    if not body:
        return {"body_html": html, "body_text": soup.get_text(" ", strip=True)}

    # body를 기준으로만 작업
    # 1) script/style/noscript 제거
    for tag in body(["script", "style", "noscript"]):
        tag.decompose()
    # 2) 주석 제거
    for c in body.find_all(text=lambda t: isinstance(t, Comment)):
        c.extract()

    # 3) body 내부만(outer <body> 태그 없이) 직렬화
    body_html = "".join(str(child) for child in body.contents)
    body_text = body.get_text(" ", strip=True)

    return {"body_html": body_html, "body_text": body_text}

async def crawl_and_save(url: str) -> tuple[str, dict]:
    logger.info(f"🌐 Start crawling → {url}")
    hash_name = hashlib.md5(url.encode()).hexdigest()[:8]
    ts = datetime.now().isoformat()

    try:
        async with AsyncWebCrawler(
            timeout=15000,
            wait_until="domcontentloaded",
            headless=True,
            browser_type="chromium",
        ) as crawler:
            try:
                result = await asyncio.wait_for(
                    crawler.arun(url=url),
                    timeout=20,   # 🔥 Render-safe hard stop
                )
            except asyncio.TimeoutError:
                logger.error(f"❌ Crawl hard timeout (Render): {url}")
                raise RuntimeError("Crawl timeout")
            print(f"🌐 크롤링 완료: {url}")

        html = getattr(result, "html", "") or ""
        md = getattr(result, "markdown", "") or ""
        links = getattr(result, "links", None)
        metadata = getattr(result, "metadata", {}) or {}
        title = metadata.get("title") if metadata else None

        extracted = _extract_a_div(html)

        body = _extract_body_only(html)
        body_html = body["body_html"]
        body_text = body["body_text"]

        site_doc = {
            "url": url,
            "hash": hash_name,
            "title": metadata.get("title") if metadata else None,
            "timestamp": ts,
            "html_length": len(html),
            "html_length_body": len(body_html),
            "markdown_preview": md[:300],
            "links": links,
            "html_body": body_html,
            "text_body": body_text,
            "a_div_html": extracted["partial_html"],
            "a_div_text": extracted["partial_text"],
            "metadata": metadata,
            "status": "crawled",
        }

        existing = await analysis_collection.find_one({"url": url})
        if existing:
            await analysis_collection.update_one({"_id": existing["_id"]}, {"$set": site_doc})
            logger.info(f"♻️ Updated existing entry for URL: {url}")
        else:
            result = await analysis_collection.insert_one(site_doc)
            logger.info(f"✅ Crawled & saved to MongoDB: {url} ({result.inserted_id})")



        return body_html, metadata

    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")
        logger.error(f"❌ Failed to crawl {url}: {e}")
        raise e


if __name__ == "__main__":
    asyncio.run(crawl_and_save("https://scholar.google.com/scholar?hl=ko&q=한국"))