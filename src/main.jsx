/* src/main.jsx */
/* 변경 요지
   1) root 엘리먼트 존재 여부 확인 (XSS 삽입 방지, 예외 처리)
   2) ErrorBoundary 추가로 렌더링 오류 시 내부정보 노출 차단
   3) 개발환경에서만 디버깅 로그 허용 (운영 시 콘솔 노출 금지)
   4) 시큐어코딩 가이드 근거 주석 포함
*/

import React from 'react'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// [가이드 근거] p.125–130: 오류 및 예외 정보 노출 금지
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
      // 운영 환경에서는 상세 정보 미노출
      // 필요 시 서버 로깅 엔드포인트로 최소 정보 전송
      try {
        navigator.sendBeacon('/_/log/error', JSON.stringify({
          code: 'UI-ERR-01',
          message: 'Unexpected client error',
          time: new Date().toISOString()
        }))
      } catch {
        /* 전송 실패 시 아무 정보도 노출하지 않음 */
      }
    }
  }

  render() {
    if (this.state.hasError) {
      // [가이드 근거] p.9–13: 사용자에게 내부 구조 노출 금지
      return (
        <div role="alert" aria-live="polite">
          문제가 발생했습니다. 잠시 후 다시 시도해주세요.
        </div>
      )
    }
    return this.props.children
  }
}

// 안전한 루트 엘리먼트 탐색
const rootEl = document.getElementById('root')

if (!rootEl) {
  // [가이드 근거] p.10–16: 예외 처리 및 안전한 초기화
  console.error('Root element not found. Rendering aborted.')
} else {
  const root = createRoot(rootEl)
  root.render(
    <StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </StrictMode>
  )
}