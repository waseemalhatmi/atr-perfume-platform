import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Bell } from 'lucide-react'
import toast from 'react-hot-toast'
import type { Item } from '@/lib/api'
import { subscribePriceAlert } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

interface Props {
  item: Item
  onClose: () => void
}

export default function PriceAlertModal({ item, onClose }: Props) {
  const { user } = useAuthStore()
  const [email, setEmail]         = useState(user?.email ?? '')
  const [target, setTarget]       = useState('')
  const [loading, setLoading]     = useState(false)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const price = parseFloat(target)
    // If not logged in, email is required
    if ((!user && !email) || isNaN(price) || price <= 0) {
      toast.error('يرجى إدخال السعر المستهدف بشكل صحيح، والبريد الإلكتروني إن لم تكن مسجل الدخول.')
      return
    }
    setLoading(true)
    try {
      const res = await subscribePriceAlert(item.id, email, price)
      if (res.success) {
        toast.success(res.message || 'تم تسجيل التنبيه!')
        onClose()
      } else {
        toast.error(res.error || 'حدث خطأ.')
      }
    } catch {
      toast.error('حدث خطأ في الاتصال.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-[300] flex items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
        <motion.div
          className="relative glass-card p-8 w-full max-w-md shadow-2xl"
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="price-alert-title"
        >
          <button type="button" onClick={onClose} aria-label="إغلاق التنبيه"
            className="absolute top-4 left-4 text-muted-foreground hover:text-foreground transition-colors">
            <X size={20} />
          </button>

          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full flex items-center justify-center"
              style={{ background: 'rgba(212,175,55,0.15)' }}>
              <Bell size={18} style={{ color: 'var(--gold-primary)' }} />
            </div>
            <div>
              <h3 id="price-alert-title" className="font-bold text-lg">تنبيه السعر</h3>
              <p className="text-sm text-muted-foreground">{item.name}</p>
            </div>
          </div>

          <p className="text-sm text-muted-foreground mb-6">
            السعر الحالي: <span className="luxury-text font-bold">
              {item.min_price > 0 ? `${item.min_price.toFixed(2)} ${item.currency}` : 'غير محدد'}
            </span>
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Only show email input if user is NOT logged in */}
            {!user && (
              <div>
                <label className="block text-sm font-medium mb-1">البريد الإلكتروني</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="your@email.com"
                  className="w-full px-4 py-3 rounded-lg text-sm outline-none focus:ring-2 focus:ring-gold-primary/40"
                  style={{ background: 'var(--secondary)', border: '1px solid var(--border)', color: 'var(--foreground)' }}
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium mb-1">السعر المستهدف (SAR)</label>
              <input
                type="number"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                required
                min="1"
                step="0.01"
                placeholder="مثال: 120.00"
                className="w-full px-4 py-3 rounded-lg text-sm outline-none focus:ring-2 focus:ring-gold-primary/40"
                style={{ background: 'var(--secondary)', border: '1px solid var(--border)', color: 'var(--foreground)' }}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-gold w-full py-4 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? 'جاري الحفظ...' : 'سجّل التنبيه'}
            </button>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
