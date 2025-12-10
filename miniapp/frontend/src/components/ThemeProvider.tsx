import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { selectTheme, useUIStore } from '@/store/ui'

type Props = {
  children: ReactNode
}

const ThemeProvider = ({ children }: Props) => {
  const theme = useUIStore(selectTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return <>{children}</>
}

export default ThemeProvider
