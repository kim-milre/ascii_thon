import React, { useState, useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import styled from '@emotion/styled'
import { useAuth } from '../contexts/AuthContext'
import { FaUser, FaSignOutAlt } from 'react-icons/fa'

const HeaderContainer = styled.header`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 3rem;
  transition: background 0.4s ease, box-shadow 0.4s ease;
  background: ${({ scrolled }) =>
    scrolled ? 'rgba(255, 255, 255, 0.95)' : 'rgba(255, 255, 255, 0.7)'};
  backdrop-filter: blur(14px);
  box-shadow: ${({ scrolled }) =>
    scrolled
      ? '0 4px 12px rgba(0, 0, 0, 0.12)'  
      : '0 2px 6px rgba(0, 0, 0, 0.05)'}; 
`

const Brand = styled(Link)`
  text-decoration: none;
  font-weight: 700;
  font-size: 1.5rem;
  color: #111827;
`

const NavContainer = styled.div`
  display: flex;
  justify-content: space-between;
  flex: 1;
  margin: 0 3rem;
`

const NavGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;
`

const NavLink = styled(Link)`
  position: relative;
  text-decoration: none;
  color: #111827;
  font-weight: 500;
  font-size: 1rem;
  padding-bottom: 4px;
  transition: color 0.2s ease;

  &:hover {
    color: #4f46e5;
  }

  &.active::after {
    content: '';
    position: absolute;
    left: 0;
    bottom: -3px;
    width: 100%;
    height: 2px;
    background: #4f46e5;
    border-radius: 2px;
  }
`

const UserMenuContainer = styled.div`
  position: relative;
  display: inline-block;
`

const UserButton = styled.button`
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 500;
  cursor: pointer;
  color: #111827;
  transition: color 0.2s;

  &:hover {
    color: #4f46e5;
  }
`

const Dropdown = styled.div`
  position: absolute;
  top: 2.8rem;
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
  padding: 0.8rem 1rem;
  width: 180px;
  opacity: ${(props) => (props.show ? 1 : 0)};
  transform: translateY(${(props) => (props.show ? '0' : '-5px')});
  pointer-events: ${(props) => (props.show ? 'auto' : 'none')};
  transition: opacity 0.25s ease, transform 0.25s ease;
  z-index: 100;
`

const DropdownHeader = styled.div`
  font-weight: 600;
  font-size: 0.95rem;
  color: #111827;
  text-align: center;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 0.6rem;
`

const DropdownItem = styled.button`
  display: block;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  padding: 0.6rem 0;
  color: #374151;
  font-size: 0.95rem;
  cursor: pointer;
  transition: 0.2s;

  &:hover {
    color: #4f46e5;
  }

  &.danger {
    color: #dc2626;
    &:hover {
      color: #b91c1c;
    }
  }
`

const escapeHTML = (str = '') =>
  String(str).replace(/[&<>"']/g, (m) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
  }[m]));

function Header() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuth()
  const [scrolled, setScrolled] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const hideTimer = useRef(null)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const isActive = (path) => (location.pathname === path ? 'active' : '')
  
  const handleLogout = async () => {
    try {
      await logout();
      navigate('/dashboard', { replace: true });
    } catch (e) {
      console.warn('⚠️ 로그아웃 오류:', e?.message || 'unknown');
      alert('로그아웃 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    }
  };

  const handleMouseEnter = () => {
    clearTimeout(hideTimer.current)
    setShowDropdown(true)
  }

  const handleMouseLeave = () => {
    hideTimer.current = setTimeout(() => {
      setShowDropdown(false)
    }, 250)
  }

    const safeUserName = escapeHTML(user?.name || '사용자');

  return (
    <HeaderContainer scrolled={scrolled}>
      <Brand to="/">Crawlwise</Brand>

      <NavContainer>
        <NavGroup>
          <NavLink to="/" className={isActive('/')}>
            Home
          </NavLink>
          <NavLink to="/list" className={isActive('/list')}>
            List
          </NavLink>
        </NavGroup>

        <NavGroup>
          {isAuthenticated ? (
            <UserMenuContainer
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
            >
              <UserButton>
                <FaUser /> User
              </UserButton>
              <Dropdown show={showDropdown}>
                <div
                  style={{
                    padding: '0.4rem 0.2rem',
                    fontWeight: '600',
                    color: '#111827',
                  }}
                >
                </div>
                <DropdownHeader>{safeUserName}</DropdownHeader>

                <DropdownItem onClick={() => navigate('/user')}>
                  내 정보 보기
                </DropdownItem>
                <DropdownItem className="danger" onClick={handleLogout}>
                  <FaSignOutAlt /> 로그아웃
                </DropdownItem>
              </Dropdown>
            </UserMenuContainer>
          ) : (
            <NavLink to="/dashboard" className={isActive('/dashboard')}>
              Login
            </NavLink>
          )}
        </NavGroup>
      </NavContainer>
    </HeaderContainer>
  )
}

export default Header