PII_WEIGHTS = {
    "CREDIT_CARD": 12,
    "RESIDENT_ID": 15,
    "PHONE": 5,
    "EMAIL": 4,
    "NAME": 2,
}

MAX_PII_PENALTY = 40


def count_pii(per_item_results: list) -> dict:
    counts = {"TOTAL": 0}
    for r in per_item_results or []:
        if not isinstance(r, dict):
            continue
        finding = r.get("finding") or {}
        if isinstance(finding, dict):
            label = finding.get("label")
        else:
            label = None

        if not label:
            continue

        label = str(label).upper()
        counts[label] = counts.get(label, 0) + 1
        counts["TOTAL"] += 1
    return counts


def compute_pii_penalty(counts: dict):
    penalty = 0
    for label, weight in PII_WEIGHTS.items():
        penalty += counts.get(label, 0) * weight
    return min(penalty, MAX_PII_PENALTY)


def apply_policy(llm_result: dict, findings: dict, rag_score: int):
    counts = count_pii(findings)
    pii_penalty = compute_pii_penalty(counts)

    base = int(rag_score * 0.6 + llm_result["score"] * 0.4)
    final_score = min(100, base + pii_penalty)

    decision = llm_result["decision"]
    if counts["CREDIT_CARD"] >= 1 or counts["RESIDENT_ID"] >= 1:
        decision = "MASK"
    elif counts["TOTAL"] >= 3:
        decision = "MASK"

    llm_result["score"] = final_score
    llm_result["decision"] = decision
    llm_result["pii_counts"] = counts

    return llm_result