import { useQuery } from '@tanstack/react-query'
import { fetchProfile } from '@/lib/api'
import { useMemo } from 'react'
import { useAuthStore } from '@/store/authStore'

export function useProfileData() {
  const { user } = useAuthStore()
  
  const { data, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: fetchProfile,
    enabled: !!user,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: true,
  })

  const profileData = useMemo(() => {
    if (!data?.data) return { savedSet: new Set<number>(), alertSet: new Set<number>() }
    
    return {
      savedSet: new Set(data.data.saved_item_ids || []),
      alertSet: new Set(data.data.alert_item_ids || []),
    }
  }, [data])

  return { ...profileData, isLoading }
}
