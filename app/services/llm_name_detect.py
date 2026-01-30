import os
import json
from typing import List, Dict, Any
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


SYSTEM_PROMPT = """
너는 개인정보 탐지기다.
다음 텍스트에서 '실제 사람 이름'만 찾아라.

규칙:
- 사람 이름만 반환한다
- 날짜, 조직명, 일반 명사, 직업명, 개념어는 절대 포함하지 않는다
- 원문에 그대로 등장한 문자열(span)만 사용한다
- 추측하지 않는다
- 중복 이름은 한 번만 반환한다

반드시 json 형식으로만 출력하라.
응답은 json 객체여야 한다.

출력 예시 (json):
{
  "names": ["김현서", "양종원"]
}
"""


def detect_names_with_openai(text: str, max_chars: int = 4000) -> List[Dict[str, Any]]:
    """
    OpenAI를 사용해 사람 이름만 보강 탐지
    반환 형식은 detect_risks와 호환됨
    """
    if not _client or not text.strip():
        return []

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text[:max_chars]},
            ],
            max_tokens=300,
        )

        raw = resp.choices[0].message.content
        data = json.loads(raw)
        names = data.get("names", [])

        results = []
        for name in names:
            if not isinstance(name, str):
                continue
            name = name.strip()
            if not name:
                continue

            # 원문에 실제로 존재하는 경우만
            idx = text.find(name)
            if idx == -1:
                continue

            results.append({
                "type": "PII",
                "label": "NAME",
                "span": name,
                "start": idx,
                "end": idx + len(name),
                "confidence": 0.7,
                "method": "openai",
            })
        print("🧪 OPENAI RAW NAME RESULT:", data)

        return results

    except Exception as e:
        print(f"⚠️ OpenAI 이름 탐지 실패: {e}")
        return []