import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from app.config.database import policies_collection, policy_vectors_collection
from crawl4ai import AsyncWebCrawler
from openai import OpenAI
import os

CANDIDATE_KEYWORDS = [
    "이용약관", "개인정보처리방침", "개인정보 보호정책", "위치정보", "쿠키정책", "제3자 제공", "privacy", "terms", "policy"
]

def is_policy_like(text: str) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in CANDIDATE_KEYWORDS)

def pick_policy_type(title_or_url: str) -> str:
    s = title_or_url.lower()
    if "privacy" in s or "개인정보" in s:
        return "privacy_policy"
    if "terms" in s or "이용약관" in s:
        return "tos"
    if "location" in s or "위치정보" in s:
        return "location_terms"
    if "cookie" in s or "쿠키" in s:
        return "cookie_policy"
    return "other"

async def discover_policy_links(base_url: str) -> List[Tuple[str, str]]:
    async with AsyncWebCrawler() as crawler:
        r = await crawler.arun(base_url)
        links = []
        for a in r.links:
            if isinstance(a, str):
                href = a
                text = a
            else:
                text = getattr(a, "text", "") or ""
                href = getattr(a, "href", "") or ""

            if not href:
                continue

            if is_policy_like(text) or is_policy_like(href):
                abs_url = urljoin(base_url, href)
                links.append((text.strip() or href, abs_url))
        # dedupe by normalized URL
        seen = set()
        uniq = []
        for title, u in links:
            nu = urlparse(u)._replace(fragment="", query="").geturl()
            if nu not in seen:
                seen.add(nu)
                uniq.append((title, nu))
        return uniq

async def fetch_and_store_policies(site_url: str) -> List[Dict]:
    links = await discover_policy_links(site_url)
    results = []
    async with AsyncWebCrawler() as crawler:
        for title, link in links:
            r = await crawler.arun(link)
            text = r.markdown or r.cleaned_text or ""
            if len(text) < 200:
                continue
            doc = {
                "site": site_url,
                "title": title,
                "url": link,
                "policy_type": pick_policy_type(title + " " + link),
                "content": text,
            }
            # upsert
            await policies_collection.update_one(
                {"site": site_url, "url": link},
                {"$set": doc},
                upsert=True,
            )
            results.append(doc)
    return results

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def index_policies(site_url: str, policies: list):
    """
    약관(policy) 문서들을 OpenAI 임베딩으로 변환 후 MongoDB에 저장.
    """
    if not policies:
        print("⚠️ index_policies: 빈 약관 목록, 인덱싱 생략.")
        return

    print(f"🧩 index_policies: {len(policies)}개 약관 벡터화 시작")

    for policy in policies:
        try:
            if isinstance(policy, str):
                policy_doc = {
                    "site": site_url,
                    "policy_type": "unknown",
                    "content": policy,
                    "url": site_url
                }
            elif isinstance(policy, dict):
                policy_doc = policy
            else:
                print(f"⚠️ 예기치 않은 policy 타입: {type(policy)} → 건너뜀")
                continue

            text = policy_doc.get("content") or ""
            if not text or len(text) < 50:
                print(f"⚠️ 약관 텍스트가 비어 있음 또는 너무 짧음 ({policy_doc.get('url', '')})")
                continue

            embedding_resp = client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            embedding_vector = embedding_resp.data[0].embedding

            doc = {
                "site": site_url,
                "url": policy_doc.get("url", site_url),
                "policy_type": policy_doc.get("policy_type", "unknown"),
                "title": policy_doc.get("title", ""),
                "content": text,
                "vector": embedding_vector,
            }

            await policy_vectors_collection.update_one(
                {"site": site_url, "url": policy_doc.get("url", site_url)},
                {"$set": doc},
                upsert=True
            )

        except Exception as e:
            print(f"❌ index_policies 오류: {e}")
            continue

    print("✅ index_policies 완료")