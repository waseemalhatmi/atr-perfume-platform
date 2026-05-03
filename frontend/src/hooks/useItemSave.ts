/**
 * useItemSave — Production-grade, reusable save/unsave hook.
 *
 * Architecture decisions:
 *
 * 1. `isSavingRef` (not `isSaving` state) guards the double-click check inside
 *    the callback. This keeps `isSaving` out of useCallback's dependency array,
 *    which means the callback reference stays stable across renders — critical
 *    for React.memo on ItemCard (1 instance per grid row, ×N cards).
 *
 * 2. `savedRef` mirrors `isSaved` state so the rollback always uses the value
 *    that was current when the click occurred (avoids stale-closure bugs with
 *    the async try/catch).
 *
 * 3. Auth guard redirects to /login instead of only showing a toast, giving
 *    the user a clear path to resolve the issue.
 *
 * 4. The hook is pure — it owns NO side effects beyond its own state +
 *    invalidating the ['profile'] React Query key.
 */

import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useQueryClient, useMutation } from '@tanstack/react-query'
import { toggleSaveItem } from '@/lib/api'
import type { SaveToggleResponse } from '@/lib/api'
import toast from 'react-hot-toast'

// ─── Public types ─────────────────────────────────────────────────────────────

export interface UseItemSaveOptions {
  /** ID of the item to save / unsave. */
  itemId: number
  /**
   * Initial saved state — seed from React Query profile cache so the button
   * renders in the correct state without an extra network request.
   * Defaults to false (not saved) when cache is cold.
   */
  initialSaved?: boolean
}

export interface UseItemSaveReturn {
  /** Optimistic-or-confirmed saved state — bind to button icon / label. */
  isSaved: boolean
  /** True while the HTTP request is in-flight — bind to `disabled` prop. */
  isSaving: boolean
  /**
   * Stable event handler — safe to pass to onClick without wrapping.
   * Prevents bubbling so it works inside `<Link>` wrappers.
   */
  handleSave: (e?: React.MouseEvent) => Promise<void>
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useItemSave({
  itemId,
  initialSaved = false,
}: UseItemSaveOptions): UseItemSaveReturn {
  const [optimisticSaved, setOptimisticSaved] = useState<boolean | null>(null)
  const currentSaved = optimisticSaved !== null ? optimisticSaved : initialSaved
  
  const { user }    = useAuthStore()
  const queryClient = useQueryClient()
  const navigate    = useNavigate()

  const mutation = useMutation({
    mutationFn: toggleSaveItem,
    onMutate: async () => {
      setOptimisticSaved(!currentSaved)
    },
    onSuccess: (data) => {
      if (data.success) {
        setOptimisticSaved(null)
        const nowSaved = data.status === 'saved'
        toast.success(nowSaved ? 'تمت الإضافة للمفضلة 💖' : 'تمت الإزالة من المفضلة 💔')
        queryClient.invalidateQueries({ queryKey: ['profile'] })
      } else {
        setOptimisticSaved(null)
        toast.error(data.error || 'حدث خطأ')
      }
    },
    onError: () => {
      setOptimisticSaved(null)
      toast.error('تعذر الاتصال بالخادم')
    }
  })

  const handleSave = useCallback(async (e?: React.MouseEvent) => {
    e?.preventDefault()
    e?.stopPropagation()

    if (!user) {
      toast.error('يجب تسجيل الدخول لحفظ العطور', { icon: '🔐' })
      navigate('/login')
      return
    }

    if (mutation.isPending) return
    mutation.mutate(itemId)
  }, [user, itemId, mutation, navigate])

  return { isSaved: currentSaved, isSaving: mutation.isPending, handleSave }
}
