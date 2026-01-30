# app/services/llm_quickest.py
import os, json, re
from openai import OpenAI
from app.services.mask_service import mask_pii

# ──────────────────────────────────────────────
# ① 기본 시스템 프롬프트 정의
# ──────────────────────────────────────────────
DEFAULT_SYSTEM_PROMPT = """
당신은 법적 리스크 자동 판정기입니다.
감정적이거나 수사적인 표현 없이, 입력된 문맥(context)과 증거(evidences)를 근거로 **기계적으로** 판단하세요.

────────────────────────
입력 형식
────────────────────────
- findings: 사이트에서 탐지된 항목들의 배열
  * 각 항목: {label, span, context, method, confidence}
  * context: 탐지된 텍스트 주변의 실제 HTML 문맥 (앞뒤 약 16자)
- evidences: 관련 법령 또는 약관의 구절 배열
  * 각 항목: {text, source_type}
- terms: (선택) 사이트의 약관/정책 원문 일부

────────────────────────
판정 규칙
────────────────────────
**1. 반드시 context를 확인하여 span이 실제 개인정보로 사용된 것인지 판단합니다.**
**2. span에 조사('을','를','이','가','의' 등)나 호칭('씨','님' 등)이 붙어 있다면, 이를 제거한 후 핵심 단어를 기준으로 판정합니다.**
**3. context에서 해당 span이 단순 명사/동사/대명사로 쓰인 경우 PASS로 처리합니다.**

────────────────────────
결정 기준
────────────────────────
- "PASS": 법적 문제 없음 / 비식별 / 공지 수준 / 실제 노출 가능성 낮음
  * HTML 태그나 속성 내부에서만 등장
  * 일반 명사, 동사, 대명사 (예: "여자친구", "운영체제", "내가", "사용하고")
  * context상 단순 서술 또는 예시로 사용된 경우

- "REVIEW": 추가 검토 필요 / 애매 / 법령 또는 약관과 상충 가능성
  * 조사가 붙은 2~4자 한글 명사("기록을","파일이","계정을" 등)은 실명이 아닌 일반명사로 간주하고 반드시 PASS로 처리합니다.
  * context가 불충분하여 명확한 판정이 어려움
  * 법령 또는 정책상 근거는 있으나 위험도가 불확실함

- "MASK": 명백한 개인정보로 실제 문맥에서 개인 식별 가능
  * EMAIL, PHONE, ADDRESS, RESIDENT_ID, CREDIT_CARD 등 형식상 민감정보
  * NAME이면서 context에 직함/연락처/역할명이 함께 등장 (예: "홍길동 담당자", "김철수(010-1234-5678)")
  * context에서 span이 단순 명사가 아니라 **실명(개인 식별 가능한 이름)** 으로 사용된 경우

────────────────────────
라벨별 처리 원칙
────────────────────────
- NAME:
  * 반드시 context를 통해 사람이름(real name)인지 일반명사인지 구분
  * 일반명사(예: "여자친구", "학생", "내가")는 PASS
  * 실명 가능성이 높을 경우(직함·직위·연락처와 함께 사용 등) MASK
  * 애매하면 REVIEW

- EMAIL, PHONE, ADDRESS, RESIDENT_ID, CREDIT_CARD:
  * 원칙적으로 식별성이 높으므로 기본적으로 MASK

- HTML 태그/스크립트/스타일 내부에서만 등장하는 값(context로 확인):
  * 실제 노출 가능성이 낮으므로 PASS

────────────────────────
출력 형식 (반드시 JSON 한 개)
────────────────────────
주의:
- 코드펜스(````), 주석, 트레일링 콤마 없이 JSON 한 개만 출력
- 모든 문자열은 반드시 쌍따옴표(") 사용

────────────────────────
REASON 작성 규칙 (반드시 서술형 줄글 형식 준수)
────────────────────────
- PII 원문은 그대로 쓰지 말고 **부분 마스킹**하여 언급해야 합니다. (예: 앞 1글자/뒤 1글자만 노출, 가운데 `*`)

- **반드시 다음 세 가지 내용을 포함하는 논리적인 서술형 문장**으로 구성합니다:
  1.  **발견된 항목 및 문맥 설명:** 탐지된 항목(`masked_span`), 그리고 HTML 문맥에서의 노출 유형(`context_class`)을 언급합니다.
  2.  **판단 근거:** 항목의 최종 라벨(`final_label` 또는 `label`)로의 변경 여부, 사용된 핵심 규칙(예: 전화번호 정규식 일치, 이름 주변 직함), 그리고 결정(`PASS/REVIEW/MASK`)에 도달한 **핵심 이유**를 설명합니다.
  3.  **점수 산정 및 증거 요약:** 최종 점수(`score_logic`에 기반한 산정) 및 사용된 법률/약관 증거를 간략히 언급합니다.

- **주의:** 내용은 최대 600자로 제한합니다.


작성 규칙 상세:
- masked_span: 예) “김*레”, “k***@d***.com”, “010-12**-****”
- label: 전처리/판정으로 라벨이 바뀌면 “NAME->TEXT”처럼 표기, 그대로면 “EMAIL->EMAIL”
- context_class: 
  - 일반 텍스트면 `visible_text`
  - 태그 속성/메타/스크립트/스타일 내부면 `tag_attr_only` 또는 `script_style_only`
- triggers: 발동한 규칙·정규식·휴리스틱을 짧게 나열 (예: EMAIL_REGEX, JOSA_STRIP, NAME+TITLE_NEARBY, TAG_ONLY_DEMERIT 등)
- evidences: 법령/약관 근거를 1~3개, **짧은 요지**로 (예:“내부 방침: 연락처 공개 금지”)
- decision_logic: 최종 결론에 도달한 핵심 이유를 1~2절로 (예: “직함+전화번호 동시노출 → 식별성 높음 → MASK”)
- score_logic: 점수 산정 근거를 간략히 (예: “RAG 55 + context +20 = 75” 또는 “명백한 이메일 패턴 → 80”)

제약:
- reason은 최대 600자.
- 줄바꿈 없이 ‘ | ’ 구분자로만 이어서 기재.
- PII 원문 전체를 절대 그대로 쓰지 말 것(부분 마스킹 필수).


출력 예시:
{
  "decision": "PASS" | "REVIEW" | "MASK",
  "score": 0~100,                 // 위험도 (의심할 여지가 적을수록 낮은 값)
  "reason": "자세한 판단 과정 (필요 시 context 내용 언급, masked_span 사용)",
  "law_evidence": [법령 관련 요약 문장 최대 3개],
  "site_policy_evidence": [약관 관련 문장 최대 3개]
}
"""



# ──────────────────────────────────────────────
# ② 프롬프트 로드 함수: llm_quickest 안에서 처리
# ──────────────────────────────────────────────
def get_system_prompt(override_prompt: str = None) -> str:
    """
    override_prompt: data에서 전달된 새 프롬프트가 있으면 그걸 사용.
    그렇지 않으면 .env나 기본 프롬프트를 로드.
    """
    # 1) 호출자가 data["override_system_prompt"]로 프롬프트를 넘겼을 때
    if override_prompt:
        return override_prompt.strip()

    # 2) .env에서 외부 파일 지정 가능 (선택)
    custom_path = os.getenv("RISK_SYSTEM_PROMPT_PATH")
    if custom_path and os.path.exists(custom_path):
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
                if text:
                    return text
        except Exception:
            pass

    # 3) 기본 프롬프트 반환
    return DEFAULT_SYSTEM_PROMPT.strip()


# ──────────────────────────────────────────────
# ③ judge_risk 본문 (요약만 표시)
# ──────────────────────────────────────────────
def judge_risk(data: dict):
    findings = data.get("findings", {})
    evidences = data.get("evidences", [])
    terms = data.get("terms", None)
    rag_score = data.get("rag_score")

    # 🔸 여기서 system prompt를 결정
    system_prompt = get_system_prompt(data.get("override_system_prompt"))

    # 유저 프롬프트 구성
    user_prompt = {
        "FINDINGS": findings,
        "EVIDENCES": evidences,
        "TERMS": terms,
        "INSTRUCTIONS": "system prompt를 사용해서 PASS/REVIEW/MASK 중 하나를 직접 선택하고 이유를 설명."
    }

    # LLM 호출
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_RISK_MODEL", "gpt-4o-mini"),
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)}
            ]
        )

        raw = resp.choices[0].message.content
        result = json.loads(re.search(r"\{.*\}", raw, flags=re.DOTALL).group(0))

        rag = rag_score or 0
        llm = int(result.get("score", 0))
        final_score = min(100, int(rag * 0.6 + llm * 0.4))
        result["score"] = final_score
        return result

    except Exception as e:
        print("❌ LLM 판단 실패:", e)
        return {
            "decision": "REVIEW",
            "score": rag_score,
            "reason": f"fallback: {e}",
            "law_evidence": [],
            "site_policy_evidence": [],
        }