import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface CompareState {
  ids: number[]
  addItem: (id: number) => void
  removeItem: (id: number) => void
  toggleItem: (id: number) => void
  clearAll: () => void
  isInCompare: (id: number) => boolean
}

export const useCompareStore = create<CompareState>()(
  persist(
    (set, get) => ({
      ids: [],

      addItem: (id) =>
        set((s) => {
          if (s.ids.includes(id) || s.ids.length >= 4) return s
          return { ids: [...s.ids, id] }
        }),

      removeItem: (id) =>
        set((s) => ({ ids: s.ids.filter((i) => i !== id) })),

      toggleItem: (id) => {
        const { ids } = get()
        if (ids.includes(id)) {
          set({ ids: ids.filter((i) => i !== id) })
        } else if (ids.length < 4) {
          set({ ids: [...ids, id] })
        }
      },

      clearAll: () => set({ ids: [] }),

      isInCompare: (id) => get().ids.includes(id),
    }),
    {
      name: 'compare-store',
      partialize: (s) => ({ ids: s.ids }),
    }
  )
)
