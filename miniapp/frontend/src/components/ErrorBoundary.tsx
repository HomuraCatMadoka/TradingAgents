import { Button, ErrorBlock } from 'antd-mobile'
import { Component, type ErrorInfo, type ReactNode } from 'react'

type FallbackRender =
  | ReactNode
  | ((args: { error: Error | null; reset: () => void }) => ReactNode)

type Props = {
  children: ReactNode
  fallback?: FallbackRender
  onReset?: () => void
}

type State = { hasError: boolean; error: Error | null }

class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // 生产环境可在此接入 Sentry/LogRocket 等监控
    console.error('ErrorBoundary 捕获错误', error, info)
  }

  handleRetry = () => {
    this.props.onReset?.()
    this.setState({ hasError: false, error: null })
  }

  renderFallback() {
    const { fallback } = this.props
    if (typeof fallback === 'function') {
      return fallback({ error: this.state.error, reset: this.handleRetry })
    }
    if (fallback) {
      return fallback
    }

    return (
      <ErrorBlock
        status="default"
        title="页面出错了"
        description={
          <Button color="primary" onClick={this.handleRetry}>
            重试
          </Button>
        }
      />
    )
  }

  render() {
    if (this.state.hasError) {
      return this.renderFallback()
    }

    return this.props.children
  }
}

export default ErrorBoundary
