import { useQuery } from '@tanstack/react-query'
import { fetchPriceHistory } from '@/lib/api'

export interface PricePoint {
  date: string
  price: number
}

export const usePriceHistory = (itemId: number) => {
  return useQuery({
    queryKey: ['price-history', itemId],
    queryFn: () => fetchPriceHistory(itemId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    // Only fetch if itemId is valid
    enabled: !!itemId,
  })
}
