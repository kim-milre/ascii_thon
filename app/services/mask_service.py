from bs4 import BeautifulSoup, NavigableString
from typing import Dict, Any, List

SKIP_TAGS = {"script", "style", "noscript", "meta", "head", "title"}

# =========================
# 유틸
# =========================
def _looks_like_html(text: str) -> bool:
    return "<" in text and ">" in text

def _iter_text_nodes(soup: BeautifulSoup):
    for el in soup.descendants:
        if isinstance(el, NavigableString):
            parent = el.parent.name.lower() if el.parent and el.parent.name else ""
            if parent in SKIP_TAGS:
                continue
            yield el


def _mask_span(span: str, label: str) -> str:
    label = (label or "").upper()

    if label == "EMAIL":
        return '<span class="mask-email">이메일</span>'

    if label in {"PHONE", "MOBILE", "TEL"}:
        return '<span class="mask-phone">전화번호</span>'

    if label in {"CREDIT_CARD", "CARD"}:
        return '<span class="mask-card">카드번호</span>'

    if label in {"RRN", "RESIDENT_ID", "주민번호"}:
        return '<span class="mask-rrn">주민번호</span>'

    if label == "NAME":
        return '<span class="mask-name">이름</span>'

    return '<span class="mask-unknown">개인정보</span>'

def _mask_text(text: str, targets: List[tuple]) -> str:
    masked = text
    for span, label in targets:
        if span in masked:
            masked = masked.replace(span, _mask_span(span, label))
    return masked

# =========================
# 엔트리포인트
# =========================
def mask_pii(content: str, pipeline_output: Dict[str, Any]) -> Dict[str, Any]:
    if not content:
        return {"masked_html": "", "masked_count": 0}

    per_items = (pipeline_output or {}).get("perItemResults") or []

    targets = []
    for r in per_items:
        if not isinstance(r, dict):
            continue

        if str(r.get("decision", "")).upper() != "MASK":
            continue

        f = r.get("finding")
        if not isinstance(f, dict):
            continue
        span = str(f.get("span", "")).strip()
        label = str(f.get("label") or "").strip()
        if span:
            targets.append((span, label))

    if not targets:
        return {"masked_html": content, "masked_count": 0}

    # ✅ TEXT 경로
    if not _looks_like_html(content):
        return {
            "masked_html": _mask_text(content, targets),
            "masked_count": len(targets)
        }
    
    soup = BeautifulSoup(content, "html.parser")
    masked_count = 0

    for node in _iter_text_nodes(soup):
        original = str(node)
        new_text = _mask_text(original, targets)

        if new_text != original:
            node.replace_with(BeautifulSoup(new_text, "html.parser"))
            masked_count += 1

    for r in per_items:
        if not isinstance(r, dict):
            continue
        f = r.get("finding")
        if not isinstance(f, dict):
            continue
        print("[MASK DEBUG]", f.get("label"), f.get("span"))
    

    return {
        "masked_html": str(soup),
        "masked_count": masked_count
    }