import React from 'react';
import styled from '@emotion/styled';

const Wrapper = styled.div`
  width: 360px;
  margin-top: 2rem;
`;

const BarBg = styled.div`
  width: 100%;
  height: 12px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
`;

const BarFill = styled.div`
  height: 100%;
  width: ${({ percent }) => percent}%;
  background: linear-gradient(90deg, #6366f1, #4f46e5);
  transition: width 0.4s ease;
`;

const Label = styled.div`
  margin-top: 0.75rem;
  font-size: 0.95rem;
  color: #4f46e5;
  font-weight: 600;
`;

const STEP_LABEL = {
  INITIALIZING: '분석 준비 중',
  CRAWLING: '웹페이지 크롤링 중',
  DETECTING_RISKS: '리스크 탐지 중',
  RAG_SEARCH: '법적 근거 검색 중',
  LLM_JUDGMENT: 'AI 판단 중',
  MASKING: '민감 정보 마스킹 중',
  SAVING: '결과 저장 중',
};

export default function ProgressBar({ progress }) {
  if (!progress) return null;

  return (
    <Wrapper>
      <BarBg>
        <BarFill percent={progress.percent || 0} />
      </BarBg>
      <Label>
        {STEP_LABEL[progress.step] || progress.step} · {progress.percent}%
      </Label>
    </Wrapper>
  );
}