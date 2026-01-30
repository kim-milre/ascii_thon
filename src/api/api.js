import axios from 'axios';

const sanitizeInput = (data) => {
  if (!data || typeof data !== 'object') return data;
  const sanitized = {};
  for (const key in data) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      const val = data[key];
      sanitized[key] =
        typeof val === 'string'
          ? val.replace(/[<>\"'();]/g, '')
          : val;
    }
  }
  return sanitized;
};

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://sducoss.onrender.com',
  timeout: 300000,
  withCredentials: true,
});

api.defaults.headers.common['Content-Type'] = 'application/json';
api.defaults.headers.common['X-Content-Type-Options'] = 'nosniff';
api.defaults.headers.common['X-Frame-Options'] = 'DENY';

/* =========================
   요청 인터셉터
   ========================= */
api.interceptors.request.use((config) => {
  const isAuth =
    config.url?.includes('/api/auth/login') ||
    config.url?.includes('/api/auth/register');

  if (!isAuth && config.data && typeof config.data === 'object') {
    config.data = sanitizeInput(config.data);
  }

  return config;
});

/* =========================
   응답 인터셉터
   ========================= */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 🔐 토큰 만료/위조 시 자동 로그아웃
    if (error?.response?.status === 401) {
      localStorage.removeItem('accessToken');
    }

    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error.message ||
      'API 요청 중 오류 발생';

    console.error('❌ API 에러:', msg);
    return Promise.reject(new Error(msg));
  }
);

/* =========================
   기존 API 그대로 유지
   ========================= */
export const complianceAPI = {
  runFullAnalysis: async (url, navigate) => {
    try {
      const response = await api.post('/api/sites/process', { url });
      console.log('🔥 PROCESS RESPONSE:', response); // ← 여기

      const result = response.data;

      if (!result || typeof result !== 'object') {
        throw new Error('서버 응답이 비정상입니다.');
      }

      if (!result.site_id) {
        throw new Error('분석 결과를 가져오지 못했습니다.');
      }
      return result;

    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.message ||
        '알 수 없는 오류가 발생했습니다.';
      console.error('❌ 전체 분석 중 오류:', message);
      throw new Error(message);
    }
  },

  analyzePolicies: async (htmlContent) => {
    const response = await api.post('/api/sites/process', { html: htmlContent });
    return response.data;
  },

  detectRisks: async (text) => {
    const response = await api.post('/api/detect', { text });
    return response.data;
  },

  judgeRisk: async (analysisResults) => {
    const response = await api.post('/api/judge', analysisResults);
    return response.data;
  },

  maskContent: async (htmlContent) => {
    const response = await api.post('/api/mask', { html: htmlContent });
    return response.data;
  },

  getSiteProgress: async (id) => {
    const response = await api.get(`/api/sites/${id}/progress`);
    return response.data;
  },

  getAnalyzedSites: async () => {
    const response = await api.get('/api/sites');
    return response.data;
  },

  getSiteResult: async (id) => {
    const response = await api.get(`/api/sites/${id}`);
    return response.data;
  },

  deleteSite: async (id) => {
    const response = await api.delete(`/api/sites/${id}`);
    return response.data;
  },

  deleteAllSites: async () => {
    const response = await api.delete('/api/sites');
    return response.data;
  },
};

export default api;