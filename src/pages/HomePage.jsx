/* src/pages/HomePage.jsx. */
import React, { useEffect, useState } from 'react';
import styled from '@emotion/styled';
import ProgressBar from '../components/ProgressBar';

import { useNavigate } from 'react-router-dom';
import { complianceAPI } from '../api/api';
import { toast } from 'react-toastify';
import loader from '../assets/loader.gif';
import { useAuth } from '../contexts/AuthContext';
import { FaUser, FaCrown } from 'react-icons/fa';

const STEP_LABEL = {
  CRAWLING: '웹 페이지를 수집하고 있습니다',
  DETECTING_RISKS: '개인정보 및 위험 요소를 탐지하고 있습니다',
  RAG_SEARCH: '관련 법령과 약관을 분석하고 있습니다',
  LLM_JUDGMENT: 'AI가 법적 리스크를 판단하고 있습니다',
  MASKING: '민감 정보를 안전하게 마스킹하고 있습니다',
  SAVING: '분석 결과를 저장하고 있습니다',
};

const TopBackground = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: calc(100vh + 20rem);
  z-index: -2;
  background:
    radial-gradient(circle closest-side at 30% 75%, rgba(99, 102, 241, 0.12) 0%, rgba(255, 255, 255, 0) 5%),
    linear-gradient(160deg, rgba(242, 255, 230, 0.95) 5%, rgba(255, 255, 255, 0.98) 25%, rgba(230, 232, 255, 0.5) 65%, rgba(99, 102, 241, 0.18) 100%);
`;



const Container = styled.div`
  text-align: center;
  padding: 10rem 1rem 6rem;
  position: relative;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const UserSection = styled.div`
  position: absolute;
  top: 1.5rem;
  right: 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f1f5f9;
  border-radius: 20px;
  padding: 0.5rem 1rem;
  color: #374151;
  font-weight: 500;
`;

const IconButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.5rem 0.8rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.3s ease;

  &:hover {
    background: #4f46e5;
  }
`;

const Title = styled.h1`
  font-size: 3rem;
  margin-bottom: 1.5rem;
  color: #111827;
  font-weight: 800;
`;

const Subtitle = styled.p`
  font-size: 1.2rem;
  color: #4b5563;
  margin-bottom: 3.5rem;
`;

const INPUT_HEIGHT = '56px';

const InputArea = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.8rem;
  width: 70%;
  max-width: 900px;
  margin-top: 2rem;
`;

const InputWrapper = styled.div`
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;    
  height: ${INPUT_HEIGHT};
  box-sizing: border-box;
  border: 2px solid #6366f1;
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
`;

const Input = styled.input`
  flex: 1;
  border: none;
  outline: none;
  font-size: 1.05rem;
  color: #111827;
  background: transparent;
  height: 100%;
  display: flex;
  align-items: center;     
  padding: 0 1.2rem;
  margin: 0;
  box-sizing: border-box;

  &::placeholder {
    color: #9ca3af;
  }
`;


const Button = styled.button`
  height: ${INPUT_HEIGHT};
  line-height: ${INPUT_HEIGHT};
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  border: 2px solid #6366f1;
  border-radius: 10px;
  padding: 0 1.6rem;
  background: #6366f1;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;

  &:hover {
    background: #4f46e5;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const IntroWrapper = styled.div`
  width: 100%;
  max-width: 960px;
  margin: 4rem auto;
  padding: 3rem 2rem;
  background: #fff;
  border-radius: 1rem;
  box-shadow: 0 0 20px rgba(0,0,0,0.05);
  text-align: center;
`

const IntroTitle = styled.h2`
  font-size: 2rem;
  line-height: 1.2;
  color: #1e3a8a;
  margin-bottom: 1.25rem;
`

const IntroText = styled.p`
  font-size: 1.1rem;
  line-height: 1.8;
  color: #333;
  margin: 0.75rem 0;`

const isValidUrl = (str) => {
  try {
    const url = new URL(str);
    return ['http:', 'https:'].includes(url.protocol);
  } catch {
    return false;
  }
};

const escapeHTML = (str) =>
  String(str).replace(/[&<>"']/g, (m) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
  }[m]));

function HomePage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const [siteId, setSiteId] = useState(null);
  const [progress, setProgress] = useState(null);
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

//   useEffect(() => {
//   if (!siteId) return;
//
//   const timer = setInterval(async () => {
//       try {
//         const raw = await complianceAPI.getSiteProgress(siteId);
//
//         // API 응답 정규화
//         const normalizedProgress =
//           raw?.progress ??
//           raw?.data?.progress ??
//           raw;
//
//         setProgress(normalizedProgress);
//
//         const percent = normalizedProgress?.percent;
//         if (percent >= 100) {
//           clearInterval(timer);
//           setLoading(false);
//           navigate(`/result/${siteId}`);
//         }
//     } catch (e) {
//       console.error('progress fetch error', e);
//     }
//   }, 1000);
//
//   return () => clearInterval(timer);
//   }, [siteId, navigate]);

  const handleAnalyze = async () => {
    if (!url.trim()) return toast.warn('URL을 입력해주세요!');
    if (!isValidUrl(url)) return toast.error('올바른 URL 형식만 입력 가능합니다.');

    setLoading(true);
    setProgress(null);
    setSiteId(null);
    try {
//       const result = await complianceAPI.runFullAnalysis(url);
//       setSiteId(result.site_id);
      const result = await complianceAPI.runFullAnalysis(url);
      navigate(`/result/${result.site_id}`);
    } catch (error) {
      setLoading(false);
      toast.error('분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    }
  };
  const step = progress?.step;
  const percent = progress?.percent;

  const handleLogout = async () => {
    await logout();
    toast.success('로그아웃되었습니다.');
    navigate('/dashboard', { replace: true });
  };

  const handleGoToAdminPage = () => {
    navigate('/admin');
  };

  const handleGoToUserPage = () => {
    navigate('/dashboard');
  };

  return (
    <>
      <TopBackground />
      <Container>
        {isAuthenticated && (
          <UserSection>

            {user?.userType === 'admin' && (
              <IconButton onClick={handleGoToAdminPage}>
                <FaCrown /> 관리자 페이지
              </IconButton>
            )}
          </UserSection>
        )}

        <Title>웹사이트 리스크 분석 컴플라이언스</Title>
        <Subtitle>
          URL을 입력하면 AI가 자동으로 크롤링 후 분석 및 마스킹 결과를 제공합니다.
        </Subtitle>

        <InputArea>
          <InputWrapper>
            <Input
              type="text"
              placeholder="예: https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              maxLength={2048}
            />
          </InputWrapper>
          <Button onClick={handleAnalyze} disabled={loading}>
            {loading ? '분석 중...' : '분석 시작'}
          </Button>
        </InputArea>

        {loading && (
          <div style={{ marginTop: '2.5rem', textAlign: 'center' }}>
            <img
              src={loader}
              alt="분석 중 로딩 애니메이션"
              style={{ width: '100px', height: '100px', margin: 'auto', objectFit: 'contain' }}
            />
            <p style={{ marginTop: '1rem', fontSize: '1rem', color: '#4f46e5' }}>
              AI가 리스크를 분석하고 있습니다...
            </p>
          </div>
        )}

{/*         {loading && ( */}
{/*           <div style={{ marginTop: '2.5rem', textAlign: 'center' }}> */}
{/*             <img */}
{/*               src={loader} */}
{/*               alt="분석 중 로딩 애니메이션" */}
{/*               style={{ */}
{/*                 width: '100px', */}
{/*                 height: '100px', */}
{/*                 margin: 'auto', */}
{/*                 objectFit: 'contain', */}
{/*               }} */}
{/*             /> */}

{/*             <p style={{ marginTop: '1rem', fontSize: '1rem', color: '#4f46e5' }}> */}
{/*               {step */}
{/*                 ? STEP_LABEL[step] ?? '분석 진행 중' */}
{/*                 : '분석 준비 중'} */}
{/*             </p> */}

{/*             {percent != null && ( */}
{/*               <div style={{ marginTop: '0.75rem', fontSize: '0.9rem', color: '#6b7280' }}> */}
{/*                 {percent}% */}
{/*               </div> */}
{/*             )} */}

{/*             {percent != null && ( */}
{/*               <ProgressBar percent={percent} /> */}
{/*             )} */}
{/*           </div> */}
{/*         )} */}

        <IntroWrapper>
          <IntroTitle>Crawlwise: AI 기반 웹사이트 리스크 분석 플랫폼</IntroTitle>
          <IntroText>
            Crawlwise는 <strong style={{ color: '#4f46e5' }}>AI와 법률 데이터</strong>를 결합하여  
            웹사이트 내 <strong>개인정보, 저작권, 부정경쟁</strong> 요소를 자동 감지하고  
            법령 근거를 바탕으로 <strong>PASS / REVIEW / MASK / BLOCKED</strong>를 판단하는  
            <strong>지능형 리스크 분석 플랫폼</strong>입니다.
          </IntroText>

          
          <div
            style={{
              position: 'relative',
              margin: '5rem auto 3rem',
              width: '100%',
              maxWidth: '680px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
          
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 'calc(50% - 1px)',
                width: '2px',
                height: '100%',
                background: 'linear-gradient(180deg, rgba(99,102,241,0.4) 0%, rgba(212,214,255,0.25) 100%)',
                borderRadius: '2px',
                zIndex: 0,
              }}
            />

            
            {[
              {
                step: '1단계 탐지 (Detect)',
                color: '#4f46e5',
                bg: '#f5f7ff',
                text: (
                  <>
                    AI가 웹페이지 텍스트를 분석하여  
                    <strong>정규식(Regex)</strong>과 <strong>NER</strong> 기반으로  
                    이메일, 전화번호, 학번 등의 민감 정보를 식별합니다.  
                    Confidence ≥ 0.7 이상이면 “위험 요소”로 분류됩니다.
                  </>
                ),
              },
              {
                step: '2단계 근거 검색 (RAG 기반)',
                color: '#059669',
                bg: '#f2fbf6',
                text: (
                  <>
                    탐지된 위험 요소를 <strong>법령·약관 벡터 데이터베이스</strong>와 비교하여  
                    법적 근거를 탐색합니다.  
                    <strong>MongoDB Vector Search</strong>를 통해 가장 유사한 조항을 찾아냅니다.
                  </>
                ),
              },
              {
                step: '3단계 판단 (Decision)',
                color: '#b45309',
                bg: '#fff8ef',
                text: (
                  <>
                    AI가 법적 근거와 위험도를 종합해  
                    <strong>PASS / REVIEW / MASK / BLOCKED</strong> 중 하나로 분류합니다.  
                    robots.txt에 의해 접근이 차단된 경우  
                    자동으로 <strong style={{ color: '#ef4444' }}>BLOCKED</strong> 처리됩니다.
                  </>
                ),
              },
              {
                step: '4단계 마스킹 (Masking)',
                color: '#dc2626',
                bg: '#fff5f5',
                text: (
                  <>
                    “MASK”로 분류된 항목은 자동으로  
                    <strong>비식별화(*** 처리)</strong>되어 HTML 내에서 가려집니다.  
                    사용자는 마스킹 결과를 미리보기로 확인할 수 있습니다.
                  </>
                ),
              },
            ].map((item, i) => (
              <div
                key={i}
                style={{
                  position: 'relative',
                  zIndex: 1,
                  textAlign: 'center',
                  marginBottom: i === 3 ? '0' : '6rem',
                  width: '100%',
                }}
              >
                
                <div
                  style={{
                    background: item.bg,
                    border: `1px solid ${item.color}30`,
                    borderRadius: '16px',
                    padding: '2rem 2.5rem',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.05)',
                    display: 'inline-block',
                    maxWidth: '520px',
                  }}
                >
                  <h4
                    style={{
                      color: item.color,
                      fontSize: '1.3rem',
                      fontWeight: 700,
                      marginBottom: '0.75rem',
                    }}
                  >
                    {item.step}
                  </h4>
                  <p style={{ color: '#374151', lineHeight: 1.7, fontSize: '1.05rem' }}>{item.text}</p>
                </div>
              </div>
            ))}
          </div>

          <IntroText style={{ marginTop: '4rem', fontSize: '1.05rem', color: '#444' }}>
            Crawlwise는 <strong>OpenAI LLM</strong>과 <strong>법령 벡터 검색</strong> 기술을 통해  
            단순 탐지를 넘어 <strong>AI 판단의 근거와 이유</strong>를 투명하게 제공합니다.  
            사용자는 각 결과의 법적 근거를 확인하며,  
            서비스의 신뢰성과 투명성을 함께 경험할 수 있습니다.
          </IntroText>
        </IntroWrapper>
        <section
          style={{
            width: '100%',
            maxWidth: '1080px',
            margin: '6rem auto',
            padding: '4rem 3rem',
            background: 'linear-gradient(180deg, #ffffff 0%, #f9fafb 100%)',
            borderRadius: '24px',
            boxShadow: '0 10px 35px rgba(0,0,0,0.05)',
          }}
        >
          <h2
            style={{
              fontSize: '2rem',
              fontWeight: 800,
              color: '#111827',
              textAlign: 'center',
              marginBottom: '1rem',
              letterSpacing: '-0.02em',
            }}
          >
            Crawlwise Analysis Pipeline
          </h2>
          <p
            style={{
              textAlign: 'center',
              color: '#6b7280',
              fontSize: '1.05rem',
              marginBottom: '3.5rem',
              lineHeight: 1.7,
            }}
          >
            Crawlwise는 크롤링부터 마스킹까지 8단계의 안전하고 투명한 AI 분석 절차를 따릅니다.
            <br />
            모든 단계는 법적 준수와 데이터 최소 수집 원칙에 맞춰 설계되었습니다.
          </p>

          
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '1.75rem',
              marginBottom: '4rem',
            }}
          >
            {[
              {
                title: '1. 입력 처리',
                color: '#4f46e5',
                text:
                  'URL 유효성 검증 후 표준화된 도메인 형식으로 변환합니다. ' +
                  '잘못된 형식은 사전에 차단되어 안전성을 보장합니다.',
              },
              {
                title: '2. 접근 정책 확인',
                color: '#059669',
                text:
                  'robots.txt를 파싱해 허용된 경로만 요청합니다. ' +
                  'Disallow된 URL은 자동으로 BLOCKED 처리됩니다.',
              },
              {
                title: '3. 크롤링',
                color: '#f59e0b',
                text:
                  'Playwright 기반의 헤드리스 브라우저로 렌더링 결과를 수집하며, ' +
                  '서버 부하를 줄이기 위해 요청 지연(Throttle)과 지수 백오프를 적용합니다.',
              },
              {
                title: '4. 탐지',
                color: '#dc2626',
                text:
                  '정규식과 NER 모델을 결합해 개인정보·저작권·식별 정보 등을 감지합니다. ' +
                  '신뢰도(confidence) ≥ 0.7인 항목만 위험으로 분류합니다.',
              },
              {
                title: '5. 근거 검색',
                color: '#4f46e5',
                text:
                  '탐지된 텍스트를 벡터로 변환해 MongoDB Atlas Vector Search에서 ' +
                  '법령·약관 조항과 의미 유사도를 계산합니다.',
              },
              {
                title: '6. 판단',
                color: '#059669',
                text:
                  'AI가 RAG 결과를 기반으로 PASS, REVIEW, MASK, BLOCKED 중 하나로 판단하고, ' +
                  '판단 사유와 근거를 함께 저장합니다.',
              },
              {
                title: '7. 마스킹',
                color: '#f59e0b',
                text:
                  'MASK로 결정된 스팬만 정밀 마스킹합니다. ' +
                  '이메일, 전화번호, 학번 등은 *** 처리하여 비식별화합니다.',
              },
              {
                title: '8. 감사 로그',
                color: '#dc2626',
                text:
                  '크롤링 메타데이터와 AI 판단 근거를 비식별 상태로 기록합니다. ' +
                  '재현성과 투명성을 위해 단계별 결과를 안전하게 보관합니다.',
              },
            ].map((step, i) => (
              <div
                key={i}
                style={{
                  background: '#fff',
                  borderRadius: '16px',
                  padding: '2rem',
                  border: `1px solid ${step.color}25`,
                  boxShadow: '0 4px 14px rgba(0,0,0,0.04)',
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 6px 18px rgba(0,0,0,0.08)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 4px 14px rgba(0,0,0,0.04)';
                }}
              >
                <h4
                  style={{
                    color: step.color,
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    marginBottom: '0.75rem',
                    letterSpacing: '-0.01em',
                  }}
                >
                  {step.title}
                </h4>
                <p style={{ color: '#374151', fontSize: '1.02rem', lineHeight: 1.7 }}>
                  {step.text}
                </p>
              </div>
            ))}
          </div>

          
          <div
            style={{
              borderTop: '1px solid #e5e7eb',
              paddingTop: '2.5rem',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              gap: '1.5rem',
            }}
          >
            {[
              {
                title: 'robots.txt 준수',
                desc: 'Disallow 규칙을 엄격히 따르며 차단된 URL은 절대 요청하지 않습니다.',
              },
              {
                title: '속도 제한 및 백오프',
                desc: '동일 도메인에 대한 연속 요청 간에 지연을 두고, 서버 부하를 감지하면 자동 대기합니다.',
              },
              {
                title: '데이터 최소 수집',
                desc: '필요한 HTML 본문만 수집하며 이미지, 스크립트 등은 저장하지 않습니다.',
              },
            ].map((p, i) => (
              <div
                key={i}
                style={{
                  background: '#f9fafb',
                  borderRadius: '14px',
                  border: '1px solid #e5e7eb',
                  padding: '1.5rem',
                  textAlign: 'center',
                }}
              >
                <h5
                  style={{
                    color: '#111827',
                    fontWeight: 700,
                    fontSize: '1.1rem',
                    marginBottom: '0.5rem',
                  }}
                >
                  {p.title}
                </h5>
                <p style={{ color: '#4b5563', fontSize: '0.98rem', lineHeight: 1.7 }}>{p.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </Container>
    </>
  );
}

export default HomePage;