import { ErrorBlock } from 'antd-mobile'
import { Suspense, lazy, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import ErrorBoundary from '@/components/ErrorBoundary'
import LoadingState from '@/components/LoadingState'
import { selectToken, useAuthStore } from '@/store/auth'

const Layout = lazy(() => import('@/components/Layout'))
const Analysis = lazy(() => import('@/pages/Analysis'))
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Protocols = lazy(() => import('@/pages/Protocols'))
const ProtocolDetail = lazy(() => import('@/pages/ProtocolDetail'))
const History = lazy(() => import('@/pages/History'))
const Favorites = lazy(() => import('@/pages/Favorites'))
const Settings = lazy(() => import('@/pages/Settings'))
const Watchlist = lazy(() => import('@/pages/Watchlist'))

type GuardProps = {
  children: ReactNode
}

const RequireAuth = ({ children }: GuardProps) => {
  const token = useAuthStore(selectToken)
  if (!token) {
    return <Navigate to="/error" replace />
  }
  return children
}

const withSuspense = (node: ReactNode) => (
  <Suspense fallback={<LoadingState message="内容加载中..." />}>{node}</Suspense>
)

const AppRouter = () => (
  <ErrorBoundary>
    <BrowserRouter>
      <Routes>
        <Route element={withSuspense(<Layout />)}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/dashboard"
            element={<RequireAuth>{withSuspense(<Dashboard />)}</RequireAuth>}
          />
          <Route
            path="/analysis"
            element={<RequireAuth>{withSuspense(<Analysis />)}</RequireAuth>}
          />
          <Route
            path="/protocols"
            element={<RequireAuth>{withSuspense(<Protocols />)}</RequireAuth>}
          />
          <Route
            path="/protocols/:slug"
            element={<RequireAuth>{withSuspense(<ProtocolDetail />)}</RequireAuth>}
          />
          <Route
            path="/history"
            element={<RequireAuth>{withSuspense(<History />)}</RequireAuth>}
          />
          <Route
            path="/favorites"
            element={<RequireAuth>{withSuspense(<Favorites />)}</RequireAuth>}
          />
          <Route
            path="/watchlist"
            element={<RequireAuth>{withSuspense(<Watchlist />)}</RequireAuth>}
          />
          <Route
            path="/settings"
            element={<RequireAuth>{withSuspense(<Settings />)}</RequireAuth>}
          />
        </Route>
        <Route
          path="/error"
          element={
            <ErrorBlock
              status="disconnected"
              title="未认证"
              description="缺少有效的登录状态，请重新打开应用"
            />
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  </ErrorBoundary>
)

export default AppRouter
