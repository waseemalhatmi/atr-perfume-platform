import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ThemeState {
  isDark: boolean
  toggleTheme: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      isDark: true, // Default to dark for luxury feel
      toggleTheme: () => set((state) => {
        const next = !state.isDark
        if (next) document.documentElement.classList.add('dark')
        else document.documentElement.classList.remove('dark')
        return { isDark: next }
      }),
    }),
    { name: 'theme-storage' }
  )
)
