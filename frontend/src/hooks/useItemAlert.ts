import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useQueryClient, useMutation } from '@tanstack/react-query'
import { subscribePriceAlert, deletePriceAlert } from '@/lib/api'
import toast from 'react-hot-toast'

interface UseItemAlertOptions {
  itemId: number
  initialHasAlert?: boolean
}

export function useItemAlert({ itemId, initialHasAlert = false }: UseItemAlertOptions) {
  const [optimisticAlert, setOptimisticAlert] = useState<boolean | null>(null)
  const currentHasAlert = optimisticAlert !== null ? optimisticAlert : initialHasAlert
  
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const subscribeMutation = useMutation({
    mutationFn: (price: number) => subscribePriceAlert(itemId, user?.email || '', price),
    onMutate: () => setOptimisticAlert(true),
    onSuccess: (res) => {
      if (res.success) {
        setOptimisticAlert(null)
        toast.success('تم تفعيل تنبيه السعر بنجاح 🔔')
        queryClient.invalidateQueries({ queryKey: ['profile'] })
      } else {
        setOptimisticAlert(null)
        toast.error(res.error || 'حدث خطأ أثناء تفعيل التنبيه')
      }
    },
    onError: () => {
      setOptimisticAlert(null)
      toast.error('خطأ في الاتصال')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: () => deletePriceAlert(itemId),
    onMutate: () => setOptimisticAlert(false),
    onSuccess: (res) => {
      if (res.success) {
        setOptimisticAlert(null)
        toast.success('تم إلغاء تنبيه السعر 🔕')
        queryClient.invalidateQueries({ queryKey: ['profile'] })
      } else {
        setOptimisticAlert(null)
        toast.error(res.error || 'حدث خطأ أثناء إلغاء التنبيه')
      }
    },
    onError: () => {
      setOptimisticAlert(null)
      toast.error('خطأ في الاتصال')
    }
  })

  const toggleAlert = useCallback((targetPrice?: number) => {
    if (!user) {
      toast.error('يجب تسجيل الدخول لإدارة التنبيهات', { icon: '🔐' })
      navigate('/login')
      return
    }

    if (currentHasAlert) {
      deleteMutation.mutate()
    } else if (targetPrice) {
      subscribeMutation.mutate(targetPrice)
    }
  }, [user, currentHasAlert, deleteMutation, subscribeMutation, navigate])

  return { 
    hasAlert: currentHasAlert, 
    isLoading: subscribeMutation.isPending || deleteMutation.isPending,
    toggleAlert 
  }
}
