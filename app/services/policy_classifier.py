from typing import Dict

LABEL_MAP = {
    "privacy_policy": "개인정보처리방침",
    "tos": "이용약관",
    "cookie_policy": "쿠키정책",
    "location_terms": "위치정보 약관",
    "other": "기타 정책"
}

def classify_summary(policy_doc: Dict) -> Dict:
    # 규칙 기반 요약 태그, 필요시 LLM 분류로 교체 가능
    t = policy_doc.get("policy_type", "other")
    title = LABEL_MAP.get(t, "정책")
    length = len(policy_doc.get("content", ""))
    approx_sections = max(1, length // 1500)
    return {
        "policy_type_human": title,
        "section_count_est": approx_sections
    }