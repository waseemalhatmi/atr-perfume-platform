import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams, Link } from 'react-router-dom'
import { Search as SearchIcon, ChevronLeft, Filter, Sparkles, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { searchItems } from '@/lib/api'
import ItemCard from '@/components/ItemCard'
import SkeletonCard from '@/components/SkeletonCard'
import SEO from '@/components/SEO'
import { useAnalytics } from '@/hooks/useAnalytics'
import { useProfileData } from '@/hooks/useProfileData'
import { useMemo } from 'react'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialQuery = searchParams.get('q') || ''
  const [searchTerm, setSearchTerm] = useState(initialQuery)
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const { track } = useAnalytics()

  useEffect(() => {
    try {
      const stored = localStorage.getItem('recentSearches')
      if (stored) setRecentSearches(JSON.parse(stored))
    } catch {}
  }, [])

  // Debounce the URL update
  useEffect(() => {
    const timer = setTimeout(() => {
      const next = new URLSearchParams(searchParams)
      if (searchTerm.trim()) {
        next.set('q', searchTerm.trim())
      } else {
        next.delete('q')
      }
      setSearchParams(next, { replace: true })
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm, searchParams, setSearchParams])

  const query = searchParams.get('q') || ''
  const isValidQuery = query.trim().length > 0

  useEffect(() => {
    if (isValidQuery) {
      track('search_executed', { query })
      setRecentSearches(prev => {
        const updated = [query, ...prev.filter(q => q !== query)].slice(0, 5)
        localStorage.setItem('recentSearches', JSON.stringify(updated))
        return updated
      })
    }
  }, [query, isValidQuery, track])

  const { data, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn:  () => searchItems(query),
    enabled:  isValidQuery,
  })

  const { savedSet, alertSet, isLoading: profileLoading } = useProfileData()
  const isGlobalLoading = isLoading || profileLoading

  return (
    <div className="container-px py-12 md:py-20 min-h-screen">
      <SEO 
        title={query ? `نتائج البحث عن ${query} | منصة عطري` : 'البحث | منصة عطري'} 
        description="ابحث في أكبر مكتبة للعطور العالمية والنيش." 
      />
      {/* Header */}
      <div className="text-center mb-16 relative">
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-48 h-48 bg-primary/5 blur-[80px] rounded-full -z-10" />
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Sparkles className="mx-auto mb-4 text-primary" size={32} />
          <h1 className="text-4xl md:text-6xl font-bold mb-8">
            {isValidQuery ? (
              <><span className="text-muted-foreground">نتائج البحث عن:</span> <span className="luxury-text italic">"{query}"</span></>
            ) : (
              <>اكتشف <span className="luxury-text">عطرك التالي</span></>
            )}
          </h1>
          
          <div className="relative max-w-2xl mx-auto mb-8">
            <input 
              type="text" 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="ابحث عن ماركة، عطر، أو نوتة..."
              className="w-full glass border-2 border-border/50 py-4 pr-14 pl-6 rounded-full outline-none focus:border-primary transition-all text-lg font-bold"
            />
            <SearchIcon className="absolute right-5 top-1/2 -translate-y-1/2 text-muted-foreground" size={24} />
            {isLoading && <Loader2 className="absolute left-5 top-1/2 -translate-y-1/2 text-primary animate-spin" size={24} />}
          </div>

          <p className="text-muted-foreground max-w-xl mx-auto">
            نحن نبحث في مئات الماركات والمتاجر الموثوقة لنجد لك أفضل العروض.
          </p>
        </motion.div>
      </div>

      {/* Results Info Bar */}
      {!isLoading && (
        <div className="flex items-center justify-between mb-10 glass p-4 px-8 rounded-3xl">
          <div className="flex items-center gap-3 text-sm font-bold">
            <Filter size={18} className="text-primary" />
            <span>عثرنا على <span className="text-primary">{data?.results?.length || 0}</span> نتيجة</span>
          </div>
          <Link to="/items" className="text-xs font-bold hover:text-primary transition-colors flex items-center gap-1">
            مشاهدة جميع العطور <ChevronLeft size={14} />
          </Link>
        </div>
      )}

      {/* Results Grid */}
      {!isValidQuery ? (
        <motion.div 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="text-center py-16 md:py-24 glass rounded-[3rem] border-dashed border-2"
        >
          <div className="w-24 h-24 bg-secondary rounded-full flex items-center justify-center mx-auto mb-8">
            <SearchIcon size={48} className="text-primary/40" />
          </div>
          <h3 className="text-2xl font-bold mb-4">ابدأ بالبحث...</h3>
          <p className="text-muted-foreground mb-12 max-w-md mx-auto">
            استخدم صندوق البحث أعلاه للعثور على عطورك المفضلة أو الماركات التي تحبها.
          </p>

          {recentSearches.length > 0 && (
            <div className="max-w-md mx-auto mb-8 text-center">
              <h4 className="text-sm font-bold text-muted-foreground mb-4">عمليات البحث الأخيرة</h4>
              <div className="flex flex-wrap justify-center gap-2">
                {recentSearches.map((s, i) => (
                  <button 
                    key={i} 
                    onClick={() => setSearchTerm(s)}
                    className="px-5 py-2 glass rounded-full text-sm font-bold hover:bg-primary hover:text-black transition-all shadow-sm"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="max-w-md mx-auto">
            <h4 className="text-sm font-bold text-muted-foreground mb-4">اقتراحات شائعة</h4>
            <div className="flex flex-wrap justify-center gap-2">
              {['شانيل', 'توم فورد', 'عطر صيفي', 'عود', 'ديور'].map((s, i) => (
                <button 
                  key={i} 
                  onClick={() => setSearchTerm(s)}
                  className="px-5 py-2 bg-secondary/30 rounded-full text-sm font-bold hover:bg-primary/20 text-primary transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      ) : isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : (data?.results && data.results.length > 0) ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-8">
          {data.results.map((item: any, i: number) => (
            <ItemCard 
              key={item.id} 
              item={item} 
              index={i} 
              isSaved={savedSet.has(item.id)}
              hasAlert={alertSet.has(item.id)}
            />
          ))}
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="text-center py-32 glass rounded-[3rem] border-dashed border-2"
        >
          <div className="w-24 h-24 bg-secondary rounded-full flex items-center justify-center mx-auto mb-8">
            <SearchIcon size={48} className="text-muted-foreground/20" />
          </div>
          <h3 className="text-2xl font-bold mb-4">لم نجد أي نتائج لـ "{query}"</h3>
          <p className="text-muted-foreground mb-8 max-w-md mx-auto">
            جرّب البحث عن اسم الماركة، أو اسم العطر بشكل مختلف، أو تصفح مجموعاتنا المختارة.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/items" className="btn-gold px-12">تصفح المتجر</Link>
            <Link to="/" className="glass px-12 py-4 rounded-full font-bold">العودة للرئيسية</Link>
          </div>
        </motion.div>
      )}

      {/* Quick Tips */}
      <div className="mt-32 grid md:grid-cols-3 gap-8">
        {[
          { title: "ابحث بالماركة", desc: "اكتب 'شانيل' أو 'ديور' لعرض جميع عطور الماركة." },
          { title: "ابحث بالمكونات", desc: "اكتب 'عود' أو 'فانيلا' لاكتشاف عطورك المفضلة." },
          { title: "ابحث بالسعر", desc: "استخدم الفلاتر في صفحة المتجر لتحديد ميزانيتك." },
        ].map((tip, i) => (
          <div key={i} className="glass p-8 rounded-3xl border-primary/5 hover:border-primary/20 transition-all">
            <h4 className="font-bold mb-3 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px]">{i+1}</span>
              {tip.title}
            </h4>
            <p className="text-sm text-muted-foreground leading-relaxed">{tip.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
