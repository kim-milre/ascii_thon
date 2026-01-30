//AuthContext.jsx
import React, { createContext, useContext, useRef, useState, useEffect } from 'react'
import { authAPIService as authAPI } from '../api/authApi'
import api from '../api/api'

const USE_PERSISTENT_STORAGE = true
const STORAGE = typeof window !== 'undefined' ? localStorage : null

const AuthContext = createContext()

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
useAuth.displayName = 'useAuth'

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const mounted = useRef(true)

  const safeSet = (fn) => mounted.current && fn()

  const readToken = () => {
    try {
      if (!STORAGE) return null
      const v = STORAGE.getItem('token')
      return typeof v === 'string' && v.length > 0 ? v : null
    } catch { return null }
  }
  const writeToken = (t) => {
    try {
      if (!STORAGE) return
      if (t) STORAGE.setItem('token', t)
      else STORAGE.removeItem('token')
    } catch {}
  }

  const applyAuthHeader = (t) => {
    if (t) api.defaults.headers.common['Authorization'] = `Bearer ${t}`
    else delete api.defaults.headers.common['Authorization']
  }

  const clearAuthState = () => {
    writeToken(null)
    applyAuthHeader(null)
    safeSet(() => {
      setUser(null)
      setToken(null)
      setIsAuthenticated(false)
    })
  }


  const checkAuthStatus = async (manualToken) => {
    try {
      safeSet(() => setIsLoading(true))
      const stored = manualToken || readToken()
      if (!stored) {
        clearAuthState()
        return
      }
      applyAuthHeader(stored)
      const res = await authAPI.getCurrentUser()

      const u = res?.data?.data?.user
      const ok = res?.data?.success && u
      if (!ok) {
        clearAuthState()
        return
      }
      safeSet(() => {
        setUser(u)
        setToken(stored)
        setIsAuthenticated(true)
      })
    } catch {
      clearAuthState()
    } finally {
      safeSet(() => setIsLoading(false))
    }
  }

  const login = async ({ email, password }) => {
    try {      
      const payload = {
        email: String(email || '').trim(),
        password: String(password || ''),
      }
      const res = await authAPI.login(payload)
      const accessToken = res?.data?.data?.access_token
      if (res?.data?.success && accessToken) {
        writeToken(accessToken)
        applyAuthHeader(accessToken)
        safeSet(() => setToken(accessToken))
        await checkAuthStatus(accessToken)
      }
      return res?.data ?? { success: false }
    } catch (error) {
      return {
        success: false,
        message: '로그인 실패',
      }
    }
  }

   const register = async ({ name, email, password }) => {
     try {
       const payload = {
         name: String(name || '').trim(),
         email: String(email || '').trim(),
         password: String(password || ''),
       }

       console.log('REGISTER PAYLOAD FINAL:', payload)

       const res = await authAPI.register(payload)

       if (res?.data?.success) {
         return { success: true }
       }

       return { success: false, message: '회원가입 실패' }
     } catch {
       return { success: false, message: '회원가입 중 오류' }
     }
   }

  const logout = async () => {
    try {      
      if (token) await api.post('/api/auth/logout')
    } catch {}
    finally {
      clearAuthState()
    }
  }

  const isAdmin = () => user?.userType === 'admin'

  useEffect(() => {
    mounted.current = true
    checkAuthStatus()
    return () => { mounted.current = false }
  }, [])

  const value = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    isAdmin,
    checkAuthStatus,
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}