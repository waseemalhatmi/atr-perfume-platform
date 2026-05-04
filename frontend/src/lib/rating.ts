import { Item } from './api'

// Fix #5: Dynamic Rating System
export function calculateRating(item: Item | any): string {
  if (!item) return '4.0'
  
  // Base rating for all luxury items is 4.0
  let score = 4.0
  
  // Calculate bonus based on views (max 0.5 bonus)
  const views = item.view_count || 0
  const viewBonus = Math.min(0.5, views / 2000)
  
  // Calculate bonus based on number of variants/stores as a proxy for popularity (max 0.5 bonus)
  const variants = item.variants?.length || 1
  const popularityBonus = Math.min(0.5, variants * 0.1)
  
  score += viewBonus + popularityBonus
  
  return Math.min(5.0, score).toFixed(1)
}
