import pymongo
from pymongo.server_api import ServerApi
import urllib.parse
import sys  # 1. ❗️ 시스템 종료(sys.exit)를 위해 import

# --- 1단계: 괄쇠('<', '>')를 제거하고 ID/PW를 정확히 입력 ---
# ❗️❗️❗️ 괄쇠(< >) 없이 순수 ID와 PW만 입력해야 합니다 ❗️❗️❗️
MONGO_ID = "ckwcan"
MONGO_PW = "123"
MONGO_CLUSTER_URL = "cluster.nenw4i7.mongodb.net/?appName=Cluster"

# --- 2단계: ID/PW의 특수문자('@' 등)를 인코딩 ---
try:
    # ID와 PW에 포함된 특수문자(@ 등)를 RFC 3986 표준에 맞게 인코딩합니다.
    escaped_id = urllib.parse.quote_plus(MONGO_ID)
    escaped_pw = urllib.parse.quote_plus(MONGO_PW)
except Exception as e:
    print(f"❌ ID/PW 인코딩 중 치명적 오류 발생: {e}")
    # 인코딩 실패 시 이후 진행이 무의미하므로 종료합니다.
    sys.exit(1)

# --- 3단계: 인코딩된 ID/PW로 최종 URI 조합 ---
MONGO_URI = f"mongodb+srv://{escaped_id}:{escaped_pw}@{MONGO_CLUSTER_URL}"

# 전역 변수로 MongoDB 클라이언트를 생성합니다.
# (연결 타임아웃을 5초로 설정하여 응답을 빠르게 받습니다)
try:
    print(f"MongoDB({MONGO_URI}) 클라이언트 생성 시도...")
    # ❗️ serverSelectionTimeoutMS: 5초 내 연결(IP 접근)이 안 되면 바로 실패 처리
    client = pymongo.MongoClient(
        MONGO_URI,
        server_api=ServerApi('1'),
        serverSelectionTimeoutMS=5000  # 5초 타임아웃
    )
    print("...클라이언트 객체 생성 성공.")
except pymongo.errors.ConfigurationError as e:
    # 이 오류는 URI 문자열 자체가 잘못되었을 때만 발생합니다.
    print(f"❌ MongoDB 연결 실패: 설정 오류 (ConfigurationError)")
    print("-> 1순위: MONGO_ID, MONGO_PW에 괄쇠(< >)가 포함되었는지 확인하세요.")
    print(f"-> 2순위: MONGO_URI 형식 자체를 다시 확인하세요. (예: mongodb+srv://...)")
    print(f"-> 상세 오류: {e}")
    # 이 경우, 더 이상 테스트가 불가능하므로 종료합니다.
    sys.exit(1)
except Exception as e:
    print(f"❌ 클라이언트 생성 중 알 수 없는 오류: {e}")
    sys.exit(1)


def test_connection_ping():
    """테스트 1: 'admin' DB에 'ping' 명령을 보내 연결을 테스트합니다."""
    print("\n--- [테스트 1: PING 명령 테스트] 시작 ---")
    try:
        # 'ping' 명령은 인증(Authentication)만 확인합니다.
        client.admin.command('ping')
        print("=========================================")
        print("  ✅ (테스트 1) PING 연결 성공! ✅")
        print("=========================================")
        return True

    except pymongo.errors.OperationFailure as e:
        print(f"❌ (테스트 1) PING 실패: 인증 오류 (OperationFailure)")
        print(f"-> ID({MONGO_ID}) 또는 PW가 잘못되었습니다. (사용자 주장과 다름)")
        print(f"-> 상세 오류: {e}")
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print(f"❌ (테스트 1) PING 실패: 연결 시간 초과 (ServerSelectionTimeoutError)")
        print("-> ❗️❗️❗️ 1순위: Atlas [Network Access]에 IP(0.0.0.0/0)가 등록되었는지 확인하세요.")
        print("-> 2순위: 방화벽(Firewall)이 27017 포트를 막고 있는지 확인하세요.")
        print(f"-> 상세 오류: {e}")
    except Exception as e:
        print(f"❌ (테스트 1) PING 실패: 기타 오류")
        print(f"-> 상세 오류: {e}")

    return False


def test_list_databases():
    """테스트 2: 실제 데이터베이스 목록을 조회하여 권한을 테스트합니다."""
    print("\n--- [테스트 2: DB 목록 조회 테스트] 시작 ---")
    try:
        # list_database_names()는 실제 '데이터 조회' 권한을 확인합니다.
        db_list = client.list_database_names()
        print("=========================================")
        print("  ✅ (테스트 2) DB 목록 조회 성공! ✅")
        print("=========================================")
        print(f"-> 접근 가능한 DB 목록: {db_list}")
        return True

    except pymongo.errors.OperationFailure as e:
        print(f"❌ (테스트 2) 조회 실패: 인증/권한 오류 (OperationFailure)")
        print(f"-> PING은 성공했으나 DB 목록 조회가 실패했습니다.")
        print(f"-> 사용자({MONGO_ID})가 DB를 조회할 권한(예: 'readWrite')이 없는지 확인하세요.")
        print(f"-> 상세 오류: {e}")
    except pymongo.errors.ServerSelectionTimeoutError as e:
        # PING 테스트에서 이미 이 오류가 발생했다면 여기서도 동일하게 발생합니다.
        print(f"❌ (테스트 2) 조회 실패: 연결 시간 초과 (ServerSelectionTimeoutError)")
        print("-> ❗️ (테스트 1과 동일) Atlas [Network Access] IP 설정을 확인하세요.")
    except Exception as e:
        print(f"❌ (테스트 2) 조회 실패: 기타 오류")
        print(f"-> 상세 오류: {e}")

    return False


if __name__ == "__main__":
    print("=====================================================")
    print(" SDUCOSS 공모전: MongoDB Atlas 연결 진단을 시작합니다.")
    print("=====================================================")

    # 1. PING 테스트 실행
    ping_success = test_connection_ping()

    # 2. PING이 성공했을 경우에만 DB 목록 조회 테스트 실행
    if ping_success:
        test_list_databases()
    else:
        print("\n❗️ PING 테스트에 실패하여, DB 목록 조회 테스트를 건너뜁니다.")
        print("❗️ '테스트 1'의 오류 메시지를 먼저 해결해 주세요.")

    print("\n--- [연결 진단 완료] ---")