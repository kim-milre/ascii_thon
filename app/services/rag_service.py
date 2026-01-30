import os
import json
import re
import pymongo
from pymongo.server_api import ServerApi
from openai import OpenAI
from typing import List, Dict, Any, Union
from dotenv import load_dotenv
from itertools import chain

# --- 법적 핵심 키워드 ---
LEGAL_KEYWORDS = [
    "개인정보", "수집", "이용", "제공", "보관", "파기",
    "동의", "책임", "면책", "약관", "저작권"
]

MAX_EMBED_CHARS = 3000  # 1분 내 처리 안정선

load_dotenv()

# --- 1. 환경 설정 및 상수 정의 ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://ckwcan:123@cluster.nenw4i7.mongodb.net/?appName=Cluster")
DB_NAME = os.getenv("DB_NAME", "compliance_db")

LEGAL_COLLECTION = os.getenv("COLLECTION_NAME", "legal_vectors")
POLICY_COLLECTION = os.getenv("POLICY_COLLECTION", "policy_vectors")

LEGAL_VECTOR_INDEX = os.getenv("LEGAL_VECTOR_INDEX", "vector_index")
POLICY_VECTOR_INDEX = os.getenv("POLICY_VECTOR_INDEX", "site_policy_vector_index")

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072 # text-embedding-3-large 모델의 벡터 차원 수

# --- [수정됨] MongoDB Atlas 벡터 인덱스 이름 ---
# 중요: 이 값은 실제 MongoDB Atlas에서 생성한 인덱스 이름으로 변경해야 합니다.
VECTOR_INDEX_NAME = "vector_index"

# --- 2. 전역 클라이언트 초기화 ---
# FastAPI 앱이 시작될 때 이 모듈이 로드되면서 클라이언트가 생성됩니다.
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    mongo_client = pymongo.MongoClient(MONGO_URI, server_api=ServerApi('1'))
    mongo_client.admin.command('ping')
    db = mongo_client[DB_NAME]
    legal_collection = db[LEGAL_COLLECTION]
    policy_collection = db[POLICY_COLLECTION]
    ok = True
    print("✅ (rag_service.py) OpenAI 및 MongoDB 클라이언트 초기화 완료.")

except Exception as e:
    print(f"❌ (rag_service.py) 클라이언트 초기화 중 오류 발생: {e}")
    openai_client = None
    legal_collection = None
    policy_collection = None
    ok = False


# --- 메모리 캐시 ---
_rag_cache: Dict[str, List[Dict[str, Any]]] = {}


# --- 쿼리 문자열 생성 ---
def build_query_string(finding: Union[str, Dict], html_context: str = "", site: str = "") -> str:
    if isinstance(finding, dict):
        cat = finding.get("type", "")
        label = finding.get("label", "")
        span = finding.get("span", "")
        # ✅ finding 자체의 context를 우선 사용 (주변 문맥)
        local_ctx = finding.get("context", "")
        ctx = local_ctx if local_ctx else html_context[:300]
        return f"Category: {cat} | Label: {label} | Text: {span} | Context: {ctx} | Site: {site}"
    return str(finding)


# --- 법령 벡터 검색 ---
def _vector_search_legal(query_vector, top_k: int = 2) -> List[Dict[str, Any]]:
    if legal_collection is None:
        return []
    try:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": LEGAL_VECTOR_INDEX,
                    "path": "vector",
                    "queryVector": query_vector,
                    "numCandidates": 50,
                    "limit": top_k
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "source_type": {"$literal": "law"},
                    "text": 1,
                    "source": 1,
                    "law_ref": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        return list(legal_collection.aggregate(pipeline))
    except Exception as e:
            print(f"⚠️ 법령 벡터 검색 오류: {e}")
            return []

def extract_legal_query_text(
    finding: dict,
    html_context: str = ""
) -> str:
    """
    임베딩에 사용할 최소 법적 문맥만 추출
    - span + 주변 법적 키워드 문장만 사용
    - 개인정보/원문 재사용 최소화
    """
    span = str(finding.get("span", "")).strip()
    ctx = str(finding.get("context", "")).strip()

    base = f"{span} {ctx}"

    lines = base.splitlines()
    selected = [
        line for line in lines
        if any(k in line for k in LEGAL_KEYWORDS)
    ]

    text = "\n".join(selected) if selected else span
    return text[:MAX_EMBED_CHARS]

# --- 사이트 약관 벡터 검색 ---
def _vector_search_policy(query_vector, site: str, top_k: int = 5) -> List[Dict[str, Any]]:
    if policy_collection is None:
        return []
    try:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": POLICY_VECTOR_INDEX,
                    "path": "vector",
                    "queryVector": query_vector,
                    "numCandidates": 50,
                    "limit": top_k,
                    "filter": {"site": site}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "source_type": {"$literal": "site_policy"},
                    "text": 1,
                    "source_url": 1,
                    "policy_type": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        return list(policy_collection.aggregate(pipeline))
    except Exception as e:
        print(f"⚠️ 약관 벡터 검색 오류: {e}")
        return []

# --- 핵심 검색 함수 ---
async def search_legal_evidence(finding: Any, site: str = "", html_context: str = "", top_k: int = 2) -> List[Dict[str, Any]]:
    """탐지된 텍스트를 기반으로 법령/사이트 약관에서 근거 검색"""
    if openai_client is None or legal_collection is None:
        print("❌ (rag_service) 클라이언트 초기화 오류로 검색 불가.")
        return []

    # --- 쿼리 문자열 준비 ---
    query_str = extract_legal_query_text(finding, html_context).strip()
    if not query_str or len(query_str) < 3:
        print("⚠️ (rag_service) 유효하지 않은 법적 쿼리 — 검색 생략")
        return []

    # --- 캐시 확인 ---
    cache_key = f"{site}::{query_str}"

    if cache_key in _rag_cache:
        print(f"⚡ 캐시 재사용: {cache_key[:80]}...")
        return _rag_cache[cache_key]

    print(f"🔍 RAG 검색 시작: '{query_str[:120]}...'")

    try:
        # --- OpenAI 임베딩 생성 ---
        emb_response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query_str
        )
        query_vector = emb_response.data[0].embedding

        # --- 법령 + 약관 근거 병합 ---
        legal_results = _vector_search_legal(query_vector, top_k=top_k)
        policy_results = _vector_search_policy(query_vector, site, top_k=top_k) if site else []
        combined = sorted(
            chain(legal_results, policy_results),
            key=lambda x: x.get("score", 0),
            reverse=True,
        )[: top_k * 2]

        print(f"✅ 법령 {len(legal_results)}건, 약관 {len(policy_results)}건 검색 완료")

        # --- 캐시 저장 ---
        _rag_cache[query_str] = combined

        return combined

    except Exception as e:
        if hasattr(e, "response") and hasattr(e.response, "text"):
            try:
                print(f"❌ OpenAI 오류: {json.loads(e.response.text)}")
            except Exception:
                pass
        print(f"❌ (rag_service) RAG 검색 중 오류 발생: {e}")
        return []

async def analyze_findings(
    site_url: str,
    findings: list,
    html_context: str = "",
    limit: int = 10,          # 상위 N개만 RAG
    top_k: int = 2,           # 법/약관 각각 몇 개까지 가져올지
) -> list | dict:
    """
    탐지 결과를 받아 RAG만 수행.
    - 단일 항목([item])을 주면: evidences(list[dict]) 만 반환
    - 복수 항목을 주면: [{finding, evidences}] 리스트 반환
    """
    print(f"🔎 analyze_findings() 호출 — 입력 {len(findings)}건")

    # 1) 입력 정리/필터
    filtered = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        span = str(f.get("span", "")).strip()
        if not span or len(span) <= 2:
            continue
        if re.match(r'^(<|>|/|http|src|meta|js|css|style|card|apple|svg|link|async|defer|script)', span, re.I):
            continue
        filtered.append(f)

    print(f"🧩 필터링 후 {len(filtered)}건 (원래 {len(findings)}건)")

    # 2) RAG 수행
    results = []
    for finding in filtered[:limit]:
        hits = await search_legal_evidence(finding, site_url, html_context, top_k)
        results.append({"finding": finding, "evidences": hits})
    total_hits = sum(len(r["evidences"]) for r in results)
    print(f"✅ RAG 완료: 대상 {len(results)}건, 근거 {total_hits}개.")
    if len(findings) == 1 and results:
        return results[0]["evidences"]   # ← 단일 항목이면 evidences 리스트만
    return results

# async def search_legal_evidence(query_text: Any, top_k: int = 1) -> List[Dict[str, Any]]:
#     """
#     탐지된 위험 텍스트(쿼리)를 기반으로 MongoDB Atlas에서
#     가장 관련성 높은 법적 근거(문서 청크)를 검색합니다.
#
#     Args:
#         query_text (str): 'detect_service'가 탐지한 텍스트
#                           (예: "이메일 주소 admin@example.com 발견")
#         top_k (int): 반환할 관련 문서의 최대 개수 (기본 1개)
#
#     Returns:
#         List[Dict[str, Any]]: 포맷팅된 근거 자료 리스트.
#                               (예: [{"source": "...", "text": "...", "score": 0.85}])
#     """
#
#     # 'is None'으로 명시적으로 비교하도록 변경
#     if openai_client is None or collection is None:
#         print("❌ (rag_service) 오류: 클라이언트가 제대로 초기화되지 않았습니다.")
#         return []
#
#     if isinstance(query_text, dict):
#         query_str = query_text.get("span", json.dumps(query_text, ensure_ascii=False))
#     else:
#         query_str = str(query_text).strip()
#
#     if not query_str:
#         print("⚠️ (rag_service) 빈 쿼리 문자열이 감지되어 검색을 건너뜁니다.")
#         return []
#
#     # --- 캐시 확인 ---
#     if query_str in _rag_cache:
#         print(f"⚡ 캐시 재사용: {query_str}")
#         return _rag_cache[query_str]
#
#     print(f"🔍 RAG 검색 시작 (쿼리: '{query_text}')")
#
#     try:
#         # --- 절차 1: 쿼리 임베딩 ('detect된 부분'을 임베딩) ---
#         # "admin@example.com" 같은 텍스트를 OpenAI API를 통해 벡터(좌표)로 변환
#         if isinstance(query_text, dict):
#             query_str = query_text.get("span", json.dumps(query_text, ensure_ascii=False))
#         else:
#             query_str = str(query_text).strip()
#
#         if not query_str:
#             print("⚠️ (rag_service) 빈 쿼리 문자열이 감지되어 검색을 건너뜁니다.")
#             return []
#
#         embedding_response = openai_client.embeddings.create(
#             model=EMBEDDING_MODEL,
#             input=query_str
#         )
#         query_vector = embedding_response.data[0].embedding
#
#         # --- 절차 2: MongoDB Vector Search 파이프라인 정의 ---
#         # 이 좌표와 가장 가까운 법령/약관을 DB에서 검색
#         pipeline = [
#             {
#                 "$vectorSearch": {
#                     "index": VECTOR_INDEX_NAME,  # 벡터 인덱스 이름
#                     "path": "vector",  # 벡터 필드 경로
#                     "queryVector": query_vector,  # 방금 생성한 '쿼리 벡터(좌표)'
#                     "numCandidates": 50,  # 검색 후보군
#                     "limit": top_k  # 최종 반환 개수
#                 }
#             },
#             {
#                 # --- 절차 3: 결과 포맷팅 ---
#                 "$project": {
#                     "_id": 0,
#                     "text": 1,  # 원본 텍스트
#                     "source": 1,  # 출처 파일명
#                     "score": {"$meta": "vectorSearchScore"}  # 유사도 점수
#                 }
#             }
#         ]
#
#         # --- 절차 4: 검색 실행 ---
#         search_results = list(collection.aggregate(pipeline))
#
#         print(f"    ✅ 총 {len(search_results)}개의 관련 문서를 찾았습니다.")
#
#         _rag_cache[query_str] = search_results
#         # --- 절차 5: 결과 반환 ---
#         return search_results
#
#
#     except Exception as e:
#         # API 응답이 dict 형태일 경우 상세 원인 출력
#         if hasattr(e, "response") and hasattr(e.response, "text"):
#             try:
#                 error_json = json.loads(e.response.text)
#                 print(f"❌ (rag_service) OpenAI 오류 세부내용: {error_json}")
#             except Exception:
#                 pass
#
#         print(f"❌ (rag_service) RAG 검색 중 오류 발생: {e}")
#         return []