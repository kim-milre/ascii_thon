import api from './api';
import { apiUrl } from '../config/environment';


const API_BASE_URL = apiUrl;

const sanitizeInput = (data) => {
  if (!data || typeof data !== 'object') return {};
  const sanitized = {};
  for (const key in data) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      const value = data[key];
      // 단순 문자열 필터링 (스크립트 삽입 방지)
      sanitized[key] =
        typeof value === "string"
          ? value.replace(/[<>\"'();]/g, "")
          : value;
    }
  }
  return sanitized;
};

export const authAPIService = {
  register: async (userData) => {
    console.log("📨 회원가입 요청 데이터:", userData);
    return await api.post("/api/auth/register", userData, {
      headers: { "Content-Type": "application/json" },
    });
  },
  login: async (credentials) => {
    const safeCreds = sanitizeInput(credentials);
    try {
      return await api.post("/api/auth/login", safeCreds, {
        headers: {
          "Content-Type": "application/json",
          "X-Frame-Options": "DENY",
          "X-XSS-Protection": "1; mode=block",
        },
        withCredentials: true,
      });
    } catch {
      throw new Error("로그인 실패. 입력값을 확인해주세요.");
    }
  },

  logout: async () => {
    try {
      return await api.post('/api/auth/logout', {}, { withCredentials: true });
    } catch {
      throw new Error("로그아웃 처리 중 오류가 발생했습니다.");
    }
  },


  getCurrentUser: async () => {
    return await api.get('/api/auth/me', { withCredentials: true });
  },


  getAllUsers: async () => {
    return await api.get('/api/users/all', { withCredentials: true });
  },

  changeUserType: async (userId, userType) => {
    if (!/^[a-zA-Z0-9_-]+$/.test(userId)) throw new Error("잘못된 사용자 ID 형식입니다.");
    return await api.put(`/api/users/${userId}/type`, { userType }, { withCredentials: true });
  },
}


export const authAPI = authAPIService;
