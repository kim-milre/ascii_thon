class AnalysisResultResponse(BaseModel):
    url: str
    decision: Optional[str] = None
    riskScore: Optional[float] = None
    has_masked_html: Optional[bool] = False
    law_evidence: Optional[List[str]] = []   # ✅ 추가
    site_policy_evidence: Optional[List[str]] = []  # ✅ 추가
    user_id: Optional[str] = None