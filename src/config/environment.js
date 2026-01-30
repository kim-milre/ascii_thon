// src/config/environment.js
// [시큐어코딩 가이드 근거]
// - 입력값 검증 (p.10~16)
// - 보안 설정 관리 원칙 (p.3~4)
// - 데이터 무결성 보호 (p.83)
// - 오류·로깅 최소화 (p.125~130)
// - 환경 접근 제어 (p.118~122)

const SAFE_PROTOCOLS = new Set(['http:', 'https:'])

function isValidUrl(url) {
  try {
    const parsed = new URL(url)
    return SAFE_PROTOCOLS.has(parsed.protocol)
  } catch {
    return false
  }
}

function getEnvironmentConfig() {
  const isDevelopment = import.meta.env.DEV
  const isProduction = import.meta.env.PROD

  // 안전한 기본값
  const safeDefaults = {
    apiUrl: 'http://localhost:5000',
    clientUrl: 'http://localhost:5173'
  }

  const config = {
    development: {
      apiUrl: import.meta.env.VITE_API_URL || safeDefaults.apiUrl,
      clientUrl: import.meta.env.VITE_CLIENT_URL || safeDefaults.clientUrl
    },
    production: {
      apiUrl: import.meta.env.VITE_API_URL || 'https://sducoss.onrender.com',
      clientUrl: import.meta.env.VITE_CLIENT_URL || 'https://sducoss.netlify.app'
    }
  }

  // URL 및 길이 검증
  Object.entries(config[isDevelopment ? 'development' : 'production']).forEach(([key, value]) => {
    if (typeof value !== 'string' || value.length > 2048 || !isValidUrl(value)) {
      if (!isProduction) console.warn(`⚠️ Invalid ${key} detected, fallback to safe default`)
      config[isDevelopment ? 'development' : 'production'][key] = safeDefaults[key]
    }
  })

  const envConfig = isDevelopment ? config.development : config.production

  // 로그 제한 (운영 환경에서 디버그 차단)
  if (isProduction) {
    console.log = () => {}
    console.warn = () => {}
  }

  // 환경 설정 객체 무결성 강화
  Object.freeze(envConfig)
  Object.preventExtensions(envConfig)
  Object.seal(envConfig)

  // 무단 접근 탐지용 훅
  Object.defineProperty(window, '__envTamperCheck__', {
    get() {
      console.error('⚠️ Unauthorized environment access detected')
      return null
    },
    configurable: false
  })

  return envConfig
}

const rawEnv = Object.freeze({ ...import.meta.env })
const env = getEnvironmentConfig()

export const { apiUrl, clientUrl } = env
export default env