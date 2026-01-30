# robots_service.py
import asyncio
import aiohttp
from urllib.parse import urlparse, urljoin

async def fetch_robots_txt(url: str) -> str | None:
    """URL에서 /robots.txt 파일 내용을 가져온다."""
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = urljoin(base, "/robots.txt")

    print(f"[INFO] 요청: {robots_url}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(robots_url, timeout=10) as resp:
                if resp.status == 200:
                    print("[INFO] robots.txt 수신 성공 ✅")
                    return await resp.text()
                else:
                    print(f"[WARN] 응답 코드 {resp.status} — 파일이 없거나 접근 불가")
        except Exception as e:
            print(f"[ERROR] 요청 실패: {e}")
    return None



def parse_robots_txt(text: str, user_agent: str = "*"):
    """
    RFC에 맞춰 '섹션' 단위로 파싱하고, 지정된 user_agent(* 포함)에 해당하는 규칙을
    {'allow': [...], 'disallow': [...]} 형태로 반환.
    - 주석(#) 및 inline 주석 제거
    - CRLF/탭/앞뒤 공백 제거
    - 키 대소문자 무시 (User-agent/Disallow/Allow)
    - 여러 UA 섹션 누적 지원 (*, 특정 UA 동시 존재 시 모두 포함)
    """
    if not text:
        return {"allow": [], "disallow": []}

    # BOM 제거 + 개행 통일
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    target = user_agent.strip().lower()

    sections = []
    cur_uas = []
    cur_rules = {"allow": [], "disallow": []}

    def _push_section():
        nonlocal cur_uas, cur_rules
        if cur_uas:
            sections.append((cur_uas[:], {"allow": cur_rules["allow"][:], "disallow": cur_rules["disallow"][:]}))
        cur_uas = []
        cur_rules = {"allow": [], "disallow": []}

    for raw_line in text.split("\n"):
        # inline 주석 제거
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()

        if key == "user-agent":
            # 새로운 UA가 나오면 이전 섹션을 푸시해야 함
            # (첫 UA 이전엔 빈 섹션이므로 푸시 안 함)
            if cur_uas or cur_rules["allow"] or cur_rules["disallow"]:
                _push_section()
            cur_uas = [val.lower()]
        elif key == "allow":
            cur_rules["allow"].append(val)
        elif key == "disallow":
            cur_rules["disallow"].append(val)
        else:
            # 다른 디렉티브(sitemap, crawl-delay 등)는 무시
            pass

    # 파일 끝 처리
    if cur_uas or cur_rules["allow"] or cur_rules["disallow"]:
        _push_section()

    # 대상 UA와 매칭되는 섹션의 규칙 모두 합치기
    merged = {"allow": [], "disallow": []}
    for uas, rules in sections:
        if "*" in uas or target in uas:
            merged["allow"].extend(rules["allow"])
            merged["disallow"].extend(rules["disallow"])

    # 공백/중복 제거
    def _norm_list(lst):
        out, seen = [], set()
        for p in lst:
            p = (p or "").strip()
            if p in seen:
                continue
            seen.add(p)
            if p == "":  # 'Disallow:' 빈 값은 허용 의미
                continue
            out.append(p)
        return out

    merged["allow"] = _norm_list(merged["allow"])
    merged["disallow"] = _norm_list(merged["disallow"])
    return merged


def has_ai_crawl_prohibition(text: str) -> bool:
    """
    robots.txt에 AI / RAG / 학습 목적 접근 금지 의사가 명시돼 있는지 판단
    """
    if not text:
        return False

    lowered = text.lower()

    ai_keywords = [
        "ai", "artificial intelligence",
        "gpt", "llm",
        "training", "train",
        "rag", "retrieval",
        "machine learning",
    ]

    bot_keywords = [
        "gptbot",
        "openai",
        "oai-searchbot",
        "claudebot",
        "perplexitybot",
        "google-extended",
        "meta-externalagent",
        "applebot-extended",
        "ccbot",
    ]

    # AI 관련 User-agent + Disallow: /
    if any(bot in lowered for bot in bot_keywords) and "disallow: /" in lowered:
        return True

    # 주석/설명에 명시적 금지 문구
    if any(k in lowered for k in ai_keywords) and "prohibit" in lowered:
        return True

    return False

def is_allowed(path: str, rules) -> bool:
    """
    robots 규칙에 따라 경로 허용 여부 판단.
    - path: '/abc/...' (반드시 슬래시 시작)
    - rules: {'allow': [...], 'disallow': [...]}
    - 전략: allow/disallow 각각 path-prefix longest match → 더 긴 쪽이 우선
    """
    if not isinstance(rules, dict):
        return True
    
    disallows = rules.get("disallow") or []
    if "/" in disallows:
        return False

    path = path or "/"
    if not path.startswith("/"):
        path = "/" + path

    allows = rules.get("allow", []) or []
    disallows = rules.get("disallow", []) or []

    def longest_prefix_len(prefixes, s):
        best = -1
        for p in prefixes:
            # 구글 규칙은 와일드카드도 있지만, 여기선 prefix 매치로 단순화
            if p == "/":
                length = 1 if s.startswith("/") else -1
            else:
                length = len(p) if s.startswith(p) else -1
            if length > best:
                best = length
        return best

    la = longest_prefix_len(allows, path)
    ld = longest_prefix_len(disallows, path)

    # 둘 다 매치 없으면 허용
    if la < 0 and ld < 0:
        return True

    # 더 긴 규칙이 우선
    if la > ld:
        return True
    if ld > la:
        return False

    # 길이 동일하면 Disallow 우선 (보수적)
    return False


if __name__ == "__main__":
    asyncio.run(main())
