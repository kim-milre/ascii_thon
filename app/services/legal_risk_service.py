# app/services/legal_risk_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


def _html_text_len(html: str) -> int:
    if not html:
        return 0
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return len(soup.get_text(" ", strip=True))


def _has_main_article(html: str) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(html, "html.parser")
    return bool(soup.select_one("article") or soup.select_one("main"))


def _looks_like_article(html: str) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(html, "html.parser")
    # 기사 페이지에서 흔한 구조적 단서들
    return bool(
        soup.select_one("meta[property='og:type'][content*='article']")
        or soup.select_one("meta[name='article:author']")
        or soup.select_one("meta[property='article:author']")
        or soup.select_one("time")
        or soup.select_one(".article")
        or soup.select_one(".news")
    )


def _detect_block_page(html: str) -> bool:
    if not html:
        return False
    h = html.lower()
    # 네가 실제로 본 네이버 쇼핑 차단 페이지 유형 포함
    patterns = [
        "잠시 후 다시 확인해주세요",
        "접근이 제한",
        "서비스와 연결할 수 없습니다",
        "비정상적인 접근",
        "captcha",
        "robot check",
        "are you a robot",
        "access denied",
        "forbidden",
        "too many requests",
    ]
    return any(p.lower() in h for p in patterns)


def _extract_terms_signals(policies: Any) -> Dict[str, Any]:
    """
    policies는 fetch_and_store_policies(url) 결과가 list일 수도 있고 dict일 수도 있음
    여기서는 텍스트를 모아 키워드 기반으로 신호를 만든다
    """
    texts: List[str] = []

    if isinstance(policies, list):
        for p in policies:
            if isinstance(p, dict):
                texts.append(_safe_str(p.get("content") or p.get("text") or p.get("body")))
            else:
                texts.append(_safe_str(p))
    elif isinstance(policies, dict):
        texts.append(_safe_str(policies.get("content") or policies.get("text") or policies.get("body")))
    else:
        texts.append(_safe_str(policies))

    joined = "\n".join([t for t in texts if t]).lower()

    def has_any(keys: List[str]) -> bool:
        return any(k.lower() in joined for k in keys)

    return {
        "has_terms": bool(joined.strip()),
        "anti_scraping": has_any(["크롤링 금지", "스크래핑 금지", "자동 수집 금지", "자동화", "봇", "bot", "scraping", "crawling"]),
        "anti_ai_training": has_any(["ai 학습", "학습 목적", "training", "llm", "rag", "retrieval-augmented", "gptbot", "google-extended"]),
        "redistribution": has_any(["재배포 금지", "무단 전재", "전재", "복제 금지", "저작권", "redistribution", "reproduce", "copy"]),
    }


def build_legal_risks(
    *,
    url: str,
    robots_txt: Optional[str],
    robots_blocked: bool,
    ai_prohibited: bool,
    html: Optional[str],
    metadata: Optional[Dict[str, Any]],
    policies: Any,
    findings: Optional[Dict[str, Any]] = None,
    per_item_results: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:

    parsed = urlparse(url)
    domain = parsed.netloc

    legal_risks: List[Dict[str, Any]] = []  # ✅ 반드시 필요
    terms_sig = _extract_terms_signals(policies)

    # ✅ [BLOCKED 전용] robots.txt / AI 접근 금지 → 즉시 리턴
    if robots_blocked or ai_prohibited:
        return [{
            "id": "ROBOTS_TXT_BLOCK",
            "type": "access_control",
            "level": "HIGH",
            "title": "robots.txt 기반 자동화 접근 차단",
            "law": "부정경쟁방지법 제2조 제1호 (차)",
            "summary": (
                f"{domain}은 robots.txt 또는 접근 정책을 통해 "
                "자동화된 크롤링 및 AI/RAG 목적 접근을 명시적으로 제한하고 있습니다."
            ),
            "reason": (
                "접근 제한을 인지하고도 수집·분석을 수행할 경우 "
                "타인의 성과를 공정한 상거래 관행에 반하여 무단으로 이용하는 행위로 "
                "해석될 소지가 있습니다."
            ),
            "legal_basis": [
                "부정경쟁방지 및 영업비밀보호에 관한 법률 제2조 제1호 (차)목",
                "서비스 제공자의 robots.txt 및 접근 통제 정책",
            ],
            "signals": {
                "robots_txt_present": bool(robots_txt),
                "robots_blocked": bool(robots_blocked),
                "ai_prohibited": bool(ai_prohibited),
            }
        }]

    # 2) copyright/database_right: 저장/재배포 위험 신호
    html_len = _html_text_len(html or "")
    has_article_like = _has_main_article(html or "") or _looks_like_article(html or "")

    store_full_html = bool((html or "").strip())
    store_masked_html = True  # 너 final_doc에 masked_html을 저장하고 있으니 기본 True

    copyright_level = None
    copyright_reasons: List[str] = []

    # 기사 전문 저장/재배포 쪽은 "저장량 + 기사스러운 구조"로 신호를 만든다
    if store_full_html and store_masked_html and html_len >= 3000 and has_article_like:
        copyright_level = "HIGH"
        copyright_reasons.append("본문 텍스트가 길고 기사 또는 콘텐츠 전문에 가까운 구조가 감지됨")
        copyright_reasons.append("원문 또는 준원문에 준하는 형태로 저장될 경우 재배포·전재로 해석될 소지가 있음")
    elif store_full_html and html_len >= 1500:
        copyright_level = "MEDIUM"
        copyright_reasons.append("일정량 이상의 콘텐츠를 저장하는 구조가 확인됨")
    elif store_full_html and html_len > 0:
        copyright_level = "LOW"
        copyright_reasons.append("콘텐츠를 저장하는 구조가 존재함")

    if terms_sig["redistribution"]:
        # 약관이 재배포 금지를 명시하면 한 단계 상향
        if copyright_level == "LOW":
            copyright_level = "MEDIUM"
        elif copyright_level == "MEDIUM":
            copyright_level = "HIGH"
        copyright_reasons.append("약관에서 무단 전재·복제·재배포 금지 취지가 확인됨")

    if copyright_level:
        legal_risks.append({
            "type": "copyright",
            "level": copyright_level,
            "law": "저작권법 / 데이터베이스 제작자의 권리",
            "reason": f"{domain}의 콘텐츠를 일정량 이상 저장·가공·재이용하는 구조는 저작권 또는 데이터베이스 제작자의 권리 관점에서 검토가 필요함\n" +
                      " | ".join(copyright_reasons),
            "signals": {
                "text_length": html_len,
                "article_like": bool(has_article_like),
                "stores_full_html": bool(store_full_html),
                "stores_masked_html": bool(store_masked_html),
                "terms_redistribution_notice": bool(terms_sig["redistribution"]),
            }
        })

    # 3) network_abuse: 서비스 운영 방해/비정상 트래픽 가능성
    block_page = _detect_block_page(html or "")
    uses_headless = False
    if isinstance(metadata, dict):
        # crawl metadata에 브라우저 사용 여부 같은 키가 있으면 여기에서 연결
        uses_headless = bool(metadata.get("used_playwright") or metadata.get("playwright") or metadata.get("rendered"))

    # 네트워크 남용 리스크는 "차단 페이지/비정상 응답 + 자동화 특성" 기반
    if block_page or uses_headless:
        reasons: List[str] = []
        if block_page:
            reasons.append("차단 또는 제한 페이지로 보이는 응답이 감지됨")
        if uses_headless:
            reasons.append("동적 렌더링을 위한 자동화 브라우저 접근이 사용됨")

        level = "MEDIUM"
        if block_page and uses_headless:
            level = "HIGH"

        legal_risks.append({
            "type": "network_abuse",
            "level": level,
            "law": "정보통신망법 서비스 보호 규정 관점",
            "reason": f"{domain}에 대한 자동화 접근이 비정상 트래픽 또는 서비스 운영 방해로 해석될 수 있어 접근 빈도·동작 방식에 대한 통제가 필요함\n" +
                      " | ".join(reasons),
            "signals": {
                "block_page_detected": bool(block_page),
                "uses_headless_browser": bool(uses_headless),
            }
        })

    # 4) privacy_context: 공개 정보라도 맥락 결합 위험
    # per_item_results에서 NAME/EMAIL/PHONE 같이 식별자 다건 + 콘텐츠 맥락이 길면 상승
    context_level = None
    context_reasons: List[str] = []

    pii_count = 0
    if isinstance(findings, dict) and isinstance(findings.get("pii"), list):
        pii_count = len(findings.get("pii") or [])
    if isinstance(per_item_results, list):
        pii_count = max(pii_count, sum(1 for r in per_item_results if str(r.get("decision", "")).upper() in ["REVIEW", "MASK"]))

    if pii_count >= 3 and html_len >= 1200:
        context_level = "MEDIUM"
        context_reasons.append("식별 가능 정보가 다수 탐지되었고 본문 길이가 길어 맥락 결합 가능성이 큼")
    if pii_count >= 5 and html_len >= 2000:
        context_level = "HIGH"
        context_reasons.append("다수의 식별자와 장문 맥락이 결합될 경우 개인 식별 가능성이 상승함")

    if context_level:
        legal_risks.append({
            "type": "privacy_context",
            "level": context_level,
            "law": "개인정보 보호법 맥락 결합 리스크 관점",
            "reason": f"공개된 정보라도 맥락과 결합되면 개인 식별 가능성이 상승하여 추가 검토가 필요함\n" +
                      " | ".join(context_reasons),
            "signals": {
                "pii_count": int(pii_count),
                "text_length": int(html_len),
            }
        })

    return legal_risks