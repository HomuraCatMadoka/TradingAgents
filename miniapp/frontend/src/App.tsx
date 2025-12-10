import { useEffect, useState } from 'react'
import { ErrorBlock } from 'antd-mobile'
import WebApp from '@twa-dev/sdk'
import LoadingState from '@/components/LoadingState'
import AppRouter from '@/router'
import { login, refresh } from '@/services/auth'
import { useTelegramTheme } from '@/hooks/useTelegramTheme'
import { useAuthStore } from '@/store/auth'
import { getRefreshToken, isTokenExpired } from '@/utils/auth'

const App = () => {
  const accessToken = useAuthStore((state) => state.accessToken)
  const refreshToken = useAuthStore((state) => state.refreshToken)
  const logout = useAuthStore((state) => state.logout)
  const [authReady, setAuthReady] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)

  useTelegramTheme()

  useEffect(() => {
    WebApp.ready()
    WebApp.expand()
  }, [])

  useEffect(() => {
    const bootstrapAuth = async () => {
      try {
        setAuthError(null)
        if (accessToken && !isTokenExpired(accessToken)) {
          setAuthReady(true)
          return
        }

        const storedRefresh = refreshToken ?? getRefreshToken()
        if (storedRefresh && !isTokenExpired(storedRefresh)) {
          await refresh()
          setAuthReady(true)
          return
        }

        const initData = WebApp.initData
        if (!initData) {
          throw new Error('缺少 Telegram initData')
        }
        await login(initData)
      } catch (error) {
        console.error('Auth failed', error)
        setAuthError('认证失败，请返回重试')
        logout()
      } finally {
        setAuthReady(true)
      }
    }

    bootstrapAuth()
  }, [accessToken, login, logout, refresh, refreshToken])

  if (!authReady) {
    return <LoadingState message="正在验证身份..." />
  }

  if (authError) {
    return (
      <ErrorBlock status="disconnected" title="认证失败" description={authError} />
    )
  }

  return <AppRouter />
}

export default App
