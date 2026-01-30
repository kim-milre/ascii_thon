// src/pages/ListPage.jsx.
import React, { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import styled from '@emotion/styled'
import { complianceAPI } from '../api/api'
import { ClipLoader } from 'react-spinners'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { useAuth } from '../contexts/AuthContext'


const Background = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  background: linear-gradient(180deg, #eef2ff 0%, #ffffff 60%);
  z-index: -1;
`

const PageContainer = styled.div`
  position: relative;
  width: 100%;
  min-height: 100vh;
  padding: 8rem 4rem;
  box-sizing: border-box;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
`

const Header = styled.div`
  text-align: center;
  margin-bottom: 3rem;

  h2 {
    font-size: 2.2rem;
    font-weight: 800;
    color: #111827;
    margin-bottom: 0.6rem;
  }

  p {
    color: #6b7280;
    font-size: 1.05rem;
  }
`

const FilterBar = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 3rem;
  flex-wrap: wrap;
`

const FilterButton = styled.button`
  border: none;
  background: none;
  font-size: 1rem;
  font-weight: ${(props) => (props.active ? '700' : '500')};
  color: ${(props) => (props.active ? '#4f46e5' : '#6b7280')};
  padding-bottom: 0.4rem;
  border-bottom: ${(props) =>
    props.active ? '2px solid #4f46e5' : '2px solid transparent'};
  cursor: pointer;
  transition: color 0.25s, border-bottom 0.25s;

  &:hover {
    color: #4f46e5;
  }
`

const CardGrid = styled.div`
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.8rem;
  justify-items: center;
  box-sizing: border-box;
  padding-bottom: 4rem;
`

const Card = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.5rem 1.8rem;
  width: 100%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  transition: all 0.25s ease;
  cursor: pointer;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.15);
  }

  h3 {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.6rem;
    word-break: break-all;
  }

  p {
    color: #4b5563;
    font-size: 0.95rem;
    line-height: 1.4;
  }


  .meta {
    display: flex;
    justify-content: space-between;
    margin-top: 1rem;
    color: #9ca3af;
    font-size: 0.85rem;
  }
`

const DangerButton = styled.button`
  display: block;
  margin: 3rem auto 0;
  padding: 0.8rem 2rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);

  &:hover {
    background: #dc2626;
    box-shadow: 0 3px 10px rgba(239, 68, 68, 0.3);
  }
`

const LoadingWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 5rem;
  color: #4f46e5;
  font-weight: 500;

  p {
    margin-top: 1rem;
    font-size: 1.1rem;
  }
`

const escapeHTML = (str) =>
  String(str).replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]))

function ListPage() {
  const [filter, setFilter] = useState('전체')
  const filters = ['전체', 'PASS', 'REVIEW', 'MASK']
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { token } = useAuth()

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['analyzedSites', token],
    queryFn: () => complianceAPI.getAnalyzedSites(token),
    enabled: !!token, 
  })

  const handleDeleteAll = async () => {
    const firstCheck = window.confirm('⚠️ 정말 모든 분석 결과를 삭제하시겠습니까?');
    if (!firstCheck) return;
    const secondCheck = window.prompt('삭제를 진행하려면 "DELETE"를 입력하세요.');
    if (secondCheck !== 'DELETE') {
      toast.info('삭제가 취소되었습니다.');
      return;
    }

    try {
      await complianceAPI.deleteAllSites();
      toast.success('모든 분석 결과가 삭제되었습니다.');
      await queryClient.invalidateQueries(['analyzedSites']);
    } catch (err) {
      console.error('❌ 삭제 오류:', err);
      toast.error('삭제 중 오류가 발생했습니다. 네트워크를 확인하세요.');
    }
  }

  if (!token) {
    return (
      <div style={{ textAlign: 'center', marginTop: '5rem', color: '#4b5563' }}>
        로그인이 필요합니다.
      </div>
    )
  }

  if (isLoading) {
    return (
      <LoadingWrapper>
        <ClipLoader color="#4f46e5" size={50} />
        <p>사이트 목록을 불러오는 중...</p>
      </LoadingWrapper>
    )
  }

  if (error) {
    const message = error?.response?.data?.message || error.message || '데이터 로드 실패';
    return <div style={{ textAlign: 'center', color: '#ef4444' }}>에러: {escapeHTML(message)}</div>;
  }

  const sites = Array.isArray(data?.data) ? data.data : [];
  const filtered = filter === '전체' ? sites : sites.filter((site) => site.decision === filter);

  return (
    <>
      <Background />
      <PageContainer>
        <Header>
          <h2>분석된 사이트 목록</h2>
          <p>AI 기반 컴플라이언스 분석 결과를 한눈에 확인하세요</p>
        </Header>

        <FilterBar>
          {filters.map((f) => (
            <FilterButton key={f} active={filter === f} onClick={() => setFilter(f)}>
              {f}
            </FilterButton>
          ))}
        </FilterBar>


        <CardGrid>
          {filtered.length > 0 ? (
            filtered.map((site) => (
              <Card
                key={site._id || site.id}
                onClick={() => navigate(`/result/${escapeHTML(site._id || site.id)}`)}
              >
                <h3>{escapeHTML(site.url)}</h3>
                <div className="meta">
                  <span>{escapeHTML(site.decision)}</span>
                  <span>{escapeHTML(String(site.riskScore ?? 'N/A'))}점</span>
                </div>
              </Card>
            ))
          ) : (
            <p style={{ textAlign: 'center', color: '#6b7280', marginTop: '3rem' }}>
              아직 분석된 사이트가 없습니다.
            </p>
          )}
        </CardGrid>

        {sites.length > 0 && (
          <DangerButton onClick={handleDeleteAll}>모두 삭제</DangerButton>
        )}
      </PageContainer>
    </>
  )
}

export default ListPage