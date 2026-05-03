import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

export const fetchSavedBatch = async (ids: number[]): Promise<Record<string, boolean>> => {
  if (!ids || ids.length === 0) return {}
  const params = new URLSearchParams()
  ids.forEach(id => {
    params.append('type', 'item')
    params.append('id', id.toString())
  })
  
  const res = await api.get('/check-save-batch', { params })
  return res.data
}

export const useSavedItems = (ids: number[]) => {
  const user = useAuthStore(s => s.user)
  
  return useQuery({
    queryKey: ['saved-batch', ids.join(',')],
    queryFn: () => fetchSavedBatch(ids),
    // Only fetch if user is logged in and we have IDs
    enabled: !!user && ids.length > 0,
    staleTime: 60 * 1000, // 1 minute
    retry: 1,
  })
}
