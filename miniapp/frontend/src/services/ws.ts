import { useAuthStore } from '@/store/auth'

type Handlers = {
  onMessage?: (data: MessageEvent) => void
  onOpen?: () => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
}

const baseWsUrl =
  (import.meta.env.VITE_WS_URL as string | undefined)?.replace(/\/$/, '') || ''

export class RealtimeClient {
  private socket: WebSocket | null = null
  private handlers: Handlers = {}
  private reconnectAttempts = 0
  private manualClose = false
  private authToken: string | null = null

  constructor(handlers?: Handlers) {
    this.handlers = handlers ?? {}
  }

  connect(token?: string) {
    const wsUrl = this.buildUrl(token)
    if (!wsUrl) return

    if (this.socket) {
      this.disconnect()
    }

    this.authToken = token ?? null
    this.manualClose = false

    this.socket = new WebSocket(wsUrl)
    this.socket.onopen = () => {
      this.reconnectAttempts = 0
      this.handlers.onOpen?.()
    }
    this.socket.onmessage = (event) => this.handlers.onMessage?.(event)
    this.socket.onerror = (event) => {
      this.handlers.onError?.(event)
      this.socket?.close()
    }
    this.socket.onclose = (event) => {
      this.handlers.onClose?.(event)
      if (!this.manualClose) {
        this.scheduleReconnect()
      }
    }
  }

  send(data: string | Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      const payload = typeof data === 'string' ? data : JSON.stringify(data)
      this.socket.send(payload)
    }
  }

  disconnect() {
    this.manualClose = true
    this.socket?.close()
    this.socket = null
  }

  private scheduleReconnect() {
    this.reconnectAttempts += 1
    const delay = Math.min(30000, 1000 * 2 ** this.reconnectAttempts)
    window.setTimeout(() => {
      this.connect(this.authToken ?? undefined)
    }, delay)
  }

  private buildUrl(token?: string) {
    if (!baseWsUrl) return null
    try {
      const url = new URL(baseWsUrl)
      if (token) {
        url.searchParams.set('token', token)
      }
      return url.toString()
    } catch {
      return null
    }
  }
}

export const realtimeClient = new RealtimeClient()

useAuthStore.subscribe(
  (state) => state.accessToken,
  (token) => {
    if (!token) {
      realtimeClient.disconnect()
      return
    }
    realtimeClient.connect(token)
  },
)
