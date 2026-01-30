//DashboardPage.jsx
import React, { useState } from 'react';
import styled from '@emotion/styled';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-toastify';
import { ClipLoader } from 'react-spinners';
import { FaEye, FaEyeSlash, FaUser, FaLock, FaEnvelope, FaGoogle } from 'react-icons/fa';
import logo from '../assets/logo.png';

const PageContainer = styled.div`
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #f9fafb;
  margin: 0;
  padding: 0;
  position: fixed;
  top: 0;
  left: 0;
`;

const LeftSection = styled.div`
  flex: 1;
  background: white;
  color: #111827;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 3rem;
  border-right: 1px solid #e5e7eb;

  img {
    width: 160px;
    margin-bottom: 2rem;
  }

  h1 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #111827;
  }

  p {
    font-size: 1.1rem;
    color: #6b7280;
  }
`;

const RightSection = styled.div`
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const AuthBox = styled.div`
  background: white;
  padding: 3rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  width: 400px;
  text-align: center;
`;

const Title = styled.h2`
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  color: #333;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const InputGroup = styled.div`
  position: relative;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
  }
`;

const InputIcon = styled.div`
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
`;

const PasswordToggle = styled.button`
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
`;

const ErrorMessage = styled.span`
  color: #ef4444;
  font-size: 0.85rem;
  margin-top: 0.25rem;
  display: block;
`;

const Button = styled.button`
  width: 100%;
  background: #6366f1;
  color: white;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  padding: 0.9rem;
  cursor: pointer;
  transition: 0.3s;

  &:hover {
    background: #4f46e5;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const Divider = styled.div`
  text-align: center;
  margin: 1.5rem 0;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
    background: #e0e0e0;
  }

  span {
    background: white;
    padding: 0 1rem;
    color: #666;
    font-size: 0.9rem;
  }
`;

const SocialButton = styled.button`
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 1rem;
  transition: all 0.3s;

  &:hover {
    border-color: #6366f1;
    background: #f8f9ff;
  }
`;

const SwitchText = styled.p`
  margin-top: 1rem;
  color: #6b7280;
  font-size: 0.95rem;

  a {
    color: #6366f1;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
`;

const validatePassword = (pw) => {
  if (pw.length < 8) return '비밀번호는 8자 이상이어야 합니다.';
  if (!/[A-Z]/.test(pw)) return '비밀번호에는 대문자가 포함되어야 합니다.';
  if (!/[0-9]/.test(pw)) return '비밀번호에는 숫자가 포함되어야 합니다.';
  return true;
};

function DashboardPage() {
  const navigate = useNavigate();
  const { login, register: registerUser } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const password = watch('password');


  const onSubmit = async (data) => {
    setIsLoading(true);
    try {
      if (isRegister) {
        const sanitizedName = data.name.replace(/[<>]/g, '');
        const sanitizedEmail = data.email.trim().toLowerCase();

        const pwValidation = validatePassword(data.password);
        if (pwValidation !== true) {
          toast.warn(pwValidation);
          setIsLoading(false);
          return;
        }

        const result = await registerUser({
          name: sanitizedName,
          email: sanitizedEmail,
          password: data.password,
        });

        if (result.success) {
          toast.success('회원가입 성공! 로그인해주세요.');
          setIsRegister(false);
        } else {
          toast.error('회원가입 실패. 잠시 후 다시 시도해주세요.');
        }
      } else {
        const sanitizedEmail = data.email.trim().toLowerCase();
        const result = await login({
          email: sanitizedEmail,
          password: data.password,
        });

        if (result.success) {
          toast.success('로그인 성공!');
          navigate('/', { replace: true });
        } else {
          toast.error('로그인 실패. 입력값을 다시 확인하세요.');
        }
      }
    } catch (err) {
      console.warn('로그인/회원가입 오류:', err?.message || 'unknown');
      toast.error('요청 처리 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <PageContainer>
      <LeftSection>
        <img src={logo} alt="crawlwise" />
        <h1>Crawlwise</h1>
        <p>Compliance Risk Analysis Platform</p>
      </LeftSection>

      <RightSection>
        <AuthBox>
          <Title>{isRegister ? '회원가입' : '로그인'}</Title>
          <Form onSubmit={handleSubmit(onSubmit)}>
            {isRegister && (
              <InputGroup>
                <InputIcon><FaUser /></InputIcon>
                <Input
                  type="text"
                  placeholder="이름"
                  {...register('name', { required: '이름은 필수입니다' })}
                />
                {errors.name && <ErrorMessage>{errors.name.message}</ErrorMessage>}
              </InputGroup>
            )}

            <InputGroup>
              <InputIcon><FaEnvelope /></InputIcon>
              <Input
                type="email"
                placeholder="이메일"
                {...register('email', { required: '이메일은 필수입니다' })}
              />
              {errors.email && <ErrorMessage>{errors.email.message}</ErrorMessage>}
            </InputGroup>

            <InputGroup>
              <InputIcon><FaLock /></InputIcon>
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="비밀번호"
                {...register('password', { required: '비밀번호는 필수입니다', validate: validatePassword, minLength: 6 })}
              />
              <PasswordToggle type="button" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </PasswordToggle>
              {errors.password && <ErrorMessage>{errors.password.message}</ErrorMessage>}
            </InputGroup>

            {isRegister && (
              <InputGroup>
                <InputIcon><FaLock /></InputIcon>
                <Input
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="비밀번호 확인"
                  {...register('confirmPassword', {
                    required: '비밀번호 확인은 필수입니다',
                    validate: (value) => value === password || '비밀번호가 일치하지 않습니다',
                  })}
                />
                <PasswordToggle type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                  {showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
                </PasswordToggle>
                {errors.confirmPassword && <ErrorMessage>{errors.confirmPassword.message}</ErrorMessage>}
              </InputGroup>
            )}

            <Button type="submit" disabled={isLoading}>
              {isLoading ? <ClipLoader size={20} color="white" /> : isRegister ? '회원가입' : '로그인'}
            </Button>
          </Form>

          <SwitchText>
            {isRegister ? (
              <>
                이미 계정이 있으신가요?{' '}
                <a onClick={() => setIsRegister(false)}>로그인</a>
              </>
            ) : (
              <>
                회원이 아니신가요?{' '}
                <a onClick={() => setIsRegister(true)}>회원가입</a>
              </>
            )}
          </SwitchText>
        </AuthBox>
      </RightSection>
    </PageContainer>
  );
}

export default DashboardPage;