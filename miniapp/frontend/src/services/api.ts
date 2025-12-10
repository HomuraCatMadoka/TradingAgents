import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type AxiosRequestHeaders,
} from 'axios'
import { useAuthStore } from '@/store/auth'
import type { AuthResponse, AuthResult } from '@/types/auth'
import { extractAuthResult, getAccessToken, getRefreshToken } from '@/utils/auth'

export const apiBase =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || ''

export const apiClient = axios.create({
  baseURL: apiBase || undefined,
  timeout: 10000,
})

type RequestConfig = AxiosRequestConfig & { _retry?: boolean; _skipAuthRefresh?: boolean }

let refreshPromise: Promise<AuthResult> | null = null
let subscribers: Array<(result: AuthResult | null, error?: unknown) => void> = []

const notifySubscribers = (result: AuthResult | null, error?: unknown) => {
  subscribers.forEach((cb) => cb(result, error))
  subscribers = []
}

const startRefresh = async (): Promise<AuthResult> => {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('缺少 refresh token')
  }
  const response = await apiClient.post<AuthResponse>(
    '/api/auth/refresh',
    { refreshToken },
    { _skipAuthRefresh: true },
  )
  const authResult = extractAuthResult(response.data, refreshToken)
  useAuthStore.getState().setAuth(authResult)
  return authResult
}

apiClient.interceptors.request.use((config) => {
  const requestConfig = config as RequestConfig
  if (requestConfig._skipAuthRefresh) {
    return config
  }
  const token = getAccessToken()
  if (token) {
    const headers = (config.headers ?? {}) as AxiosRequestHeaders
    headers.Authorization = `Bearer ${token}`
    config.headers = headers
  }
  return config
})

const handleAuthError = async (error: AxiosError) => {
  const status = error.response?.status
  const originalRequest = (error.config ?? {}) as RequestConfig

  if (
    status !== 401 ||
    originalRequest._retry ||
    originalRequest._skipAuthRefresh
  ) {
    return Promise.reject(error)
  }

  if (!getRefreshToken()) {
    useAuthStore.getState().logout()
    return Promise.reject(error)
  }

  const retryOriginalRequest = new Promise((resolve, reject) => {
    subscribers.push((result, refreshError) => {
      if (!result) {
        reject(refreshError ?? error)
        return
      }
      const headers = (originalRequest.headers ?? {}) as AxiosRequestHeaders
      headers.Authorization = `Bearer ${result.tokens.accessToken}`
      originalRequest.headers = headers
      originalRequest._retry = true
      resolve(apiClient(originalRequest))
    })
  })

  if (!refreshPromise) {
    refreshPromise = startRefresh().finally(() => {
      refreshPromise = null
    })
  }

  try {
    const refreshResult = await refreshPromise
    notifySubscribers(refreshResult)
  } catch (refreshError) {
    notifySubscribers(null, refreshError)
    useAuthStore.getState().logout()
  }

  return retryOriginalRequest
}

apiClient.interceptors.response.use(
  (response) => {
    if (response.status !== 401) return response
    const syntheticError = new AxiosError(
      'Unauthorized',
      AxiosError.ERR_BAD_REQUEST,
      response.config,
      response.request,
      response,
    )
    return handleAuthError(syntheticError)
  },
  (error: AxiosError) => handleAuthError(error),
)
