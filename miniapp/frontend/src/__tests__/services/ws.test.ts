import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

const sockets: MockWebSocket[] = []

class MockWebSocket {
  static OPEN = 1
  static CLOSED = 3
  static CONNECTING = 0

  url: string
  readyState = MockWebSocket.CONNECTING
  onopen?: () => void
  onmessage?: (event: MessageEvent) => void
  onclose?: (event: CloseEvent) => void
  onerror?: (event: Event) => void
  sent: any[] = []

  constructor(url: string) {
    this.url = url
    sockets.push(this)
  }

  send(data: any) {
    this.sent.push(data)
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.({} as CloseEvent)
  }
}

vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket)

const importModule = async (url = 'ws://example.com/ws') => {
  vi.resetModules()
  vi.stubEnv('VITE_WS_URL', url)
  return import('@/services/ws')
}

beforeEach(() => {
  sockets.length = 0
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllEnvs()
})

describe('RealtimeClient', () => {
  it('使用 token 建立连接并发送消息', async () => {
    const { RealtimeClient } = await importModule()
    const onOpen = vi.fn()
    const client = new RealtimeClient({ onOpen })

    client.connect('token-123')

    expect(sockets[0]?.url).toContain('token=token-123')
    sockets[0]!.readyState = MockWebSocket.OPEN
    sockets[0]?.onopen?.()

    expect(onOpen).toHaveBeenCalled()

    client.send({ action: 'ping' })
    expect(sockets[0]?.sent).toContain(JSON.stringify({ action: 'ping' }))
  })

  it('断线自动重连，手动断开则停止重连', async () => {
    vi.useFakeTimers()
    const { RealtimeClient } = await importModule('ws://example.com/feed')
    const client = new RealtimeClient()
    const connectSpy = vi.spyOn(client, 'connect')

    client.connect('abc')
    sockets[0]!.readyState = MockWebSocket.OPEN
    sockets[0]?.onclose?.({} as CloseEvent)

    vi.runOnlyPendingTimers()
    expect(connectSpy).toHaveBeenCalledTimes(2)

    const reopened = sockets[1]
    reopened!.readyState = MockWebSocket.OPEN
    client.disconnect()
    reopened?.onclose?.({} as CloseEvent)
    vi.runOnlyPendingTimers()

    expect(connectSpy).toHaveBeenCalledTimes(2)
  })
})
