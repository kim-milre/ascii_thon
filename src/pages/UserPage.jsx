// src/pages/UserPage.jsx
import React, { useState } from 'react'
import styled from '@emotion/styled'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { FaUser, FaEnvelope, FaShieldAlt, FaCalendarAlt, FaLock } from 'react-icons/fa'
import api from '../api/api'

const DashboardContainer = styled.div`
  max-width: 800px;
  margin: 8rem auto;
  padding: 2.5rem;
  border-radius: 20px;
  background: white;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  text-align: center;
`

const Welcome = styled.div`
  margin-bottom: 2.5rem;
  h1 { font-size: 1.8rem; font-weight: 700; color: #111827; margin-bottom: 0.5rem; }
  p { color: #6b7280; font-size: 1rem; }
`

const UserCard = styled.div`
  background: #f9fafb;
  border-radius: 16px;
  padding: 2rem;
  text-align: left;
  margin-top: 1rem;
`

const CardTitle = styled.h2`
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 1.2rem; color: #4f46e5; margin-bottom: 1.5rem;
`

const UserAvatar = styled.img`
  width: 90px; height: 90px; border-radius: 50%;
  margin: 0 auto 1.5rem; display: block; border: 3px solid #e0e7ff;
`

const AvatarPlaceholder = styled.div`
  width: 90px; height: 90px; border-radius: 50%;
  margin: 0 auto 1.5rem; display: flex; align-items: center; justify-content: center;
  background: #e0e7ff; color: #4338ca; font-size: 2rem; font-weight: 700;
`

const UserInfo = styled.div` display: flex; flex-direction: column; gap: 1rem; `
const InfoRow = styled.div` display: flex; align-items: center; gap: 0.8rem; font-size: 1rem; color: #374151; `
const InfoLabel = styled.span` font-weight: 600; color: #111827; min-width: 90px; `
const InfoValue = styled.span` color: #4b5563; word-break: break-all; `
const ProviderBadge = styled.span`
  background: ${({ provider }) =>
    provider === 'admin' ? '#dc2626' :
    provider === 'local' ? '#4f46e5' :
    '#10b981'};
  color: white; font-weight: 600; border-radius: 12px;
  padding: 0.2rem 0.6rem; font-size: 0.85rem;
`

const ActionButtons = styled.div`
  margin-top: 2.5rem; display: flex; justify-content: center; gap: 1rem;
`

const ActionButton = styled.button`
  border: none; border-radius: 8px; font-size: 1rem; padding: 0.6rem 1.4rem;
  cursor: pointer; transition: 0.25s ease;
  &.primary { background: #4f46e5; color: white; }
  &.primary:hover { background: #4338ca; }
  &.secondary { background: #f3f4f6; color: #111827; }
  &.secondary:hover { background: #e5e7eb; }
`

const Input = styled.input`
  width: 100%; border: 1px solid #d1d5db; border-radius: 8px;
  padding: 0.6rem 1rem; font-size: 1rem; color: #111827; margin-top: 0.4rem;
  &:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15); }
  max-length: 100;
`

const SectionDivider = styled.hr`
  border: none; height: 1px; background: #e5e7eb; margin: 2rem 0;
`

const escapeHTML = (str) =>
  String(str).replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]))

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
}

const getProviderDisplayName = (provider) => {
  if (provider === 'local') return '로컬'
  if (provider === 'admin') return '관리자'
  return '기타'
}

function UserPage() {
  const { user, checkAuthStatus } = useAuth()
  const navigate = useNavigate()
  const [isEditing, setIsEditing] = useState(false)
  const [newName, setNewName] = useState(user?.name || '')
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  
  const validateInputs = () => {
    if (!newName.trim()) return toast.warn('이름을 입력하세요.')
    if (newPassword && newPassword.length < 8) return toast.warn('비밀번호는 8자 이상이어야 합니다.')
    if (newPassword && !/[A-Z]/.test(newPassword)) return toast.warn('비밀번호에는 대문자가 포함되어야 합니다.')
    if (newPassword && !/[0-9]/.test(newPassword)) return toast.warn('비밀번호에는 숫자가 포함되어야 합니다.')
    if (newPassword && newPassword !== confirmPassword) return toast.warn('새 비밀번호가 일치하지 않습니다.')
    return true
  }

  if (!user) {
    return (
      <DashboardContainer>
        <h2>로그인이 필요합니다.</h2>
        <ActionButton className="primary" onClick={() => navigate('/dashboard')}>
          로그인하러 가기
        </ActionButton>
      </DashboardContainer>
    )
  }

  const handleUpdateProfile = async () => {
    if (!validateInputs()) return
    try {
      const sanitizedName = escapeHTML(newName.trim())
      const res = await api.put('/api/users/profile', { name: sanitizedName }, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      if (res.data.success) {
        toast.success('프로필이 수정되었습니다.')
        checkAuthStatus()
        setIsEditing(false)
      } else toast.error('프로필 수정 실패')
    } catch (error) {
      toast.error(`프로필 수정 중 오류 발생: ${error.response?.status || '네트워크 오류'}`)
    }
  }

  const handleChangePassword = async () => {
    if (!validateInputs()) return
    try {
      const res = await api.put('/api/users/password',
        { currentPassword: oldPassword, newPassword },
        { headers: { 'X-Requested-With': 'XMLHttpRequest' } }
      )
      if (res.data.success) {
        toast.success('비밀번호가 변경되었습니다.')
        setOldPassword('')
        setNewPassword('')
        setConfirmPassword('')
        setIsEditing(false)
      } else toast.error('비밀번호 변경 실패')
    } catch (error) {
      toast.error(`비밀번호 변경 중 오류: ${error.response?.status || '네트워크 오류'}`)
    }
  }


   return (
    <DashboardContainer>
      <Welcome>
        <h1>환영합니다, {escapeHTML(user.name)}님!</h1>
        <p>Crawlwise 계정 정보를 확인하세요.</p>
      </Welcome>

      <UserCard>
        <CardTitle><FaUser /> 프로필 정보</CardTitle>

        {user.avatar
          ? <UserAvatar src={user.avatar} alt="user avatar" />
          : <AvatarPlaceholder>{escapeHTML(user.name.charAt(0).toUpperCase())}</AvatarPlaceholder>}

        {!isEditing ? (
          <>
            <UserInfo>
              <InfoRow><FaUser /><InfoLabel>이름:</InfoLabel><InfoValue>{escapeHTML(user.name)}</InfoValue></InfoRow>
              <InfoRow><FaEnvelope /><InfoLabel>이메일:</InfoLabel><InfoValue>{escapeHTML(user.email)}</InfoValue></InfoRow>
              <InfoRow><FaShieldAlt /><InfoLabel>계정 종류:</InfoLabel>
                <InfoValue><ProviderBadge provider={user.provider}>{getProviderDisplayName(user.provider)} 계정</ProviderBadge></InfoValue>
              </InfoRow>
              <InfoRow><FaShieldAlt /><InfoLabel>사용자 유형:</InfoLabel>
                <InfoValue><ProviderBadge provider={user.userType === 'admin' ? 'admin' : 'user'}>
                  {user.userType === 'admin' ? '관리자' : '일반 사용자'}
                </ProviderBadge></InfoValue>
              </InfoRow>
              <InfoRow><FaCalendarAlt /><InfoLabel>가입일:</InfoLabel><InfoValue>{formatDate(user.createdAt)}</InfoValue></InfoRow>
            </UserInfo>

            <ActionButtons>
              <ActionButton className="primary" onClick={() => setIsEditing(true)}>정보 수정</ActionButton>
              <ActionButton className="secondary" onClick={() => navigate('/list')}>분석 내역 보기</ActionButton>
            </ActionButtons>
          </>
        ) : (
          <>
            <InfoRow><InfoLabel>이름 수정:</InfoLabel><Input value={newName} onChange={(e) => setNewName(e.target.value)} /></InfoRow>
            <SectionDivider />
            <CardTitle><FaLock /> 비밀번호 변경</CardTitle>
            <InfoRow><InfoLabel>현재 비밀번호</InfoLabel><Input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} /></InfoRow>
            <InfoRow><InfoLabel>새 비밀번호</InfoLabel><Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} /></InfoRow>
            <InfoRow><InfoLabel>비밀번호 확인</InfoLabel><Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} /></InfoRow>
            <ActionButtons>
              <ActionButton className="primary" onClick={handleUpdateProfile}>이름 수정 저장</ActionButton>
              <ActionButton className="secondary" onClick={handleChangePassword}>비밀번호 변경</ActionButton>
              <ActionButton className="secondary" onClick={() => setIsEditing(false)}>취소</ActionButton>
            </ActionButtons>
          </>
        )}
      </UserCard>
    </DashboardContainer>
  )
}

export default UserPage