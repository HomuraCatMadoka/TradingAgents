import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { act } from 'react-dom/test-utils'
import { createRoot, type Root } from 'react-dom/client'

export const createTestClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, suspense: false },
      mutations: { retry: false },
    },
  })

export const renderWithClient = async (node: ReactNode) => {
  const client = createTestClient()
  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)

  await act(async () => {
    root.render(<QueryClientProvider client={client}>{node}</QueryClientProvider>)
  })

  return { container, root, client }
}

export const flushPromises = async () => {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
}

export type TestRoot = Root
