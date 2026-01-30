# # app/controllers/analyze_controller.py
# from datetime import datetime
# from urllib.parse import urlparse
# from bs4 import BeautifulSoup
# from bson import ObjectId
# from fastapi import HTTPException
# import os, json

# from app.config.database import analysis_collection
# from app.services.robots_service import fetch_robots_txt, parse_robots_txt, is_allowed
# from app.services.crawl_service import crawl_and_save
# from app.services.detect_service import detect_risks
# from app.services.llm_quickest import judge_risk
# from app.services.mask_service import mask_pii


# def html_to_text(html: str) -> str:
#     soup = BeautifulSoup(html or "", "html.parser")
#     return soup.get_text(" ", strip=True)


# async def process_analysis(url: str):
#     print(f"📡 분석 요청 수신: {url}")
#     if not url:
#         raise HTTPException(status_code=400, detail="Missing URL")


#     robots_txt = await fetch_robots_txt(url)
#     if robots_txt:
#         rules = parse_robots_txt(robots_txt)
#         path = urlparse(url).path or "/"
#         if not is_allowed(path, rules):
#             raise HTTPException(status_code=451, detail="Blocked by robots.txt")


#     try:
#         crawl_ret = await crawl_and_save(url)
#         print("✅ 1단계 완료: 크롤링 성공")
#     except Exception as e:
#         print(f"❌ 크롤링 실패: {e}")
#         raise HTTPException(status_code=500, detail=f"Crawl failed: {e}")

#     html, metadata = "", {}
#     if isinstance(crawl_ret, tuple) and len(crawl_ret) == 2:
#         html, metadata = crawl_ret
#     elif isinstance(crawl_ret, dict):
#         html = crawl_ret.get("html") or crawl_ret.get("a_div_html") or ""
#         metadata = crawl_ret.get("metadata") or {}
#     elif isinstance(crawl_ret, str) and os.path.isfile(crawl_ret):
#         with open(crawl_ret, "r", encoding="utf-8") as f:
#             payload = json.load(f)
#         html = payload.get("html") or payload.get("a_div_html") or ""
#         metadata = payload.get("metadata") or {}
#     else:
#         raise HTTPException(status_code=500, detail="Unexpected crawl return type from crawl_service")


#     text = html_to_text(html)
#     if not text.strip():
#         raise HTTPException(status_code=422, detail="Empty or non-analyzable HTML content.")
#     findings = detect_risks(text, use_openai=True)
#     print("✅ 2단계 완료: 리스크 탐지 성공")

#     print("DETECT_RETURN_KEYS:", findings.keys())
#     print("DETECT_SAMPLE:", str(findings)[:2000])

#     decision = judge_risk({
#         "findings": findings,
#         "evidences": [],
#         "terms": None,
#         "rag_score": 50.0
#     })
#     print(f"✅ 3단계 완료: 판단 결과 = {decision}")

#     per_item_results = []

#     for item in findings.get("pii", []):
#         per_item_results.append({
#             "finding": {
#                 "label": item["label"],
#                 "span": item["span"]
#             },
#             "decision": "MASK",   # 지금은 무조건 MASK로 테스트
#             "score": int(item.get("confidence", 0.7) * 100)
#         })

#     print("PER_ITEM_COUNT:", len(per_item_results))
#     print("PER_ITEM_SAMPLE:", per_item_results[:20])
    
#     print("HTML_IS_HTML:", "<" in html and ">" in html)
#     print("HTML_PREFIX:", html[:200])
#     print("TARGETS_DEBUG:", [(r["finding"]["label"], r["finding"]["span"]) for r in per_item_results[:20]])

#     masked = mask_pii(
#         html,
#         {
#             "result": {
#                 "decision": decision.get("decision", "REVIEW"),
#                 "score": decision.get("score", 50),
#             },
#             "perItemResults": per_item_results,
#         }
#     )
#     if not isinstance(masked, dict):
#         masked = {"masked_html": str(masked)}
#     print("✅ 4단계 완료: 마스킹 성공")


#     doc = {
#         "_id": ObjectId(),
#         "url": url,
#         "timestamp": datetime.now().isoformat(),
#         "metadata": metadata,
#         "decision": decision.get("decision", "REVIEW"),
#         "risk_score": decision.get("score", 50.0),
#         "findings": findings,
#         "masked_html": masked.get("masked_html", ""),
#     }

#     result = await analysis_collection.insert_one(doc)
#     print(f"✅ 5단계 완료: MongoDB 저장 성공 ({result.inserted_id})")


#     return {
#         "_id": str(result.inserted_id),
#         "url": url,
#         "decision": decision.get("decision", "REVIEW"),
#         "riskScore": decision.get("score", 50.0),
#         "masked_html": masked.get("masked_html", ""),
#         "site_id": str(result.inserted_id),
#         "message": "✅ Analysis completed and saved to MongoDB.",
#     }