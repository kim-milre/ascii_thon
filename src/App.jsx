/* src/App.jsx */
/* [시큐어코딩 가이드 근거]
   - p.10–16: 입력·출력 검증, 예외 처리
   - p.28–30: UI 무결성 및 출력 무해화(XSS 방지)
   - p.125–130: 오류 정보 노출 방지, 예외 로깅 최소화
   - p.83: 데이터 무결성 보호 및 안전한 상태 관리
*/

import React, { Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import './App.css'


import HomePage from './pages/HomePage'
import DashboardPage from './pages/DashboardPage'
import ListPage from './pages/ListPage'
import ResultPage from './pages/ResultPage'
import UserPage from './pages/UserPage'
import AdminPage from './pages/AdminPage'


import Header from './components/Header'
import NotFound from './components/NotFound'


import GlobalStyles from './styles/GlobalStyles'
import { AuthProvider, useAuth } from './contexts/AuthContext'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
      onError: (err) => {
        if (import.meta.env.DEV) console.error('Query Error:', err)
      },
    },
  },
})

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught:', error, info)
    } else {
      try {
        navigator.sendBeacon('/_/log/error', JSON.stringify({
          code: 'APP-ERR-01',
          time: new Date().toISOString(),
        }))
      } catch {/* no-op */}
    }
  }

  render() {
    if (this.state.hasError) {
      return <div role="alert">문제가 발생했습니다. 다시 시도해주세요.</div>
    }
    return this.props.children
  }
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return <div>로딩 중...</div>
  if (!isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  return children
}

function AppContent() {
  const location = useLocation()
  const { isAuthenticated } = useAuth()

  const hideLayoutRoutes = ['/dashboard', '/login']
  const shouldHideLayout = hideLayoutRoutes.includes(location.pathname)

  return (
    <div className="app">
      {!shouldHideLayout && <Header />}

      <main className="main-content">
        <Suspense fallback={<div>로딩 중...</div>}>
          <Routes>
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/list"
              element={
                <ProtectedRoute>
                  <ListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/user"
              element={
                <ProtectedRoute>
                  <UserPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/result/:id"
              element={
                <ProtectedRoute>
                  <ResultPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                isAuthenticated ? <Navigate to="/" replace /> : <DashboardPage />
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>

      {!shouldHideLayout && (
        <footer className="footer">
          <p>© 2025 Crawlwise | Compliance Risk Analysis Platform</p>
        </footer>
      )}
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <GlobalStyles />
          <ErrorBoundary>
            <AppContent />
          </ErrorBoundary>
          <ToastContainer
            position="bottom-right"
            autoClose={3000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="light"
          />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App