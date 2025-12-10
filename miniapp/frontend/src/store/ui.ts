import { create } from 'zustand'

type Theme = 'light' | 'dark'

type UIState = {
  theme: Theme
  loading: boolean
  error: string | null
  setTheme: (theme: Theme) => void
  setLoading: (loading: boolean) => void
  setError: (message: string | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  theme: 'light',
  loading: false,
  error: null,
  setTheme: (theme) => set({ theme }),
  setLoading: (loading) => set({ loading }),
  setError: (message) => set({ error: message }),
}))

export const selectTheme = (state: UIState) => state.theme
