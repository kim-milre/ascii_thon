# scripts/create_admin.py
import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://cralwise:12345@cluster.nenw4i7.mongodb.net/?appName=Cluster")
DB_NAME = os.getenv("DB_NAME", "sducoss")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    users_collection = db["users"]

    try:
        print("데이터베이스에 연결되었습니다.")

        # 기존 관리자 계정 존재 여부 확인
        existing_admin = await users_collection.find_one({"userType": "admin"})
        if existing_admin:
            print(f"이미 관리자 계정이 존재합니다: {existing_admin['email']}")
            return

        # 새 관리자 계정 데이터
        admin_email = "crawlwise@ajou.ac.kr"
        admin_password = "C123123!"
        hashed_pw = pwd_context.hash(admin_password)

        admin_user = {
            "email": admin_email,
            "password": hashed_pw,
            "name": "관리자",
            "userType": "admin",
            "provider": "local",
            "isActive": True,
            "createdAt": datetime.utcnow(),
        }

        result = await users_collection.insert_one(admin_user)
        print("관리자 계정이 생성되었습니다:")
        print("이메일:", admin_email)
        print("비밀번호:", admin_password)
        print("사용자 유형: admin")
        print("MongoDB _id:", result.inserted_id)

    except Exception as e:
        print("관리자 계정 생성 중 오류 발생:", e)

    finally:
        client.close()
        print("데이터베이스 연결이 종료되었습니다.")


if __name__ == "__main__":
    asyncio.run(create_admin_user())