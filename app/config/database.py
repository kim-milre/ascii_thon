# app/config/database.py
import asyncio
import os
from pymongo import ASCENDING
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("DATABASE_URL")
DB_NAME = os.getenv("DB_NAME", "sducoss")

if not MONGO_URL:
    raise ValueError("❌ DATABASE_URL 환경 변수가 설정되어 있지 않습니다.")

print("📡 DATABASE_URL =", MONGO_URL)

client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
    maxPoolSize=5,
)


db = client[DB_NAME]

analysis_collection = db["analysis_results"]          # 분석 결과 저장
sites_collection = db["sites"]                        # 사이트 목록
users_collection = db["users"]                        # 사용자 정보
policies_collection = db["policies"]                  # 사이트 약관 원문
policy_vectors_collection = db["policy_vectors"]      # 약관 벡터 인덱싱 결과
legal_vectors_collection = db["legal_vectors"]        # 법령 벡터 (RAG용)
findings_collection = db["findings"]                  # 탐지 로그
decisions_collection = db["decisions"]

try:
    client.admin.command("ping")
    print("✅ MongoDB 연결 성공:", db.name)
except Exception as e:
    print("❌ MongoDB 연결 실패:", e)

# --- 약관 관련 인덱스 보장 함수 ---
async def ensure_policy_indexes():
    """
    약관 관련 컬렉션에 필요한 인덱스를 보장.
    Vector Search에서 site + policy_type 조합으로 빠른 검색이 가능하도록 설정.
    """
    try:
        await policies_collection.create_index([("url", ASCENDING)], background=True)
        await policies_collection.create_index([("site", ASCENDING)], background=True)
        await policy_vectors_collection.create_index(
            [("site", ASCENDING), ("policy_type", ASCENDING)], background=True
        )
        print("🧩 약관 및 벡터 인덱스 보장 완료.")
    except Exception as e:
        print("⚠️ ensure_policy_indexes() 실행 중 오류:", e)

async def log_collections():
    try:
        collections = await db.list_collection_names()
        print("✅ collections in DB:", collections)
    except Exception as e:
        print("⚠️ DB 컬렉션 목록 조회 실패:", e)