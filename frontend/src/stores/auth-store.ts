// 认证状态管理
import { create } from 'zustand'
import type { User } from '../types'
import { APP_CONFIG } from '../config'
import { storage } from '../utils/storage'

interface AuthState {
  token: string | null
  refreshToken: string | null
  user: User | null
  isAuthenticated: boolean

  setTokens: (token: string, refreshToken: string) => void
  setUser: (user: User) => void
  logout: () => void
  loadFromStorage: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,

  setTokens: (token, refreshToken) => {
    storage.set(APP_CONFIG.tokenKey, token)
    storage.set(APP_CONFIG.refreshTokenKey, refreshToken)
    set({ token, refreshToken, isAuthenticated: true })
  },

  setUser: (user) => {
    set({ user })
  },

  logout: () => {
    storage.remove(APP_CONFIG.tokenKey)
    storage.remove(APP_CONFIG.refreshTokenKey)
    set({ token: null, refreshToken: null, user: null, isAuthenticated: false })
  },

  loadFromStorage: () => {
    const token = storage.get<string>(APP_CONFIG.tokenKey)
    const refreshToken = storage.get<string>(APP_CONFIG.refreshTokenKey)
    if (token) {
      set({ token, refreshToken, isAuthenticated: true })
    }
  },
}))
