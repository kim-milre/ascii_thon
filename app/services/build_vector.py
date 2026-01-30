import os
import pymongo
from pymongo.server_api import ServerApi
from openai import OpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = "mongodb+srv://ckwcan:123@cluster.nenw4i7.mongodb.net/?appName=Cluster"

DB_NAME = "compliance_db"
COLLECTION_NAME = "legal_vectors" # 법령 벡터를 저장할 컬렉션

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072 # text-embedding-3-large 모델의 벡터 차원 수

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "legal_data.txt")

def get_db_collection() -> pymongo.collection.Collection:
    """MongoDB Atlas에 연결하고 컬렉션 객체를 반환하는 함수"""
    print(f"MongoDB({MONGO_URI}) 연결 시도...")

    # MongoDB 클라이언트 생성
    client = pymongo.MongoClient(MONGO_URI, server_api=ServerApi('1'))

    # 연결 테스트 (ping)
    try:
        client.admin.command('ping')
        print("✅ MongoDB 연결 성공!")
    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {e}")
        raise

    # 데이터베이스와 컬렉션 선택
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # (선택 사항) 만약 기존 데이터를 모두 지우고 새로 만들고 싶다면 아래 주석을 해제하세요.
    # print(f"경고: 기존 {COLLECTION_NAME} 컬렉션의 모든 문서를 삭제합니다...")
    # collection.delete_many({})
    # print("기존 문서 삭제 완료.")

    return collection


# ... (개발자님이 작성하신 윗부분: 임포트, 상수, get_db_collection 함수) ...

def load_and_chunk_documents(path: str) -> List[Dict[str, Any]]:
    """지정된 경로에서 문서를 로드하고 의미 단위로 분할(Chunking)하는 함수"""
    print(f"'{path}' 디렉토리에서 .txt 문서 로드 중...")

    # 1. 데이터 로드 (LangChain의 DirectoryLoader 사용)
    # TextLoader를 지정하여 .txt 파일만 UTF-8로 읽어들입니다.
    if not os.path.exists(path):
        print(f"❌ 오류: '{path}' 경로에 파일이 존재하지 않습니다.")
        return []

    loader = TextLoader(
        path,  # path 변수는 이제 "...app/services/legal_data.txt"가 됩니다.
        encoding="utf-8"
    )
    documents = loader.load()
    print(f"총 {len(documents)}개의 문서 파일 로드 완료.")

    if not documents:
        print(f"경고: '{path}'에서 문서를 찾을 수 없습니다.")
        return []

    # 2. 데이터 분할 (Chunking)
    # RecursiveCharacterTextSplitter는 문단, 줄바꿈 등을 기준으로 자연스럽게 텍스트를 나눕니다.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # 청크(조각)의 최대 글자 수
        chunk_overlap=150,  # 청크 간 겹치는 글자 수 (문맥 유지)
        length_function=len,
    )

    chunks = text_splitter.split_documents(documents)
    print(f"총 {len(chunks)}개의 텍스트 청크(Chunk)로 분할 완료.")

    # 3. DB에 저장할 형태로 데이터 가공
    # 각 청크(doc)를 필요한 정보(원본 텍스트, 출처)와 함께 딕셔너리로 변환합니다.
    processed_chunks = []
    for i, doc in enumerate(chunks):
        processed_chunks.append({
            "chunk_id": f"chunk_{i}",  # 고유 ID
            "source": doc.metadata.get("source", "unknown"),  # 파일 출처
            "text": doc.page_content  # 분할된 텍스트 원본
            # (아직 'vector' 필드는 없습니다)
        })

    return processed_chunks


def create_embeddings(client: OpenAI, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """텍스트 청크 리스트를 받아 OpenAI 임베딩 모델로 벡터를 생성하는 함수"""
    print(f"총 {len(chunks)}개 청크에 대한 임베딩 생성 시작 (모델: {EMBEDDING_MODEL})...")

    # 임베딩을 생성할 텍스트만 추출합니다.
    texts_to_embed = [chunk["text"] for chunk in chunks]

    # OpenAI API 호출하여 임베딩 생성
    try:
        response = client.embeddings.create(
            input=texts_to_embed,
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS  # 모델 차원 수 지정 (text-embedding-3-large는 3072)
        )

        # 생성된 임베딩(벡터)을 다시 원래 청크 딕셔너리에 추가
        for i, embedding_data in enumerate(response.data):
            chunks[i]["vector"] = embedding_data.embedding

        print("✅ 임베딩 생성 완료.")
        return chunks

    except Exception as e:
        print(f"❌ OpenAI 임베딩 생성 중 오류 발생: {e}")
        raise


def insert_vectors_to_db(collection: pymongo.collection.Collection, chunks_with_vectors: List[Dict[str, Any]]):
    """벡터가 포함된 청크 데이터 목록을 MongoDB에 삽입(저장)하는 함수"""

    if not chunks_with_vectors:
        print("경고: DB에 삽입할 데이터가 없습니다.")
        return

    print(f"MongoDB '{COLLECTION_NAME}' 컬렉션에 {len(chunks_with_vectors)}개 문서 삽입 시작...")

    try:
        # (선택 사항) 만약 기존 데이터를 모두 지우고 새로 만들고 싶다면
        print("기존 문서 모두 삭제 중...")
        collection.delete_many({})
        print("기존 문서 삭제 완료.")

        # 데이터를 DB에 일괄 삽입 (insert_many)
        result = collection.insert_many(chunks_with_vectors)
        print(f"✅ 총 {len(result.inserted_ids)}개 문서 삽입 성공!")

    except Exception as e:
        print(f"❌ MongoDB 삽입 중 오류 발생: {e}")
        raise


# --- 5. MongoDB Atlas Vector Search 인덱스 생성 (필수!) ---
# ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※
# 이 스크립트 실행 후, MongoDB Atlas 웹 UI에서
# [Database] -> [Collections] -> [compliance_db.legal_vectors] -> [Search Indexes] 탭
# -> [Create Search Index] -> [Atlas Vector Search] -> [JSON Editor]
#
# 아래와 같이 'vector' 필드를 인덱싱하도록 설정해야 합니다.
# {
#   "fields": [
#     {
#       "type": "vector",
#       "path": "vector",
#       "numDimensions": 3072,  <-- EMBEDDING_DIMENSIONS 값과 일치해야 함
#       "similarity": "cosine"
#     }
#   ]
# }
# ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※

def main():
    """전체 벡터 변환 및 DB 저장 파이프라인을 실행하는 메인 함수"""
    print("--- 법령 데이터 벡터화 및 DB 저장 스크립트 시작 ---")

    try:
        # 절차 1: DB 연결
        collection = get_db_collection()

        # 절차 2: OpenAI 클라이언트 초기화
        # (환경 변수에서 키를 읽어오는 것이 더 안전하지만, 상수 사용도 가능)
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        client = OpenAI(api_key=OPENAI_API_KEY)

        # 절차 3: 문서 로드 및 분할
        chunks = load_and_chunk_documents(DATA_PATH)

        if chunks:
            # 절차 4: 임베딩 생성
            chunks_with_vectors = create_embeddings(client, chunks)

            # 절차 5: DB에 적재
            insert_vectors_to_db(collection, chunks_with_vectors)

            print("--- 모든 작업 완료 ---")
            print(f"MongoDB Atlas에서 '{COLLECTION_NAME}' 컬렉션을 확인하고, 'Search Indexes' 탭에서 벡터 인덱스를 생성하세요.")

        else:
            print(f"'{DATA_PATH}'에 처리할 파일이 없어 작업을 종료합니다.")

    except Exception as e:
        print(f"❌ 메인 파이프라인 실행 중 심각한 오류 발생: {e}")


# 스크립트가 직접 실행될 때만 main() 함수를 호출
if __name__ == "__main__":
    main()