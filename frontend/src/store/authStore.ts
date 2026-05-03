import { create } from 'zustand'
import { fetchMe, logout as apiLogout, type AuthUser } from '@/lib/api'

interface AuthState {
  user: AuthUser | null
  loading: boolean
  setUser: (u: AuthUser | null) => void
  initialize: () => Promise<void>
  refreshAuth: () => Promise<void>   // silent re-check (no loading spinner)
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user:    null,
  loading: true,

  setUser: (user) => set({ user }),

  initialize: async () => {
    set({ loading: true })
    const user = await fetchMe()
    set({ user, loading: false })
  },

  // Silent re-validation: called on tab-focus / periodic timer.
  // Does NOT set loading=true so the UI doesn't flash.
  refreshAuth: async () => {
    const user = await fetchMe()
    set((prev) => {
      // Only update if state actually changed to avoid unnecessary re-renders
      const wasLoggedIn  = prev.user !== null
      const isLoggedIn   = user !== null
      const idChanged    = prev.user?.id !== user?.id
      if (wasLoggedIn !== isLoggedIn || idChanged) {
        return { user }
      }
      return prev // no-op
    })
  },

  logout: async () => {
    try {
      await apiLogout()
    } catch {
      // If the session is already expired, the server returns 401.
      // We still must clear local state so the UI is consistent.
    } finally {
      set({ user: null })
    }
  },
}))

