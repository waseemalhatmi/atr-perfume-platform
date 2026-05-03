import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, Bell, Star, Heart, ArrowRightLeft } from 'lucide-react'
import type { Item } from '@/lib/api'
import { imageUrl } from '@/lib/api'
import { calculateRating } from '@/lib/rating'
import { useState, useCallback, memo } from 'react'
import { useCompareStore } from '@/store/compareStore'
import { useQueryClient } from '@tanstack/react-query'
import { useItemSave } from '@/hooks/useItemSave'
import { useItemAlert } from '@/hooks/useItemAlert'
import PriceAlertModal from './PriceAlertModal'
import { useAnalytics } from '@/hooks/useAnalytics'

interface Props {
  item: Item
  index?: number
  isSaved?: boolean
  hasAlert?: boolean
}

function ItemCard({ item, index = 0, isSaved: initialSaved = false, hasAlert: initialHasAlert = false }: Props) {
  const [alertOpen, setAlertOpen] = useState(false)
  const { toggleItem, isInCompare } = useCompareStore()
  const inCompare = isInCompare(item.id)
  const { track } = useAnalytics()

  const { isSaved, isSaving, handleSave } = useItemSave({
    itemId: item.id,
    initialSaved,
  })

  const { hasAlert, toggleAlert } = useItemAlert({
    itemId: item.id,
    initialHasAlert,
  })

  const handleToggleCompare = useCallback(() => {
    track('item_compare_toggled', { itemId: item.id, itemName: item.name })
    toggleItem(item.id)
  }, [toggleItem, item.id, item.name, track])

  const handleOpenAlert  = useCallback(() => {
    track('price_alert_opened', { itemId: item.id, itemName: item.name })
    setAlertOpen(true)
  }, [item.id, item.name, track])

  const handleCloseAlert = useCallback(() => setAlertOpen(false), [])

  const thumb = item.images[0]
    ? imageUrl(item.images[0].path)
    : '/placeholder.jpg'

  return (
    <>
      <motion.article
        className="luxury-card group"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay: index * 0.05 }}
      >
        <div className="relative aspect-[3/4] overflow-hidden rounded-t-2xl">
          <Link to={`/items/${item.id}`}>
            <img
              src={thumb}
              alt={item.name}
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              loading="lazy"
            />
          </Link>

          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

          {/* Badges */}
          <div className="absolute top-4 left-4 flex flex-col gap-2">
            <span className="badge--luxury text-[10px] py-1">PREMIUM</span>
          </div>

          {/* Save button ❤️ */}
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            aria-label={isSaved ? 'إزالة من المفضلة' : 'حفظ في المفضلة'}
            className="absolute top-4 right-4 w-9 h-9 rounded-full glass flex items-center justify-center transition-all hover:scale-110 active:scale-95 disabled:opacity-50"
          >
            <motion.div
              animate={{ scale: isSaved ? [1, 1.3, 1] : 1 }}
              transition={{ duration: 0.3 }}
            >
              <Heart
                size={18}
                className={`transition-colors duration-300 ${isSaved ? 'fill-red-600 text-red-600' : 'text-white'}`}
              />
            </motion.div>
          </button>

          {/* Quick actions overlay */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 opacity-0 group-hover:opacity-100 translate-y-4 group-hover:translate-y-0 transition-all duration-300">
            <Link
              to={`/items/${item.id}`}
              className="btn-gold !py-2 !px-4 text-xs flex items-center gap-1 shadow-2xl"
            >
              <Eye size={14} />
            </Link>
            
            <button
              type="button"
              onClick={handleToggleCompare}
              className={`glass !p-2.5 rounded-full shadow-2xl transition-all ${
                inCompare ? 'bg-primary text-primary-foreground' : ''
              }`}
            >
              <ArrowRightLeft size={14} />
            </button>

            {/* Price Alert Button 🔔 */}
            <button
              type="button"
              onClick={hasAlert ? () => toggleAlert() : handleOpenAlert}
              className="glass !p-2.5 rounded-full shadow-2xl transition-all hover:scale-110"
            >
              <motion.div
                animate={{ rotate: hasAlert ? [0, -15, 15, 0] : 0 }}
                transition={{ duration: 0.5, repeat: hasAlert ? Infinity : 0, repeatDelay: 3 }}
              >
                <Bell 
                  size={14} 
                  className={`transition-colors duration-300 ${hasAlert ? 'fill-yellow-500 text-yellow-500' : 'text-white'}`}
                />
              </motion.div>
            </button>
          </div>
        </div>

        <div className="p-5">
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-primary/80">
              {item.brand.name}
            </span>
            <div className="flex items-center gap-1">
              <Star size={10} className="text-yellow-500 fill-current" />
              <span className="text-[10px] font-bold">{calculateRating(item)}</span>
            </div>
          </div>

          <Link to={`/items/${item.id}`}>
            <h3 className="font-bold text-sm md:text-base mb-3 line-clamp-1 group-hover:text-primary transition-colors">
              {item.name}
            </h3>
          </Link>

          <div className="flex items-center justify-between pt-3 border-t border-border/30">
            <div className="flex flex-col">
              <span className="text-[10px] text-muted-foreground">يبدأ من</span>
              <span className="item-price-range text-base md:text-lg font-bold luxury-text">
                {item.min_price > 0
                  ? `${item.min_price.toFixed(0)} ${item.currency || 'SAR'}`
                  : 'اتصل'}
              </span>
            </div>
            <div className="text-[10px] px-2 py-1 rounded bg-secondary text-muted-foreground font-bold">
              {item.category.name}
            </div>
          </div>
        </div>
      </motion.article>

      {alertOpen && <PriceAlertModal item={item} onClose={handleCloseAlert} />}
    </>
  )
}

export default memo(ItemCard)
