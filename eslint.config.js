// npm install --save-dev eslint-plugin-promise 실행
// eslint.config.js
// [시큐어코딩 가이드 근거]
// - 민감정보 하드코딩 금지 (p.70~75)
// - 안전한 코드 작성 습관: eval/new Function 사용 금지 (p.9~13)
// - 예외처리 누락 방지 및 입력 검증 강화 (p.10~16)
// - 로깅 시 민감정보 출력 금지 (p.125~130)

import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'node_modules']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      // 기존 규칙
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],

      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',

      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-restricted-syntax': [
        'error',
        {
          selector:
            "Literal[value=/^(?:[A-Za-z0-9]{32,}|sk-[A-Za-z0-9]{20,})$/]",
          message:
            '비밀키 또는 토큰을 직접 코드에 하드코딩하지 마세요. 환경변수(VITE_*)를 사용하세요.',
        },
      ],

      'no-restricted-imports': [
        'error',
        {
          patterns: ['**/eval', '**/vm', '**/child_process', '**/fs'],
          message:
            '보안상 위험한 모듈 import 금지: eval/vm/child_process/fs 등은 브라우저 번들에 포함되지 않아야 합니다.',
        },
      ],

      'no-floating-promises': 'warn',
      'react/jsx-no-script-url': 'error',
      'react/jsx-no-target-blank': ['error', { enforceDynamicLinks: 'always' }],
      'no-debugger': 'error',
      'no-unsafe-finally': 'error',
      'no-var': 'error',
    },
  },
])