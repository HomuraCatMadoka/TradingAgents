import '@testing-library/jest-dom/vitest'
import 'antd-mobile/es/global'
import { TextDecoder, TextEncoder } from 'node:util'

const createStorage = () => {
  const store = new Map<string, string>()
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value)
    },
    removeItem: (key: string) => {
      store.delete(key)
    },
    clear: () => {
      store.clear()
    },
  }
}

const storage = createStorage()

// @ts-expect-error Node 环境下缺失 window 对象，测试中需要注入
globalThis.localStorage = storage

if (!globalThis.atob) {
  globalThis.atob = (value: string) => Buffer.from(value, 'base64').toString('binary')
}

if (!globalThis.btoa) {
  globalThis.btoa = (value: string) => Buffer.from(value, 'binary').toString('base64')
}

// Vitest 在 node 环境下部分工具需要 TextEncoder/Decoder
if (typeof globalThis.TextEncoder === 'undefined') {
  // @ts-expect-error 覆盖全局类型
  globalThis.TextEncoder = TextEncoder
}

if (typeof globalThis.TextDecoder === 'undefined') {
  // @ts-expect-error 覆盖全局类型
  globalThis.TextDecoder = TextDecoder as unknown as typeof globalThis.TextDecoder
}

export {}
