import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Heart, Trees, ExternalLink, ChevronLeft, ShieldCheck, Zap, Bell, Award, Star } from 'lucide-react'
import { fetchItem, imageUrl, recordClick } from '@/lib/api'
import { calculateRating } from '@/lib/rating'
import { useItemSave } from '@/hooks/useItemSave'
import { useProfileData } from '@/hooks/useProfileData'
import ItemCard from '@/components/ItemCard'
import { useState } from 'react'
import PriceAlertModal from '@/components/PriceAlertModal'
import PriceHistoryChart from '@/components/PriceHistoryChart'

export default function ItemDetailPage() {
  const { id } = useParams<{ id: string }>()
  const itemId  = Number(id)
  const [alertOpen, setAlertOpen] = useState(false)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['item', itemId],
    queryFn:  () => fetchItem(itemId),
    enabled:  !!itemId,
  })

  const { savedSet, alertSet, isLoading: profileLoading } = useProfileData()
  
  const { isSaved, isSaving, handleSave } = useItemSave({
    itemId,
    initialSaved: savedSet.has(itemId),
  })

  if (isLoading) {
    return (
      <div className="container-px py-24 flex flex-col gap-12">
        <div className="grid lg:grid-cols-2 gap-16">
          <div className="skeleton aspect-square rounded-[3rem]" />
          <div className="space-y-6">
            <div className="skeleton h-4 w-24" />
            <div className="skeleton h-12 w-3/4" />
            <div className="skeleton h-32 w-full" />
            <div className="skeleton h-12 w-48" />
          </div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="container-px py-32 text-center">
        <div className="luxury-text text-8xl mb-8">⚠️</div>
        <h2 className="text-2xl font-bold mb-4">حدث خطأ في الاتصال</h2>
        <p className="text-muted-foreground mb-8">
          الخادم يقوم بمعالجة بيانات العطر الذكية (AI)، يرجى إعادة المحاولة.
        </p>
        <button onClick={() => window.location.reload()} className="btn-gold inline-flex items-center gap-2">
          إعادة المحاولة
        </button>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="container-px py-32 text-center">
        <div className="luxury-text text-8xl mb-8">404</div>
        <h2 className="text-2xl font-bold mb-4">العطر غير موجود</h2>
        <Link to="/items" className="btn-gold inline-flex items-center gap-2">
          <ChevronLeft size={18} /> العودة للمتجر
        </Link>
      </div>
    )
  }

  const { item, clones, recommended, similar } = data
  const thumb = item.images[0] ? imageUrl(item.images[0].path) : '/placeholder.jpg'

  const handleBuy = async (linkId: number, fallbackUrl: string) => {
    try {
      const res = await recordClick(linkId)
      window.open(res.redirect_url || fallbackUrl, '_blank', 'noopener,noreferrer')
    } catch {
      window.open(fallbackUrl, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className="pb-24">
      {/* Breadcrumb */}
      <div className="container-px py-6">
        <nav className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
          <Link to="/" className="hover:text-primary transition-colors">الرئيسية</Link>
          <ChevronLeft size={12} />
          <Link to="/items" className="hover:text-primary transition-colors">العطور</Link>
          <ChevronLeft size={12} />
          <span className="text-primary truncate">{item.name}</span>
        </nav>
      </div>

      {/* Main Product Section */}
      <section className="container-px grid lg:grid-cols-2 gap-16 items-start">
        
        {/* Gallery Area */}
        <motion.div 
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          className="relative group"
        >
          <div className="relative aspect-square rounded-[3rem] overflow-hidden glass border-2 border-primary/10 p-4">
            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
            <img 
              src={thumb} 
              alt={item.name} 
              className="w-full h-full object-contain mix-blend-multiply dark:mix-blend-normal transition-transform duration-700 group-hover:scale-110"
            />
          </div>
          {/* Floating Badges */}
          <div className="absolute -bottom-6 -right-6 glass p-6 rounded-3xl shadow-2xl animate-float">
            <Award className="text-primary mb-2" size={32} />
            <p className="text-xs font-black uppercase tracking-tighter">أصلي 100%</p>
          </div>
        </motion.div>

        {/* Info Area */}
        <div className="flex flex-col gap-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="flex items-center gap-4 mb-4">
              <span className="badge--luxury">{item.brand.name}</span>
              <span className="text-xs font-bold text-muted-foreground flex items-center gap-1">
                <ShieldCheck size={14} className="text-primary" /> موثوق
              </span>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold mb-4 leading-tight">
              {item.name}
            </h1>
            <div className="flex items-center gap-6">
              <div className="item-price-range text-4xl">
                {item.min_price > 0 ? `${item.min_price.toFixed(0)} ${item.currency}` : 'متوفر للطلب'}
              </div>
              <div className="h-10 w-px bg-border" />
              <div className="flex items-center gap-1 text-primary">
                <Star size={18} className="fill-current" />
                <span className="text-lg font-bold">{calculateRating(item)}</span>
              </div>
            </div>
          </motion.div>

          <p className="text-muted-foreground text-lg leading-relaxed italic">
            "{item.description || 'وصف فاخر لهذا العطر يعبر عن شخصيتك الفريدة وحضورك الطاغي في كل المناسبات.'}"
          </p>

          {/* Quick Specs Grid */}
          <div className="grid grid-cols-2 gap-4">
            {item.quick_details?.map((detail, i) => (
              <div key={i} className="glass p-4 rounded-2xl border-primary/5">
                <p className="text-[10px] text-muted-foreground uppercase font-bold mb-1">{detail.key}</p>
                <p className="text-sm font-bold">{detail.value}</p>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-4 mt-4">
            <button
              onClick={() => setAlertOpen(true)}
              aria-label="تنبيه انخفاض السعر"
              className="flex-1 glass p-4 rounded-full font-bold flex items-center justify-center gap-2 hover:border-primary/50 transition-all"
            >
              <Bell size={18} className="text-primary" />
              تنبيه انخفاض السعر
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              aria-label={isSaved ? 'إزالة من المفضلة' : 'أضف للمفضلة'}
              className="flex-1 btn-gold flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Heart size={18} className={isSaved ? 'fill-current' : ''} />
              {isSaving ? 'جاري الحفظ...' : isSaved ? 'في المفضلة ✓' : 'أضف للمفضلة'}
            </button>
          </div>
        </div>
      </section>

      {/* Price History Section */}
      <section className="container-px py-12">
        <PriceHistoryChart itemId={item.id} currency={item.currency} />
      </section>

      {/* Fragrance Pyramid Section */}
      {item.perfume_notes && (
        <section className="container-px py-24">
          <div className="glass rounded-[3rem] p-12 md:p-20 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[100px]" />
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-5xl font-bold mb-4">الهرم <span className="luxury-text italic">العطري</span></h2>
              <p className="text-muted-foreground">رحلة الحواس من الإفتتاحية حتى القاعدة.</p>
            </div>

            <div className="grid md:grid-cols-3 gap-12 text-center relative z-10">
              {[
                { label: 'الإفتتاحية', val: item.perfume_notes.top, icon: <Zap size={32} /> },
                { label: 'القلب', val: item.perfume_notes.heart, icon: <Heart size={32} /> },
                { label: 'القاعدة', val: item.perfume_notes.base, icon: <Trees size={32} /> }
              ].map((note, i) => (
                <div key={i} className="flex flex-col items-center gap-6 group">
                  <div className="w-20 h-20 rounded-full glass border-primary/20 flex items-center justify-center text-primary group-hover:scale-110 transition-transform duration-500">
                    {note.icon}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-[0.2em] mb-3 text-primary">{note.label}</h3>
                    <p className="text-lg leading-relaxed">{note.val || 'مكونات سرية فاخرة'}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Comparison Table / Store Links */}
      <section className="container-px py-12">
        <h2 className="text-3xl font-bold mb-10 flex items-center gap-4">
          <Award className="text-primary" />
          أفضل العروض المتاحة
        </h2>
        <div className="flex flex-col gap-4">
          {item.variants?.[0]?.store_links.map((link) => (
            <div key={link.id} className="glass p-6 rounded-3xl flex flex-col md:flex-row items-center justify-between gap-6 hover:border-primary/40 transition-all group">
              <div className="flex items-center gap-6 w-full md:w-auto">
                <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center font-black text-xl">
                  {link.store.name.charAt(0)}
                </div>
                <div>
                  <h4 className="font-bold text-lg">{link.store.name}</h4>
                  <p className="text-xs text-green-500 font-bold flex items-center gap-1">
                    <ShieldCheck size={12} /> متوفر في المخزون
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-8 w-full md:w-auto justify-between md:justify-end">
                <div className="text-right">
                  {link.old_price && (
                    <p className="text-xs text-muted-foreground line-through">{link.old_price} {link.currency}</p>
                  )}
                  <p className="text-2xl font-bold luxury-text">{link.price} {link.currency}</p>
                </div>
                <button 
                  onClick={() => handleBuy(link.id, link.affiliate_url)}
                  className="btn-gold !py-3 !px-8 flex items-center gap-2 group"
                >
                  تسوق الآن
                  <ExternalLink size={16} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Clones Section */}
      {clones && clones.length > 0 && (
        <section className="container-px py-24">
          <div className="flex items-center justify-between mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">بدائل <span className="luxury-text">ذكية</span></h2>
            <Link to="/items" className="text-sm font-bold text-primary flex items-center gap-1 group">
              عرض المزيد <ChevronLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-8">
            {clones.map((clone, i) => (
              <ItemCard 
                key={clone.id} 
                item={clone} 
                index={i} 
                isSaved={savedSet.has(clone.id)}
                hasAlert={alertSet.has(clone.id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Similar Profiles Section */}
      {similar && similar.length > 0 && (
        <section className="container-px py-24 bg-primary/5 rounded-[4rem] my-12">
          <div className="flex flex-col md:flex-row items-center justify-between mb-12 px-6 gap-6">
            <div className="text-center md:text-right">
              <h2 className="text-3xl md:text-4xl font-bold mb-2">نفس <span className="luxury-text">التجربة العطرية</span></h2>
              <p className="text-muted-foreground text-sm">عطور تشترك في نفس المكونات العطرية بدقة عالية.</p>
            </div>
            <Link to="/items" className="text-sm font-bold text-primary flex items-center gap-1 group">
              استكشف الكل <ChevronLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-8 px-6">
            {similar.map((s, i) => (
              <ItemCard 
                key={s.id} 
                item={s} 
                index={i} 
                isSaved={savedSet.has(s.id)}
                hasAlert={alertSet.has(s.id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Recommended Section */}
      {recommended && recommended.length > 0 && (
        <section className="container-px py-24 border-t border-primary/5">
          <div className="flex items-center justify-between mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">عطور <span className="luxury-text">قد تعجبك</span></h2>
            <Link to="/items" className="text-sm font-bold text-primary flex items-center gap-1 group">
              اكتشف المزيد <ChevronLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-8">
            {recommended.map((rec, i) => (
              <ItemCard 
                key={rec.id} 
                item={rec} 
                index={i} 
                isSaved={savedSet.has(rec.id)}
                hasAlert={alertSet.has(rec.id)}
              />
            ))}
          </div>
        </section>
      )}

      {alertOpen && <PriceAlertModal item={item} onClose={() => setAlertOpen(false)} />}
    </div>
  )
}
