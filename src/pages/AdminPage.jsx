//AdminPage.jsx
import styled from '@emotion/styled'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import { authAPIService } from '../api/authApi'
import { useEffect, useState } from 'react'

const Container = styled.div`
  position: relative;
  transform: translateY(8rem); /* ✅ 헤더 높이만큼 강제 아래로 밀기 */
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
  min-height: 100vh; 
  box-sizing: border-box;
  background: #fff;
`

const Title = styled.h2`
  margin-bottom: 1.5rem;
`

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;

  th, td {
    border-bottom: 1px solid #eee;
    padding: 0.75rem;
    text-align: left;
  }

  th {
    background: #fafafa;
  }

  tr:hover {
    background: #fafafa;
  }
`

const Actions = styled.div`
  display: flex;
  gap: 0.5rem;
`

const Button = styled.button`
  padding: 0.4rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;

  &:hover {
    background: #f5f5f5;
  }
`

const UserTypeBadge = styled.span`
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.875rem;
  color: white;
  background: ${props => props.isAdmin ? '#ff6b35' : '#667eea'};
`

const ProviderBadge = styled.span`
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.875rem;
  color: white;
  background: ${props => {
    switch (props.provider) {
      case 'google': return '#db4437';
      case 'naver': return '#03c75a';
      default: return '#667eea';
    }
  }};
`

const escapeHTML = (str = '') =>
  String(str).replace(/[&<>"']/g, (m) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]
  ));

function AdminPage() {
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
      queryKey: ['users'],
      queryFn: async () => {
        const res = await authAPIService.getAllUsers();
        if (!res?.data?.users) {
          throw new Error('서버 응답이 올바르지 않습니다.');
        }
        return res;
      },
      retry: 1,
      onError: () => toast.error('사용자 목록을 불러오는 중 오류가 발생했습니다.'),
    });


  const changeUserTypeMutation = useMutation({
    mutationFn: async ({ userId, userType }) => {
      if (!userId || !['user', 'admin'].includes(userType)) {
        throw new Error('잘못된 요청입니다.');
      }
      return await authAPIService.changeUserType(userId, userType, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }, // CSRF 방지
      });
    },
    onSuccess: () => {
      toast.success('사용자 유형이 변경되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: () => {
      toast.error('사용자 유형 변경 중 오류가 발생했습니다.');
    },
  });


  const users = Array.isArray(data?.data?.users) ? data.data.users : [];

    const onChangeUserType = async (user, newUserType) => {
      const safeName = escapeHTML(user?.name || '사용자');
      const userTypeText = newUserType === 'admin' ? '관리자' : '일반 사용자';
      const confirmMsg = `${safeName}님의 유형을 ${userTypeText}로 변경할까요?`;

      if (!window.confirm(confirmMsg)) return;

    try {
      await changeUserTypeMutation.mutateAsync({
        userId: user._id,
        userType: newUserType,
      })
    } catch (error) {
      toast.error(error.userMessage || '사용자 유형 변경에 실패했습니다.')
    }
  }

  if (isLoading) {
    return (
      <Container>
        <p>로딩 중...</p>
      </Container>
    )
  }

  if (error) {
    return (
      <Container>
        <h3>오류가 발생했습니다</h3>
        <p>잠시 후 다시 시도해주세요.</p>
      </Container>
    );
  }

  return (
    <Container>
      <Title>관리자 페이지 (사용자 관리)</Title>
      <Table>
        <thead>
          <tr>
            <th>이름</th>
            <th>이메일</th>
            <th>계정 종류</th>
            <th>사용자 유형</th>
            <th>가입일</th>
            <th>액션</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user._id}>
              <td>{escapeHTML(user.name)}</td>
              <td>{escapeHTML(user.email)}</td>
  
              <td>
                <UserTypeBadge isAdmin={user.userType === 'admin'}>
                  {user.userType === 'admin' ? '관리자' : '일반 사용자'}
                </UserTypeBadge>
              </td>
              <td>{new Date(user.createdAt).toLocaleDateString('ko-KR')}</td>
              <td>
                <Actions>
                  {user.userType === 'admin' ? (
                    <Button onClick={() => onChangeUserType(user, 'user')}>
                      일반 사용자로 변경
                    </Button>
                  ) : (
                    <Button onClick={() => onChangeUserType(user, 'admin')}>
                      관리자로 변경
                    </Button>
                  )}
                </Actions>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Container>
  )
}

export default AdminPage