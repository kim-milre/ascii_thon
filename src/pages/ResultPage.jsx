// src/pages/ResultPage.jsx
import React from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { complianceAPI } from "../api/api"
import { ClipLoader } from "react-spinners"
import styled from "@emotion/styled"
import DOMPurify from "dompurify"
import { Toaster, toast } from "react-hot-toast"


const Background = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 15rem;
  background: linear-gradient(180deg, #eef2ff 0%, #ffffff 65%);
  z-index: -1;
`

const PageContainer = styled.div`
  position: relative;
  width: 100%;
  min-height: 100vh;
  padding: 8rem 4rem 6rem;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-x: hidden;
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 960px;
  margin-bottom: 2rem;
`

const Title = styled.h2`
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
`

const DeleteButton = styled.button`
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 10px;
  padding: 0.6rem 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
  &:hover {
    background: #dc2626;
  }
`

const InfoCard = styled.div`
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-radius: 12px;
  padding: 2rem;
  max-width: 720px;
  text-align: center;
  color: #92400e;
  font-size: 1.05rem;
  line-height: 1.6;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
  margin-top: 2rem;
`

const Label = styled.p`
  font-weight: 600;
  margin-top: 1.5rem;
  color: #374151;
`

const Value = styled.p`
  background: white;
  padding: 0.8rem 1rem;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  color: #374151;
  word-break: break-all;
`

const Section = styled.div`
  margin-top: 2rem;
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
  width: 100%;
  max-width: 960px;
  position: relative;
  z-index: 10;
`

const SectionTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e3a8a;
  margin-bottom: 1rem;
  border-bottom: 2px solid #e0e7ff;
  padding-bottom: 0.5rem;
`

const Reason = styled.p`
  color: #374151;
  font-size: 1rem;
  line-height: 1.6;
  white-space: pre-line;
`

const EvidenceList = styled.ul`
  margin-top: 1rem;
  padding-left: 1.25rem;
`

const EvidenceItem = styled.li`
  margin-bottom: 0.75rem;
  color: #1e293b;
  line-height: 1.6;
  background: #f9fafb;
  padding: 0.9rem 1rem;
  border-radius: 8px;
  border-left: 4px solid #818cf8;
  font-family: 'Pretendard', sans-serif;
  font-size: 0.98rem;
`

const ChartContainer = styled.div`
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 3rem 0;
`

const CircleWrapper = styled.div`
  position: relative;
  width: 160px;
  height: 160px;
  display: flex;
  justify-content: center;
  align-items: center;
`

const CircleChart = styled.svg`
  width: 160px;
  height: 160px;
  transform: rotate(-90deg);
`

const CircleBg = styled.circle`
  fill: none;
  stroke: #e5e7eb;
  stroke-width: 10;
`

const CircleProgress = styled.circle`
  fill: none;
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.6s ease;
  ${({ level }) =>
    level === "LOW"
      ? `stroke: #22c55e;`
      : level === "MEDIUM"
      ? `stroke: #facc15;`
      : `stroke: #ef4444;`}
`

const ChartLabel = styled.div`
  position: absolute;
  top: 50%;
  left: 52%;
  transform: translate(-50%, -50%);
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  text-align: center;
`

const PreviewBox = styled.div`
  margin-top: 1rem;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  padding: 1rem;
  min-height: 250px;
  overflow-y: auto;
`
const PreviewText = styled.div`
  white-space: pre-line;
  line-height: 1.9;
  font-size: 1rem;
  color: #1f2937;

  .mask-name {
    background: rgba(239, 68, 68, 0.12);
    color: #b91c1c;
    padding: 0 0.25rem;
    border-radius: 4px;
    font-weight: 600;
  }

  .mask-phone {
    background: rgba(59, 130, 246, 0.12);
    color: #1d4ed8;
    padding: 0 0.25rem;
    border-radius: 4px;
    font-weight: 600;
  }

  .mask-email {
    background: rgba(16, 185, 129, 0.12);
    color: #047857;
    padding: 0 0.25rem;
    border-radius: 4px;
    font-weight: 600;
  }

    .mask-card {
    background: rgba(168, 85, 247, 0.12);
    color: #6d28d9;
    padding: 0 0.25rem;
    border-radius: 4px;
    font-weight: 600;
  }

  .mask-rrn {
    background: rgba(245, 158, 11, 0.14);
    color: #92400e;
    padding: 0 0.25rem;
    border-radius: 4px;
    font-weight: 600;
  }

  .mask-unknown {
    background: rgba(107, 114, 128, 0.12);
    color: #374151;
    padding: 0 0.25rem;
    border-radius: 4px;
    font-weight: 600;
  }
`

const FoldBox = styled.details`
  margin-top: 1.5rem;
  border-top: 1px dashed #e5e7eb;
  padding-top: 1rem;

  summary {
    cursor: pointer;
    font-weight: 600;
    color: #4f46e5;
  }
`

const HtmlPreview = styled.div`
  margin-top: 1rem;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  background: #fafafa;
`

const RiskGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
`

const RiskCard = styled.div`
  border-radius: 14px;
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  background: ${({ level }) =>
    level === "HIGH"
      ? "#fef2f2"
      : level === "MEDIUM"
      ? "#fffbeb"
      : "#f0fdf4"};

  border-left: 6px solid
    ${({ level }) =>
      level === "HIGH"
        ? "#ef4444"
        : level === "MEDIUM"
        ? "#f59e0b"
        : "#22c55e"};
`

const RiskTitle = styled.h4`
  font-size: 1.05rem;
  font-weight: 700;
  color: #1f2937;
`

const RiskLevel = styled.span`
  display: inline-block;
  margin-top: 0.4rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: ${({ level }) =>
    level === "HIGH"
      ? "#b91c1c"
      : level === "MEDIUM"
      ? "#92400e"
      : "#065f46"};
`

const RiskSummary = styled.p`
  margin-top: 0.8rem;
  font-size: 0.95rem;
  line-height: 1.6;
  color: #374151;
`

const LegalBasisList = styled.ul`
  margin-top: 0.8rem;
  padding-left: 1.1rem;
`

const LegalBasisItem = styled.li`
  font-size: 0.9rem;
  color: #1e293b;
  margin-bottom: 0.4rem;
`

function normalizeRiskLevel(risk, overallScore) {
  if (overallScore >= 70) return "HIGH"
  if (overallScore >= 40) return "MEDIUM"
  return risk.level || "LOW"
}

function extractMainContent(html) {
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, "text/html")
    const main =
      doc.querySelector("main") ||
      doc.querySelector("article") ||
      doc.querySelector("#content") ||
      doc.querySelector(".content") ||
      doc.body
    return main.innerHTML
  } catch (err) {
    console.error("본문 추출 실패:", err)
    return html
  }
}
function cleanAndExtractText(html) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html || "", "text/html")

  const main =
    doc.querySelector("article") ||
    doc.querySelector("main") ||
    doc.querySelector("#content") ||
    doc.querySelector(".content") ||
    doc.body

  // 1) 본문 DOM 내부에서 제거 (핵심: main 기준으로 제거해야 효과가 있음)
  const removeSelectors = [
    "img",
    "picture",
    "svg",
    "video",
    "audio",
    "iframe",
    "button",
    "nav",
    "aside",
    "footer",
    "header",
    "form",
    "input",
    "select",
    "textarea",
    "script",
    "style",
    "noscript",
    ".advertisement",
    ".related",
    ".subscribe",
    ".share",
    ".sns",
    ".comment",
    ".comments",
  ]

  removeSelectors.forEach(sel => {
    main.querySelectorAll(sel).forEach(el => el.remove())
  })

  // 2) 링크는 텍스트만 남기고 싶으면 a 태그 풀기 (선택)
  main.querySelectorAll("a").forEach(a => {
    const span = doc.createElement("span")
    span.textContent = a.textContent || ""
    a.replaceWith(span)
  })

  // 3) 마스킹 span은 유지한 채로 HTML 얻기
  const cleanedHtml = main.innerHTML || ""

  // 4) sanitize해서 XSS 막고, class 기반 스타일은 유지
  return DOMPurify.sanitize(cleanedHtml, {
    ALLOWED_TAGS: [
      "p","br","div","span","strong","b","em","i","u",
      "ul","ol","li","blockquote","pre","code",
      "h1","h2","h3","h4","h5","h6"
    ],
    ALLOWED_ATTR: ["class"],
  })
}

function ResultPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ["siteResult", id],
    queryFn: () => complianceAPI.getSiteResult(id),

  })

  const handleDelete = async () => {
    if (!window.confirm("정말로 이 분석 결과를 삭제할까요?")) return
    try {
      await complianceAPI.deleteSite(id)
      toast.success("삭제 완료")
      queryClient.invalidateQueries(["sitesList"])
      setTimeout(() => navigate("/list"), 800)
    } catch {
      toast.error("삭제 중 오류 발생")
    }
  }

  if (isLoading)
    return (
      <>
        <Background />
        <PageContainer style={{ textAlign: "center" }}>
          <ClipLoader color="#6366f1" size={40} />
          <p style={{ marginTop: "1rem" }}>결과를 불러오는 중...</p>
        </PageContainer>
      </>
    )

  if (error)
    return (
      <>
        <Background />
        <PageContainer>에러: {error.message}</PageContainer>
      </>
    )

  const site = data?.data ?? data
  if (!site)
    return (
      <>
        <Background />
        <PageContainer>분석 결과를 찾을 수 없습니다.</PageContainer>
      </>
    )
  const legalRisks = site?.explain?.legal_risks ?? site?.legal_risks ?? []
  console.log("LEGAL RISKS RAW:", legalRisks)

  if (site.status === "blocked" || site.decision === "BLOCKED") {
  return (
    <>
      <Background />
      <PageContainer>
        <Toaster position="top-center" />
        <Header>
          <Title>크롤링 차단됨</Title>
          <DeleteButton onClick={handleDelete}>삭제</DeleteButton>
        </Header>

        <InfoCard>
          <h2>🚫 robots.txt 정책에 의해 수집이 차단된 사이트입니다 🚫</h2>

          <p style={{ marginTop: "1rem" }}>
            이 URL은 사이트의 <strong>robots.txt</strong> 설정에 따라
            자동화된 크롤링 접근이 명시적으로 제한되어 있습니다.
          </p>

          <p style={{ marginTop: "0.75rem" }}>
            본 서비스는 해당 접근 제한을 존중하여
            콘텐츠 수집 및 분석을 중단하였습니다.
          </p>

          <hr style={{ margin: "1.5rem 0", borderColor: "#fed7aa" }} />

          <h3><p style={{ fontWeight: 600 }}>
            ⚖️ 법적 판단 근거
          </p>
          </h3>

          <p style={{ marginTop: "1rem" }}>
            robots.txt를 통해 크롤링 목적의 접근을 금지한 사이트의 콘텐츠를
            무단으로 수집·분석하는 행위는,
          </p>

          <p style={{ marginTop: "0.5rem", fontWeight: 600 }}>
            부정경쟁방지법 제2조 제1호 (차)목
          </p>

          <p style={{ marginTop: "0.25rem", fontStyle: "italic" }}>
            “타인의 성과를 공정한 상거래 관행에 반하여 무단으로 이용하는 행위”
          </p>

          <hr style={{ margin: "1.5rem 0", borderColor: "#fed7aa" }} />

          <p>
            이에 따라 본 서비스는 법적 분쟁 가능성과 이용자 책임 발생을
            사전에 방지하기 위해,
          </p>

          <p style={{ marginTop: "0.25rem" }}>
            아래 URL에 대한 분석을 수행하지 않았습니다.
          </p>

          <div
            style={{
              marginTop: "1rem",
              padding: "0.75rem 1rem",
              background: "#fff",
              border: "1px dashed #fdba74",
              borderRadius: "8px",
              fontSize: "0.95rem",
              color: "#92400e",
              wordBreak: "break-all",
            }}
          >
            {site.url}
          </div>
        </InfoCard>
        {Array.isArray(legalRisks) && legalRisks.length > 0 && (
          <Section>
            <SectionTitle>차단 사유에 대한 법적 리스크</SectionTitle>

            <RiskGrid>
              {legalRisks.map((risk, idx) => (
                <RiskCard key={idx} level={risk.level || "HIGH"}>
                  <RiskTitle>{risk.title}</RiskTitle>
                  <RiskSummary>{risk.summary}</RiskSummary>
                </RiskCard>
              ))}
            </RiskGrid>
          </Section>
        )}
      </PageContainer>
    </>
  )
}

      // ===== 정확한 데이터 매핑 =====
    const decision = site.decision
    const score = site.riskScore ?? 0

    // AI 판단 요약
    const summaryReason = site.explain?.reason ?? "AI 판단 요약 정보가 없습니다."

    // AI 판단 과정 (항목별)
    const perItemResults = Array.isArray(site.perItemResults)
      ? site.perItemResults
      : []

    // 법적 근거 (요약)
    const lawEvidences = Array.isArray(site.explain?.law_evidence)
      ? site.explain.law_evidence
      : []

  let level = "LOW"
  if (score >= 70) level = "HIGH"
  else if (score >= 40) level = "MEDIUM"


  return (
    <>
      <Background />
      <PageContainer>
        <Toaster position="top-center" />
        <Header>
          <Title>AI 판단 결과</Title>
          <DeleteButton onClick={handleDelete}>삭제</DeleteButton>
        </Header>

        <Label>URL</Label>
        <Value>{site.url}</Value>

        <Label>AI 판단</Label>
        <Value>{decision || "N/A"}</Value>

        <ChartContainer>
          <CircleWrapper>
            <CircleChart>
              <CircleBg cx="80" cy="80" r="70" />
              <CircleProgress
                cx="80"
                cy="80"
                r="70"
                level={level}
                strokeDasharray={2 * Math.PI * 70}
                strokeDashoffset={(1 - score / 100) * 2 * Math.PI * 70}
              />
            </CircleChart>
            <ChartLabel>{score ? `${score.toFixed(0)}%` : "N/A"}</ChartLabel>
          </CircleWrapper>
        </ChartContainer>


        <Section>
          <SectionTitle>AI 판단 요약</SectionTitle>
          <Reason>{summaryReason}</Reason>
        </Section>

        {Array.isArray(legalRisks) && legalRisks.length > 0 && (
          <Section>
            <SectionTitle>법적 리스크 분석</SectionTitle>

            <RiskGrid>
              {legalRisks.map((risk, idx) => {
                  const level = normalizeRiskLevel(risk, score)

                  return (
                    <RiskCard key={idx} level={level}>
                      <RiskTitle>{risk.title}</RiskTitle>

                      <RiskLevel level={level}>
                        위험도: {level}
                      </RiskLevel>

                      <RiskSummary>{risk.summary || risk.reason}</RiskSummary>
                    </RiskCard>
                  )
                })}
            </RiskGrid>
          </Section>
        )}


        {perItemResults.length > 0 && (
          <Section>
            <SectionTitle>AI 판단 과정 및 기준</SectionTitle>
            <EvidenceList>
              {perItemResults.map((item, idx) => (
                <EvidenceItem key={idx}>
                  <strong>대상:</strong> {item.finding?.span || "알 수 없음"}<br />
                  <strong>유형:</strong> {item.finding?.label}<br />
                  <strong>판정:</strong> {item.decision} (점수 {item.score})<br />
                  <strong>판단 근거:</strong><br />
                  {item.reason}
                </EvidenceItem>
              ))}
            </EvidenceList>
          </Section>
        )}

        {/* ✅ 관련 법적 근거 */}
        {Array.isArray(lawEvidences) && lawEvidences.length > 0 && (
          <Section>
            <SectionTitle>관련 법적 근거</SectionTitle>
            <EvidenceList>
              {lawEvidences.map((item, i) => (
                <EvidenceItem key={i}>{item}</EvidenceItem>
              ))}
            </EvidenceList>
          </Section>
        )}

        {/* ✅ 마스킹 미리보기 */}
        {/* ===== 텍스트 기사 뷰 ===== */}
        <Section>
          <SectionTitle>기사 본문 (텍스트)</SectionTitle>
            <PreviewText
              dangerouslySetInnerHTML={{
                __html: cleanAndExtractText(site.masked_html || "")
              }}
            />
        </Section>

        {/* ===== 접기: 원문 HTML ===== */}
        <Section>
          <SectionTitle>마스킹된 전체 본문</SectionTitle>
          <FoldBox>
            <summary>원문 HTML 펼치기</summary>
            <HtmlPreview
              dangerouslySetInnerHTML={{
                __html: DOMPurify.sanitize(site.masked_html || "<p>마스킹 결과가 없습니다.</p>"),
              }}
            />
          </FoldBox>
        </Section>
      </PageContainer>
    </>
  )
}

export default ResultPage