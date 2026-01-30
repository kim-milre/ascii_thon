import os
import re
import spacy
from typing import Dict, List, Any, Tuple, Optional
from bs4 import BeautifulSoup
from app.services.llm_name_detect import detect_names_with_openai

# =========================
# spaCy 로드
# =========================
try:
    nlp = spacy.load("ko_core_news_sm")
    print("✅ spaCy ko_core_news_sm 로드")
except Exception as e:
    print("⚠️ spaCy 로드 실패, blank 사용:", e)
    nlp = spacy.blank("xx")

# =========================
# OpenAI (보강 탐지용, 선택)
# =========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client 활성화")
    except Exception:
        _openai_client = None


# =========================
# 정규식 패턴
# =========================
EMAIL_PATTERN = r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b"

PHONE_PATTERN = r"""
(?:
  (?:\+?82[-\s]?)?(?:0)?
  (?:
    10|11|16|17|18|19
    |2
    |3[1-3]|4[1-4]|5[1-5]|6[1-4]
    |70
  )
  [-\s.]?
  \d{3,4}
  [-\s.]?
  \d{4}
)
"""

RESIDENT_ID_PATTERN = r"\b\d{6}-\d{7}\b"

PHONE_CONTEXT_WORDS = r"(전화|연락|mobile|tel|문의|고객센터|대표번호|fax)"

COPYRIGHT_PATTERNS = {
    "COPYRIGHT_NOTICE": r"(©\s?\d{4}[^<\n]{0,40})|(All rights reserved|무단 전재|무단전재)",
}

UNFAIR_PATTERNS = {
    "DISCLAIMER": r"(당사는 어떠한 책임도 지지 않습니다|면책 조항|면책조항)",
    "FORCED_AGREEMENT": r"(동의하지 않으면 서비스를 이용할 수 없습니다)",
}


# =========================
# 유틸
# =========================
def _normalize(text: str) -> str:
    return (
        (text or "")
        .replace("\u200b", "")
        .replace("\u00a0", " ")
        .replace("\ufeff", "")
    )

def _html_to_text(html_or_text: str) -> str:
    if "<" in html_or_text and ">" in html_or_text:
        soup = BeautifulSoup(html_or_text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(" ", strip=True)
    return html_or_text

def _digits_only(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def _finditer(pattern: str, text: str):
    return re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE)


# =========================
# 스코어링
# =========================
def _score_email(span: str) -> float:
    return 0.9 if "@" in span else 0.6

def _score_phone(span: str, context: str) -> Tuple[float, Optional[str]]:
    digits = _digits_only(span)
    ctx_boost = bool(re.search(PHONE_CONTEXT_WORDS, context))
    length_ok = 8 <= len(digits) <= 12

    if not length_ok:
        return 0.0, None

    # 학번/ID 필터
    if re.match(r"^20\d{6,8}$", digits):
        return 0.0, None

    conf = 0.75 + (0.1 if ctx_boost else 0.0)
    return min(conf, 0.95), "PHONE"


# =========================
# OpenAI 보강 탐지
# =========================
def _openai_extra_pii(text: str) -> List[Dict[str, Any]]:
    if not _openai_client:
        return []

    system = """
너는 개인정보 탐지기다.
다음 조건을 반드시 지켜라.

- 실제 사람 이름만 찾는다
- 일반 명사, 동사, 형용사는 절대 포함하지 않는다
- 이름은 원문에 등장한 span 그대로 반환한다
- 출력 JSON 형식은 반드시 아래를 따른다

{
  "items": [
    {
      "type": "PII",
      "label": "NAME",
      "span": "문자열"
    }
  ]
}
"""

    try:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text[:6000]},
            ],
            max_tokens=700,
        )
        import json
        data = json.loads(resp.choices[0].message.content)
        return data.get("items", [])
    except Exception:
        return []


# =========================
# 메인 함수
# =========================
def detect_risks(html_or_text: str, use_openai: bool = False) -> Dict[str, Any]:
    print("🔥 detect_risks CALLED, use_openai =", use_openai)
    text = _normalize(_html_to_text(html_or_text))

    findings: Dict[str, List[Dict[str, Any]]] = {
        "pii": [],
        "copyright": [],
        "unfair": [],
        "entity": [],
    }

    for m in re.finditer(r"\b(?:\d{4}[- ]?){3}\d{4}\b", text):
        findings["pii"].append({
            "label": "CREDIT_CARD",
            "span": m.group(),
            "confidence": 0.95
        })

    # ---------- EMAIL ----------
    for m in _finditer(EMAIL_PATTERN, text):
        findings["pii"].append({
            "type": "PII",
            "label": "EMAIL",
            "span": m.group(),
            "start": m.start(),
            "end": m.end(),
            "confidence": _score_email(m.group()),
            "method": "regex",
        })

    # ---------- PHONE ----------
    for m in _finditer(PHONE_PATTERN, text):
        span = m.group()
        ctx = text[max(0, m.start()-20): m.end()+20]
        conf, label = _score_phone(span, ctx)
        if label:
            findings["pii"].append({
                "type": "PII",
                "label": label,
                "span": span,
                "start": m.start(),
                "end": m.end(),
                "confidence": conf,
                "method": "regex",
            })

    # ---------- RESIDENT ID ----------
    for m in _finditer(RESIDENT_ID_PATTERN, text):
        findings["pii"].append({
            "type": "PII",
            "label": "RESIDENT_ID",
            "span": m.group(),
            "start": m.start(),
            "end": m.end(),
            "confidence": 0.98,
            "method": "regex",
        })


    # ---------- COPYRIGHT ----------
    for lab, pat in COPYRIGHT_PATTERNS.items():
        for m in _finditer(pat, text):
            findings["copyright"].append({
                "type": "COPYRIGHT",
                "label": lab,
                "span": m.group(),
                "start": m.start(),
                "end": m.end(),
                "confidence": 0.7,
                "method": "regex",
            })

    # ---------- UNFAIR ----------
    for lab, pat in UNFAIR_PATTERNS.items():
        for m in _finditer(pat, text):
            findings["unfair"].append({
                "type": "UNFAIR",
                "label": lab,
                "span": m.group(),
                "start": m.start(),
                "end": m.end(),
                "confidence": 0.7,
                "method": "regex",
            })

# ---------- OpenAI 보강 ----------
    if use_openai:
        openai_names = detect_names_with_openai(text)

        # 기존 NAME span과 중복 제거
        existing_spans = {r["span"] for r in findings["pii"] if r.get("label") == "NAME"}

        for r in openai_names:
            span = r.get("span")
            if not span:
                continue

            if span in existing_spans:
                continue

            findings["pii"].append({
                "type": "PII",
                "label": "NAME",
                "span": span,
                "start": None,
                "end": None,
                "confidence": 0.85,
                "method": "openai",
            })

            # ---------- meta ----------
            findings["meta"] = {
                "pii_count": len(findings["pii"]),
                "used_openai": bool(use_openai and _openai_client),
                "text_length": len(text),
            }
            print("🧪 DETECT PII:", findings["pii"])

    print("🧪 FINAL PII FINDINGS:")
    for f in findings["pii"]:
        print(f)

    return findings

