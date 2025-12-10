export const getChartColors = () => {
  const root = document.documentElement
  const getVar = (name: string, fallback: string) => {
    const value = getComputedStyle(root).getPropertyValue(name).trim()
    return value || fallback
  }

  return {
    line: getVar('--tg-theme-link-color', '#3b82f6'),
    fill: getVar('--tg-theme-secondary-bg-color', '#f3f4f6'),
    text: getVar('--tg-theme-text-color', '#111827'),
    grid: '#e5e7eb',
  }
}

export const sampleData = <T,>(data: T[], maxPoints = 100): T[] => {
  if (!Array.isArray(data) || data.length <= maxPoints) return data
  const step = Math.ceil(data.length / maxPoints)
  return data.filter((_, index) => index % step === 0)
}

export const defaultPalette = ['#3b82f6', '#10b981', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9']
