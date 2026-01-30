
import os
import json
from typing import Dict, Any
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """당신은 웹사이트의 법적 리스크를 평가하는 전문가 AI입니다.
입력으로 제공된 탐지 결과(findings)와 관련 법령·약관 근거(evidences)를 기반으로
해당 웹페이지가 개인정보 보호법·저작권법·부정경쟁방지법 등을 위반할 가능성을 판단하세요.

판단 기준:
- PASS: 위법 가능성 거의 없음
- REVIEW: 일부 조항이 모호하거나 검토 필요
- MASK: 개인정보나 민감 정보 포함 가능성 높음

다음 JSON 형식으로만 출력하세요:
{
  "decision": "PASS" | "REVIEW" | "MASK",
  "score": 0~100,
  "reason": "간단한 근거 설명",
  "law_evidence": [관련 법령 근거 요약],
  "site_policy_evidence": [약관 근거 요약]
}
"""

def _summarize_findings(findings: dict) -> str:
    if not findings:
        return "탐지된 리스크 없음."
    summary = []
    if isinstance(findings, dict):
        for cat, vals in findings.items():
            if isinstance(vals, list):
                for v in vals:
                    if isinstance(v, dict):
                        label = v.get("label", "")
                        span = v.get("span", "")
                        if span:
                            summary.append(f"[{cat}:{label}] {span}")
    elif isinstance(findings, list):
        for v in findings:
            if isinstance(v, dict):
                cat = v.get("type", "")
                label = v.get("label", "")
                span = v.get("span", "")
                if span:
                    summary.append(f"[{cat}:{label}] {span}")

    return "\n".join(summary[:20]) or "탐지된 리스크 없음."

def _summarize_evidences(evidences: list) -> str:
    if not evidences:
        return "법령 또는 약관 근거 없음."
    summary = []
    for e in evidences:
        src = e.get("source_type", "unknown")
        txt = e.get("text", "")
        summary.append(f"[{src}] {txt[:300]}")
    return "\n".join(summary[:10])

def _rule_based_fallback(findings: dict, evidences: list) -> Dict[str, Any]:
    """LLM 실패 시 사용할 기본 규칙 기반 판단"""
    pii_cnt = len(findings.get("pii", [])) if isinstance(findings.get("pii"), list) else 0
    has_sensitive = any(
        (f.get("label") in ("email", "phone"))
        for f in findings.get("pii", [])
    ) if isinstance(findings.get("pii"), list) else False

    base_score = 30 + min(70, pii_cnt * 8)
    if has_sensitive:
        base_score += 10

    decision = "PASS" if base_score < 45 else ("REVIEW" if base_score < 75 else "MASK")
    result = {
        "decision": decision,
        "score": round(base_score, 1),
        "reason": "규칙 기반 평가 결과",
        "law_evidence": [e for e in evidences if e.get("source_type") == "law"][:2],
        "site_policy_evidence": [e for e in evidences if e.get("source_type") == "site_policy"][:2],
    }
    print(f"⚙️ 규칙 기반 판단 실행: {result['decision']} ({result['score']})")
    return result

def judge_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    findings = payload.get("findings")

    if not isinstance(findings, dict):
        findings = {"pii": []}

    for k, v in list(findings.items()):
        if not isinstance(v, list):
            findings[k] = []

    evidences = payload.get("evidences", [])
    if not isinstance(evidences, list):
        evidences = []

    # 1️⃣ 요약 생성
    findings_summary = _summarize_findings(findings)
    evidence_summary = _summarize_evidences(evidences)

    # 2️⃣ LLM 프롬프트 구성
    prompt = f"""
다음은 웹사이트 분석 결과입니다.

[탐지 결과]
{findings_summary}

[법령 및 약관 근거]
{evidence_summary}

이 정보를 기반으로 PASS / REVIEW / MASK 중 하나를 선택하고, JSON 형식으로 판단 결과를 출력하세요.
"""

    # 3️⃣ LLM 호출
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600
        )
        raw = response.choices[0].message.content

        # 안전 JSON 파싱
        if isinstance(raw, dict):
            result = raw
        else:
            try:
                result = json.loads(raw)
            except Exception:
                print("⚠️ JSON 파싱 실패, 문자열 그대로 사용")
                result = {"reason": str(raw)}

        # dict 보정 (여기서 str.get 에러 방지)
        if not isinstance(result, dict):
            result = {"decision": "REVIEW", "score": 50, "reason": "결과 형식 오류"}

        # 기본값 보정
        result.setdefault("decision", "REVIEW")
        result.setdefault("score", 50)
        result.setdefault("reason", "AI 판단 근거 부족")
        result.setdefault("law_evidence", [])
        result.setdefault("site_policy_evidence", [])

        print(f"✅ LLM 판단 완료: {result['decision']} ({result['score']})")
        return result

    except Exception as e:
        print(f"❌ LLM 판단 오류 → 규칙 기반 fallback 사용: {e}")
        return _rule_based_fallback(findings, evidences)