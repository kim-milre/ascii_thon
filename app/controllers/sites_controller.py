import json, os
from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from app.services.crawl_service import crawl_and_save
from app.services.detect_service import detect_risks
from app.services.terms_service import fetch_and_store_policies
from app.services.policy_indexer import index_policies
from app.services.rag_service import analyze_findings
from app.services.rag_service import search_legal_evidence
from app.services.llm_quickest import judge_risk
from app.services.mask_service import mask_pii
from app.services.robots_service import fetch_robots_txt, parse_robots_txt, is_allowed, has_ai_crawl_prohibition
from app.services.risk_scoring import count_pii, compute_pii_penalty
from app.services.legal_risk_service import build_legal_risks
from app.services.progress import update_progress
from app.config.database import db, analysis_collection, ensure_policy_indexes

import uuid
import os, anyio
from app.utils.audit import dump_json, dump_text
import random

analysis_collection = db["analysis_results"]


def _quick_decide_without_rag(item: dict) -> dict:
    """
    RAG evidences가 0건일 때 규칙 판정.
    점수 분산을 의도적으로 크게 만든 버전
    """
    label = str(item.get("label", "")).upper()
    conf = float(item.get("confidence", 0) or 0)

    # 타입별 기본 위험도
    base_map = {
        "NAME": 60,
        "EMAIL": 70,
        "PHONE": 75,
        "MOBILE": 78,
        "TEL": 78,
        "ADDRESS": 72,
        "CREDIT_CARD": 95,
        "CARD": 95,
        "PAYMENT": 90,
        "SSN": 98,
        "RRN": 98,
        "주민번호": 98,
        "ID_NUMBER": 95,
    }

    base = base_map.get(label, 40)

    # confidence 영향 완화 (기존 ±15 → ±12)
    score = base + (conf - 0.5) * 12
    score = int(min(100, max(0, score)))

    # 결정 규칙
    high_sensitive = {
        "CREDIT_CARD", "CARD", "PAYMENT",
        "SSN", "RRN", "주민번호", "ID_NUMBER"
    }

    if label in high_sensitive:
        decision = "MASK"
    elif score >= 85:
        decision = "MASK"
    elif score >= 60:
        decision = "REVIEW"
    else:
        decision = "PASS"

    return {
        "decision": decision,
        "score": score,
        "reason": f"RAG=0 rule-based | label={label}, confidence={conf:.2f}",
        "law_evidence": [],
        "site_policy_evidence": [],
    }


def to_json_safe(obj):
    """모든 ObjectId, datetime, set, numpy 타입 등을 안전하게 JSON 직렬화 가능하게 변환"""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode(errors="ignore")
    if isinstance(obj, (set, tuple)):
        return [to_json_safe(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_json_safe(v) for v in obj]
    if hasattr(obj, "item"):  # numpy scalar
        try:
            return obj.item()
        except Exception:
            return str(obj)
    return obj

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def calculate_overall_score(per_item_results: list) -> int:
    """
    항목 개수 + 평균 점수를 함께 반영한 overall score
    """
    if not per_item_results:
        return 0

    mask_items = [
    r for r in per_item_results
    if isinstance(r, dict) and r.get("decision") == "MASK"
]
    review_items = [
    r for r in per_item_results
    if isinstance(r, dict) and r.get("decision") == "REVIEW"
]

    mask_count = len(mask_items)
    review_count = len(review_items)

    mask_avg = (
        sum(r.get("score", 0) for r in mask_items) / mask_count
        if mask_count else 0
    )
    review_avg = (
        sum(r.get("score", 0) for r in review_items) / review_count
        if review_count else 0
    )

    # 기본 가중 평균
    weighted = (
        mask_avg * 1.0 +
        review_avg * 0.5
    )

    # 개수 보정 (중요)
    volume_bonus = 0
    if mask_count >= 4:
        volume_bonus += 15
    elif mask_count == 3:
        volume_bonus += 10
    elif mask_count == 2:
        volume_bonus += 5

    if review_count >= 3:
        volume_bonus += 5

    overall_score = weighted + volume_bonus

    return int(min(100, max(0, overall_score)))


async def list_sites(user_id: str):
    try:
        cursor = analysis_collection.find(
            {"user_id": str(user_id)},
            {"_id": 1, "url": 1, "decision": 1, "riskScore": 1, "status": 1, "timestamp": 1}
        ).sort("_id", -1)
        sites = await cursor.to_list(length=100)
        return to_json_safe(sites)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB fetch error: {e}")


async def process_site(url: str, user_id: str):
    print("PROCESS_SITE_VERSION = 2025-12-21-LEGALRISKS-V2")
    print("process_site file:", os.path.abspath(__file__))
    print("legal_risks init ok")
    run_id = uuid.uuid4().hex[:8]
    legal_risks: list = []

    print(f"🤖 robots.txt 확인 중: {url}")
    parsed = urlparse(url)
    
    robots_txt = await fetch_robots_txt(url)
    ai_blocked = False

    if robots_txt:
        print("ROBOTS RAW >>>")
        print(robots_txt)
        

        robots_lower = robots_txt.lstrip().lower()

        # 🔥 0단계: HTML 반환 = 즉시 차단
        if robots_lower.startswith("<!doctype html") or robots_lower.startswith("<html"):
            blocked_reason = "robots.txt returned HTML error page"
            ai_blocked = True
            robots_blocked = True

        else:
            rules = parse_robots_txt(robots_txt, user_agent="*")
            target_path = parsed.path or "/"

            # 1단계: 기술적 Disallow
            if not is_allowed(target_path, rules):
                blocked_reason = "robots.txt technical block"
                ai_blocked = True

            # 2단계: AI/RAG 목적 명시 차단
            elif has_ai_crawl_prohibition(robots_txt):
                blocked_reason = "robots.txt AI/RAG prohibition"
                ai_blocked = True

        if ai_blocked:
            legal_risks = build_legal_risks(
            url=url,
            robots_txt=robots_txt,
            robots_blocked=ai_blocked,
            ai_prohibited=ai_blocked,
            html=None,
            metadata=None,
            policies=None,
            findings=None,
            per_item_results=None,
        )

            blocked_doc = {
                "url": url,
                "status": "blocked",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "decision": "BLOCKED",
                "riskScore": 0,
                "error": blocked_reason,
                "reason": "robots.txt에서 AI/RAG 목적 접근이 명시적으로 금지되어 있습니다.",
                "unfair_signals": {
                    "robots_txt_blocked": True,
                    "ai_bot_blocked": True,
                    "risk_level": "HIGH"
                },
                "legal_risks": legal_risks,
            }

            inserted = await analysis_collection.insert_one(blocked_doc)
            site_id = str(inserted.inserted_id)

            return {
                "site_id": site_id,
                "url": url,
                "status": "blocked",
                "decision": "BLOCKED",
                "riskScore": 0,
                "cached": False,
                "error": blocked_reason,
                "reason": blocked_doc["reason"],
                "user_id": user_id,
            }

        else:
            print(f"✅ robots.txt 허용")
    else:
        print(f"ℹ️ robots.txt 없음 → 허용")

    existing = await analysis_collection.find_one({"url": url, "user_id": user_id, "status": "completed"})
    if existing:
        print(f"✅ 이미 분석 완료된 URL: (user_id={user_id}): {url}")
        response = {
            "site_id": str(existing["_id"]),
            "url": existing["url"],
            "decision": existing.get("decision", "UNKNOWN"),
            "riskScore": float(existing.get("riskScore", 0)),
            "status": existing.get("status", "completed"),
            "cached": True,
            "user_id": user_id,
        }
        return to_json_safe(response)

    site_doc = {
        "url": url,
        "status": "processing",
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
    }
    inserted = await analysis_collection.insert_one(site_doc)
    site_id = str(inserted.inserted_id)

    try:
        masked_html = ""
        per_item_results = []
        overall_decision = "PASS"

        html, metadata = await crawl_and_save(url)
        await update_progress(site_id, "CRAWLING", 10)
        if not html:
            raise ValueError("Empty HTML content")
        print("✅ 1단계 완료: 크롤링 및 저장 성공")
        

        dump_json(run_id, "crawl", "metadata", to_json_safe(metadata))
        dump_text(run_id, "crawl", "html", html or "")

        text = html_to_text(html)

        findings = detect_risks(text, use_openai=True)
        await update_progress(site_id, "DETECTING_RISKS", 30)
        if not isinstance(findings, dict):
            raise ValueError(f"detect_risks returned non-dict type: {type(findings)}")
        dump_json(run_id, "detect", "findings_raw", to_json_safe(findings))
        print("✅ 2단계 완료: 리스크 탐지 성공")


        print("DETECT_RETURN_KEYS:", findings.keys())
        print("DETECT_SAMPLE:", str(findings)[:2000])

        await update_progress(site_id, "RAG_SEARCH", 55)
        policies = await fetch_and_store_policies(url)
        if policies:
            await index_policies(url, policies)
            print(f"✅ 3단계 완료: {len(policies)}개의 약관 인덱싱 완료")
            

        else:
            print("⚠️ 약관 탐색 실패 또는 존재하지 않음")
        

        # merged_findings 구성
        merged_findings = []
        for category, items in (findings or {}).items():
            if not isinstance(items, list):
                continue
            for f in items:
                if isinstance(f, dict):
                    item = {**f}
                    item.setdefault("type", category)
                else:
                    item = {"type": category, "span": str(f)}
                if not str(item.get("span", "")).strip():
                    continue
                merged_findings.append(item)

        if not merged_findings:
            print("⚠️ 탐지 결과 없음, RAG/판정 단계 생략.")
            per_item_results = []
        else:
            print(f"🔎 개별 RAG/판정 시작 — {len(merged_findings)}건")

        per_item_results = []
        for i, f in enumerate(merged_findings, 1):
            item = dict(f) if isinstance(f, dict) else {"type": "pii", "span": str(f)}
            item.setdefault("type", item.get("type", "pii"))
            span = str(item.get("span", "")).strip()

            item_rec = {"index": i, "finding": to_json_safe(item), "evidences": [], "judge": {}, "error": None}
            single_decision = None

            try:
                evidences = await analyze_findings(url, [item], html_context=html)
                if not isinstance(evidences, list):
                    evidences = []
                item_rec["evidences"] = to_json_safe(evidences)

                if len(evidences) == 0:
                    single_decision = _quick_decide_without_rag(item)
                    item_rec["judge"] = {
                        "mode": "rule_based_no_rag",
                        "payload": {"finding": to_json_safe(item), "evidences": []},
                        "result": to_json_safe(single_decision),
                    }
                else:
                    payload = {
                        "findings": {
                            "pii": [item]
                        },
                        "evidences": evidences
                    }
                    item_rec["judge"] = {"mode": "llm", "payload": to_json_safe(payload)}
                    single_decision = await anyio.to_thread.run_sync(judge_risk, payload)
                    item_rec["judge"]["result"] = to_json_safe(single_decision)

            except Exception as e:
                item_rec["error"] = str(e)
                print(f"❌ 개별 판정 실패 [{i}] {item}: {e}")
                if single_decision is None:
                    single_decision = {
                        "decision": "REVIEW",
                        "score": 50,
                        "reason": f"judge 실패: {e}",
                        "law_evidence": [],
                        "site_policy_evidence": [],
                    }
                    item_rec.setdefault("judge", {})
                    item_rec["judge"]["result"] = to_json_safe(single_decision)
            finally:
                decision_str = str(single_decision.get("decision", "REVIEW")).upper()
                try:
                    score_val = int(single_decision.get("score", 50))
                except Exception:
                    score_val = 50

                per_item_results.append({
                    "finding": {
                        "span": item.get("span"),
                        "label": item.get("label") or item.get("type"),  # 🔥 핵심
                    },
                    "decision": decision_str,
                    "score": score_val,
                    "reason": single_decision.get("reason", ""),
                    "law_evidence": single_decision.get("law_evidence", []),
                    "site_policy_evidence": single_decision.get("site_policy_evidence", []),
                })

                print(
                    f"  · [{i}/{len(merged_findings)}] {item.get('type')} | span='{span[:20]}' | score={score_val} | decision={decision_str}")
                dump_json(run_id, "items", f"items_{i:03d}", to_json_safe(item_rec))
        
        await update_progress(site_id, "LLM_JUDGMENT", 75)
        # ====== 3) Overall Score 계산 ======
        overall_score = calculate_overall_score(per_item_results)

        # ====== 3.1) PII 개수 기반 정책 보정 ======
        raw_counts = count_pii(per_item_results)

        if isinstance(raw_counts, list):
            counts = {}
            for item in raw_counts:
                if isinstance(item, dict):
                    k = item.get("label")
                    v = item.get("count", 0)
                    if k:
                        counts[k] = v
            counts["TOTAL"] = sum(counts.values())
        else:
            counts = raw_counts
        pii_penalty = compute_pii_penalty(counts)

        mask_count = sum(1 for r in per_item_results if r.get("decision") == "MASK")
        review_count = sum(1 for r in per_item_results if r.get("decision") == "REVIEW")
        pass_count = sum(1 for r in per_item_results if r.get("decision") == "PASS")

        # 점수 보정
        overall_score = min(100, int(overall_score + pii_penalty))

        # 강제 결정 규칙
        overall_decision = "PASS"

        if counts.get("CREDIT_CARD", 0) >= 1 or counts.get("RESIDENT_ID", 0) >= 1:
            overall_decision = "MASK"
        elif counts.get("TOTAL", 0) >= 3:
            overall_decision = "MASK"

        else:
            overall_decision = "PASS"

        print(f"📊 Overall Score 계산 완료: {overall_score} (MASK {mask_count} / REVIEW {review_count} / PASS {pass_count})")

        # ====== 4) 페이지 단위 마스킹 ======
        masked_html = ""
        if per_item_results:
            _mask = mask_pii(
                html,
                {
                    "result": {"decision": overall_decision, "score": int(overall_score)},
                    "perItemResults": per_item_results
                }
            )
            masked_html = _mask.get("masked_html") if isinstance(_mask, dict) else str(_mask)
            print(f"✅ 마스킹 완료: decision={overall_decision}, overall_score={overall_score}")
            
        else:
            print("ℹ️ 탐지 결과 없음 → 마스킹 생략")

        # ====== 4.5) 최종 결정 근거 요약 생성 ======
        def _dedup_keep_order(seq):
            seen, out = set(), []
            for s in seq:
                if not s:
                    continue
                if s in seen:
                    continue
                seen.add(s)
                out.append(s)
            return out

        if per_item_results:
            selected = [r for r in per_item_results if str(r.get("decision")).upper() == overall_decision]
            if not selected:
                selected = sorted(per_item_results, key=lambda r: r.get("score", 0), reverse=True)[:3]

            counts = {
                "MASK": sum(1 for r in per_item_results if r["decision"] == "MASK"),
                "REVIEW": sum(1 for r in per_item_results if r["decision"] == "REVIEW"),
                "PASS": sum(1 for r in per_item_results if r["decision"] == "PASS"),
            }
            reason_text = f"MASK {counts['MASK']}건 / REVIEW {counts['REVIEW']}건 / PASS {counts['PASS']}건"

            law_evi = []
            site_evi = []

            for item in selected:
                if not isinstance(item, dict):
                    continue

                law_list = item.get("law_evidence")
                if isinstance(law_list, list):
                    for x in law_list:
                        if isinstance(x, (str, int, float)):
                            law_evi.append(str(x))

                policy_list = item.get("site_policy_evidence")
                if isinstance(policy_list, list):
                    for x in policy_list:
                        if isinstance(x, (str, int, float)):
                            site_evi.append(str(x))

            law_evi = _dedup_keep_order(law_evi)[:5]
            site_evi = _dedup_keep_order(site_evi)[:5]
        else:
            reason_text = "탐지된 리스크 없음"
            law_evi, site_evi = [], []

        legal_risks = build_legal_risks(
            url=url,
            robots_txt=robots_txt,
            robots_blocked=False,
            ai_prohibited=False,
            html=html,
            metadata=metadata if isinstance(metadata, dict) else None,
            policies=policies,
            findings=findings,
            per_item_results=per_item_results,
        )

        # ====== 5) 분석 결과 저장 문서 구성 ======
        final_doc = {
            "url": url,
            "metadata": to_json_safe(metadata),
            "findings": to_json_safe(findings),
            "decision": overall_decision,
            "riskScore": float(overall_score),
            "legal_risks": to_json_safe(legal_risks),
            "explain": {
                "reason": reason_text,
                "law_evidence": law_evi,
                "site_policy_evidence": site_evi,
            },
            "perItemResults": to_json_safe(per_item_results),
            "masked_html": masked_html,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
        }

        await analysis_collection.update_one(
            {"_id": inserted.inserted_id},
            {"$set": final_doc}
        )

        # ====== 6) Output dump - MASK reason 중 랜덤 선택 + site_policy_evidence 제거 ======
        mask_reasons = []
        if final_doc["decision"] == "MASK":
            for r in per_item_results:
                if str(r.get("decision", "")).upper() == "MASK":
                    reason = r.get("reason", "")
                    if reason:
                        mask_reasons.append(reason)

        selected_reason = random.choice(mask_reasons) if mask_reasons else ""

        dump_json(run_id, "output", "final", {
            "url": url,
            "decision": final_doc["decision"],
            "riskScore": final_doc["riskScore"],
            "has_masked_html": bool(final_doc.get("masked_html")),
            "reason": selected_reason,
            "law_evidence": law_evi,
            "user_id": user_id,
        })

        print("✅ 6단계 완료: 분석 결과 저장 성공")
        await update_progress(site_id, "SAVING", 100)

        response = {
            "site_id": site_id,
            "url": url,
            "decision": final_doc["decision"],
            "riskScore": final_doc["riskScore"],
            "status": "completed",
            "cached": False,
            "user_id": user_id,
        }
        print(f"📤 최종 응답: {response}")
        return to_json_safe(response)

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 분석 중 오류 발생: {error_msg}")

        await analysis_collection.update_one(
            {"_id": ObjectId(site_id)},
            {"$set": {"status": "failed", "error": error_msg}}
        )

        return {
            "site_id": site_id,
            "url": url,
            "status": "failed",
            "error": error_msg,
            "user_id": user_id,
            "cached": False,
        }


async def get_site_detail(site_id: str, user_id: str):
    site = await analysis_collection.find_one({
        "_id": ObjectId(site_id),
        "user_id": str(user_id)
    })

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    site["_id"] = str(site["_id"])
    return site


async def delete_site(site_id: str, user_id: str):
    """특정 결과 삭제 (자기 결과만 가능)"""
    res = await analysis_collection.delete_one({"_id": ObjectId(site_id), "user_id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Result not found or not owned by this user")
    return {"message": f"✅ Site {site_id} deleted for user {user_id}"}


async def delete_all_sites(user_id: str):
    """현재 사용자 결과 전체 삭제"""
    res = await analysis_collection.delete_many({"user_id": user_id})
    return {
        "message": f"🧹 {res.deleted_count}개의 사이트 분석 결과가 삭제되었습니다.",
        "deleted_count": res.deleted_count,
    }