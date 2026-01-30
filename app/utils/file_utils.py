# app/utils/file_utils.py
import os
import json
import hashlib
from typing import Any, Dict
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl


# 결과 저장 디렉토리 생성
def ensure_result_dir() -> str:
    base_dir = os.path.join(os.path.dirname(__file__), "..", "services", "result")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

# URL 등 문자열을 짧은 해시로 변환
def short_hash(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()[:8]

# 텍스트 파일 저장
def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

# JSON 파일 저장
def write_json(path: str, obj: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# HTML을 텍스트로 변환
def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    return soup.get_text(" ", strip=True)

# 기본 URL 모델 (선택적)
DEFAULT_URL = "https://google.com"

class RunRequest(BaseModel):
    url: HttpUrl | None = None