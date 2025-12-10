import { useEffect } from 'react'
import WebApp from '@twa-dev/sdk'
import { selectTheme, useUIStore } from '@/store/ui'

const applyCssVars = () => {
  const params = WebApp.themeParams
  const root = document.documentElement

  if (params?.bg_color) root.style.setProperty('--tg-bg-color', params.bg_color)
  if (params?.secondary_bg_color) root.style.setProperty('--tg-surface-color', params.secondary_bg_color)
  if (params?.text_color) root.style.setProperty('--tg-text-color', params.text_color)
  if (params?.hint_color) root.style.setProperty('--tg-muted-text', params.hint_color)
  if (params?.link_color) root.style.setProperty('--tg-accent', params.link_color)
}

export const useTelegramTheme = () => {
  const theme = useUIStore(selectTheme)
  const setTheme = useUIStore((state) => state.setTheme)

  useEffect(() => {
    const nextTheme = WebApp.colorScheme === 'dark' ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', nextTheme)
    setTheme(nextTheme)
    applyCssVars()

    const handler = () => {
      const scheme = WebApp.colorScheme === 'dark' ? 'dark' : 'light'
      document.documentElement.setAttribute('data-theme', scheme)
      setTheme(scheme)
      applyCssVars()
    }

    WebApp.onEvent('themeChanged', handler)
    return () => {
      WebApp.offEvent('themeChanged', handler)
    }
  }, [setTheme])

  return theme
}
