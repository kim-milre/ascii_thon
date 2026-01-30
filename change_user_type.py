# scripts/change_user_type.py
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://cralwise:12345@cluster.nenw4i7.mongodb.net/?appName=Cluster")
DB_NAME = os.getenv("DB_NAME", "sducoss")

async def change_user_type(email: str, new_user_type: str):
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    users_collection = db["users"]

    try:
        print("데이터베이스에 연결되었습니다.")

        email = email.lower()
        user = await users_collection.find_one({"email": email})

        if not user:
            print(f"사용자를 찾을 수 없습니다: {email}")
            return

        if new_user_type not in ["user", "admin"]:
            print("유효하지 않은 사용자 유형입니다. (user 또는 admin)")
            return

        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"userType": new_user_type}}
        )

        print("사용자 유형이 변경되었습니다:")
        print("이메일:", user["email"])
        print("이름:", user.get("name"))
        print("이전 유형:", user.get("userType", "user"))
        print("새 유형:", new_user_type)

    except Exception as e:
        print("사용자 유형 변경 중 오류 발생:", e)
    finally:
        client.close()
        print("데이터베이스 연결이 종료되었습니다.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("사용법: python scripts/change_user_type.py <이메일> <user|admin>")
        print("예시: python scripts/change_user_type.py user@example.com admin")
        sys.exit(1)

    email_arg = sys.argv[1]
    type_arg = sys.argv[2]

    asyncio.run(change_user_type(email_arg, type_arg))