import { create } from 'zustand'
import type { AuthResult, AuthTokens, Session, User } from '@/types/auth'
import {
  clearRefreshToken,
  getRefreshToken,
  setAccessToken as cacheAccessToken,
  setRefreshToken,
} from '@/utils/auth'

type AuthState = {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  session: Session | null
  setAuth: (payload: AuthResult) => void
  setTokens: (tokens: AuthTokens) => void
  logout: () => void
}

const persistTokens = (tokens: AuthTokens | null) => {
  cacheAccessToken(tokens?.accessToken ?? null)
  if (tokens?.refreshToken) {
    setRefreshToken(tokens.refreshToken)
  } else {
    clearRefreshToken()
  }
}

const initialRefreshToken = getRefreshToken()

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  refreshToken: initialRefreshToken,
  session: null,
  setAuth: ({ user, tokens, session }) => {
    persistTokens(tokens)
    set({
      user,
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      session: session ?? null,
    })
  },
  setTokens: (tokens) =>
    set((state) => {
      persistTokens(tokens)
      return {
        ...state,
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      }
    }),
  logout: () => {
    persistTokens(null)
    set({ user: null, accessToken: null, refreshToken: null, session: null })
  },
}))

export const selectToken = (state: AuthState) => state.accessToken
