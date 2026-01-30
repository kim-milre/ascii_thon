// vite.config.js
// [시큐어코딩 가이드 근거]
// - 빌드 정보 노출 제한 및 무결성 보호: p.80~84
// - 디버그 정보·소스맵 비활성화: p.125~130
// - 환경별 설정 분리 원칙: p.3~4
// - 민감정보 하드코딩 방지: p.70~75

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'fs'

let pkg = { version: '0.0.0' }
try {
  const raw = readFileSync('./package.json', 'utf-8')
  pkg = JSON.parse(raw)
} catch (e) {
  console.warn('⚠️ package.json 읽기 실패, 기본 버전 사용')
}

const buildTag = `${pkg.version}-${Date.now()}`

// 빌드 환경에 따른 보안 설정
const isProduction = process.env.NODE_ENV === 'production'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: !isProduction,
    rollupOptions: {
      output: {
        // [무결성 보호] 파일명에 빌드 태그 추가로 캐시·서명 검증 용이
        entryFileNames: `assets/[name]-${buildTag}.js`,
        chunkFileNames: `assets/[name]-${buildTag}.js`,
        assetFileNames: `assets/[name]-${buildTag}.[ext]`,
      },
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: isProduction,
        drop_debugger: isProduction,
      },
    },
  },
  define: {
    __BUILD_TAG__: JSON.stringify(buildTag),
  },
})