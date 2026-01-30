# app/services/sites_service.py
from app.config.database import get_db
from app.models.sites_model import Site
from pymongo import ReturnDocument

db = get_db()

def get_all_sites():
    """모든 사이트 리스트 반환"""
    sites = list(db.sites.find({}, {"_id": 0}))
    return sites

def get_site_by_id(site_id: int):
    """site_id로 단일 사이트 조회"""
    return db.sites.find_one({"id": site_id}, {"_id": 0})

def process_site(url: str):
    """사이트 등록 및 기본 분석 결과 생성"""
    # id 자동 증가
    counter = db.counters.find_one_and_update(
        {"_id": "siteid"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    new_id = counter["seq"]

    new_site = Site(
        id=new_id,
        name=url,
        url=url,
        decision="REVIEW",
        riskScore=48.3
    ).model_dump()

    db.sites.insert_one(new_site)
    return new_site