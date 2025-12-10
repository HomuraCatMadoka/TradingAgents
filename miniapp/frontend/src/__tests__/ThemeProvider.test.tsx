import { describe, it, expect, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import ThemeProvider from '@/components/ThemeProvider'
import { useUIStore } from '@/store/ui'

beforeEach(() => {
  useUIStore.setState((state) => ({ ...state, theme: 'light', loading: false, error: null }))
  document.documentElement.removeAttribute('data-theme')
})

describe('ThemeProvider', () => {
  it('根据 theme 设置 data-theme 属性', async () => {
    render(<ThemeProvider>内容</ThemeProvider>)

    await waitFor(() => expect(document.documentElement.getAttribute('data-theme')).toBe('light'))

    useUIStore.getState().setTheme('dark')

    await waitFor(() => expect(document.documentElement.getAttribute('data-theme')).toBe('dark'))
  })
})
