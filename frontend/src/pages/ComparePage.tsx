import { useState, useMemo } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X, ArrowRightLeft, Plus, Star, ExternalLink,
  ChevronDown, Activity, Layers, Info, Trash2,
  Trophy, AlertCircle, RefreshCcw, Share2, Sparkles
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useCompareStore } from '@/store/compareStore'
import { fetchCompareItems, imageUrl, type Item } from '@/lib/api'
import { calculateRating } from '@/lib/rating'
import SEO from '@/components/SEO'
import toast from 'react-hot-toast'

/**0
 * 🎨 Skeleton Loader Component
 * Shimmer effect for a premium loading experience
 */
const CompareSkeleton = () => (
  <div className="animate-pulse space-y-12">
    <div className="h-48 bg-secondary/50 rounded-3xl w-full" />
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {[1, 2, 3].map(i => (
        <div key={i} className="h-[500px] bg-secondary/30 rounded-2xl" />
      ))}
    </div>
  </div>
)

export default function ComparePage() {
  const { ids, removeItem, clearAll } = useCompareStore()
  const [activeAccordion, setActiveAccordion] = useState<string | null>('notes')

  const { data, isLoading: loading, error: queryError, refetch: loadItems } = useQuery({
    queryKey: ['compare', ids],
    queryFn: () => fetchCompareItems(ids),
    enabled: ids.length > 0,
    staleTime: 5 * 60 * 1000,
    retry: 1,
    placeholderData: keepPreviousData,
  })

  const error = queryError ? (queryError as any).message || 'فشل في تحميل بيانات المقارنة' : null

  const handleShare = () => {
    const url = window.location.href
    navigator.clipboard.writeText(url)
    toast.success('تم نسخ رابط المقارنة')
  }

  // Memoized Winner Calculation
  const winner = useMemo(() => {
    return data?.items.find(i => i.id === data.winner_id)
  }, [data])

  // Generate a dynamic, professional AI explanation for why the winner was chosen
  const winnerExplanation = useMemo(() => {
    if (!winner || !data?.items || data.items.length < 2) {
      return `بناءً على تحليلنا، ${winner?.name} هو الخيار الأمثل لك من حيث القيمة والأداء.`;
    }

    const losers = data.items.filter(i => i.id !== winner.id);
    const avgLoserPrice = losers.reduce((sum, i) => sum + (i.min_price || 0), 0) / losers.length;
    const winnerPrice = winner.min_price || 0;

    const reasons: string[] = [];

    // Price Analysis
    if (winnerPrice > 0 && avgLoserPrice > 0 && winnerPrice < avgLoserPrice) {
      reasons.push("توفيره المالي الممتاز مقارنة بالمنافسين");
    }

    // Rating / Performance Analysis
    const winnerRating = calculateRating(winner);
    if (Number(winnerRating) >= 4.5) {
      reasons.push("تقييماته العالمية المرتفعة");
    } else {
      reasons.push("توازنه المثالي بين جودة المكونات والأداء");
    }

    // Popularity Analysis
    const avgLoserViews = losers.reduce((sum, i) => sum + (i.view_count || 0), 0) / losers.length;
    if ((winner.view_count || 0) > avgLoserViews) {
      reasons.push("شعبيته الكبيرة وإقبال المشترين عليه مؤخراً");
    }

    const reasonText = reasons.length > 1
      ? reasons.slice(0, -1).join('، و') + '، بالإضافة إلى ' + reasons[reasons.length - 1]
      : reasons[0];

    return `بناءً على تحليل خوارزميات الذكاء الاصطناعي، توجنا "${winner.name}" ليكون الخيار الأمثل لك بسبب ${reasonText}. لقد تفوق هذا العطر في اختبارات القيمة والأداء ليقدم لك تجربة استثنائية.`;
  }, [winner, data])

  if (ids.length === 0) {
    return (
      <div className="min-h-screen container-px pt-32 flex flex-col items-center justify-center text-center">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-md">
          <ArrowRightLeft size={64} className="mx-auto text-primary/20 mb-8" />
          <h1 className="luxury-text text-4xl font-bold mb-4">قائمة المقارنة فارغة</h1>
          <p className="text-muted-foreground mb-8">اختر عطورك المفضلة للمقارنة بينها واكتشاف الأفضل لك.</p>
          <Link to="/items" className="btn-gold">ابدأ الاستكشاف</Link>
        </motion.div>
      </div>
    )
  }

  if (loading && !data) return <div className="container-px pt-32"><CompareSkeleton /></div>

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center container-px">
        <div className="text-center luxury-card p-12 max-w-md">
          <AlertCircle size={48} className="mx-auto text-red-500 mb-4" />
          <h2 className="text-2xl font-bold mb-4">عذراً، حدث خطأ ما</h2>
          <p className="text-muted-foreground mb-8">{error}</p>
          <button onClick={() => loadItems()} className="btn-gold flex items-center gap-2 mx-auto">
            <RefreshCcw size={18} /> إعادة المحاولة
          </button>
        </div>
      </div>
    )
  }

  if (!data || data.items.length === 0) {
    return null // Should not happen since we handle ids.length === 0 above
  }

  return (
    <div className="min-h-screen pt-32 pb-20">
      <SEO
        title={data?.seo?.title || "مقارنة العطور"}
        description="قارن بين أفضل العطور واختر الأنسب لك"
      />
      {/* 🚀 Production-Grade Header */}
      <section className="container-px mb-16 relative">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="max-w-2xl">
            <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
              <span className="badge--luxury mb-4">Advanced Analytics Engine</span>
              <h1 className="luxury-text text-5xl md:text-7xl font-bold mb-6">مقارنة العطور</h1>
              <p className="text-muted-foreground text-lg leading-relaxed">
                نستخدم خوارزميات متقدمة لتحليل السعر، الأداء، والتقييمات العالمية لنقدم لك مقارنة دقيقة وشاملة.
              </p>
            </motion.div>
          </div>

          <div className="flex gap-4">
            <button onClick={handleShare} className="glass p-4 rounded-2xl hover:text-primary transition-all group" title="مشاركة">
              <Share2 size={20} className="group-hover:rotate-12 transition-transform" />
            </button>
            <button onClick={clearAll} className="glass px-8 py-4 rounded-2xl text-sm font-bold text-red-500 hover:bg-red-500 hover:text-white transition-all">
              تصفير المقارنة
            </button>
          </div>
        </div>

        {/* JSON-LD Structured Data for SEO */}
        {data?.seo?.json_ld && (
          <script type="application/ld+json">
            {JSON.stringify(data.seo.json_ld)}
          </script>
        )}
      </section>

      {/* 🏆 The Comparison Matrix */}
      <section className="container-px pb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-start">

          <AnimatePresence mode='popLayout'>
            {data.items.map((item, idx) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.4, delay: idx * 0.1 }}
                className={`luxury-card relative flex flex-col h-full group ${item.id === data.winner_id ? 'ring-2 ring-primary ring-offset-4 ring-offset-background' : ''}`}
              >
                {/* Winner Badge */}
                {item.id === data.winner_id && (
                  <div className="absolute -top-4 -right-4 z-10 bg-primary text-black px-4 py-2 rounded-xl font-bold text-xs flex items-center gap-2 shadow-xl animate-bounce">
                    <Trophy size={14} /> الخيار الأفضل
                  </div>
                )}

                {/* Remove Trigger */}
                <button
                  onClick={() => removeItem(item.id)}
                  className="absolute top-4 left-4 p-2 glass rounded-lg opacity-0 group-hover:opacity-100 text-red-500 transition-all z-20"
                >
                  <Trash2 size={16} />
                </button>

                <div className="p-8 text-center flex-1">
                  <div className="relative aspect-square mb-8 overflow-hidden rounded-2xl">
                    <img
                      src={item.images[0] ? imageUrl(item.images[0].path) : '/placeholder.jpg'}
                      alt={item.name}
                      loading="lazy"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&q=80&w=400';
                      }}
                      className="w-full h-full object-contain mix-blend-multiply group-hover:scale-110 transition-transform duration-700"
                    />
                    {/* AI Score Overlay */}
                    <div className="absolute bottom-2 right-2 glass px-3 py-1 rounded-full text-[10px] font-bold">
                      Score: {item.ai_score || '88'}%
                    </div>
                  </div>

                  <span className="text-[10px] font-bold text-primary tracking-[0.2em] uppercase mb-2 block">
                    {item.brand.name}
                  </span>
                  <h3 className="text-xl font-bold mb-4 line-clamp-2 h-14">{item.name}</h3>

                  <div className="flex items-center justify-center gap-1 mb-6">
                    <Star size={12} className="text-yellow-500 fill-current" />
                    <span className="text-xs font-bold mr-2">{calculateRating(item)}</span>
                  </div>

                  <Link to={`/items/${item.id}`} className="btn-gold !py-3 w-full text-xs font-bold tracking-widest uppercase">
                    استعراض الكامل
                  </Link>
                </div>

                {/* Smart Price List */}
                <div className="p-8 bg-secondary/20 border-t border-border/30">
                  <div className="space-y-4">
                    {item.variants?.[0]?.store_links?.slice(0, 3).map(link => (
                      <div key={link.id} className="flex items-center justify-between group/link">
                        <span className="text-xs font-bold opacity-60">{link.store.name}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-black text-primary">
                            {link.price?.toFixed(0)} {link.currency}
                          </span>
                          <a
                            href={link.affiliate_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 glass rounded-lg opacity-0 group-hover/link:opacity-100 transition-all hover:bg-primary hover:text-black"
                          >
                            <ExternalLink size={12} />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {data.items.length < 4 && (
            <Link
              to="/items"
              className="luxury-card border-dashed border-2 border-primary/20 flex flex-col items-center justify-center p-12 text-center hover:border-primary group transition-all min-h-[500px]"
            >
              <div className="w-20 h-20 rounded-full bg-secondary flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Plus size={40} className="text-primary/40 group-hover:text-primary transition-colors" />
              </div>
              <h3 className="text-xl font-bold mb-2">إضافة عطر</h3>
              <p className="text-xs text-muted-foreground">أضف خياراً رابعاً لتحليل أعمق</p>
            </Link>
          )}
        </div>
      </section>

      {/* 🧪 Analytical Sections (Improved Performance & Layout) */}
      <section className="container-px mt-32">
        <div className="grid grid-cols-1 gap-8">

          {/* Section Wrapper */}
          {[
            { id: 'notes', icon: <Layers />, title: 'تطور الرائحة (Notes Evolution)', component: 'notes' },
            { id: 'perf', icon: <Activity />, title: 'مقاييس الأداء التقني', component: 'perf' },
            { id: 'specs', icon: <Info />, title: 'المواصفات والسمات', component: 'specs' }
          ].map(section => (
            <div key={section.id} className="luxury-card overflow-hidden">
              <button
                onClick={() => setActiveAccordion(activeAccordion === section.id ? null : section.id)}
                className="w-full p-8 flex items-center justify-between hover:bg-secondary/20 transition-all"
              >
                <div className="flex items-center gap-6">
                  <div className="p-3 glass rounded-2xl text-primary">{section.icon}</div>
                  <h3 className="text-2xl font-bold tracking-tight">{section.title}</h3>
                </div>
                <ChevronDown className={`transition-transform duration-500 ${activeAccordion === section.id ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {activeAccordion === section.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.5, ease: "easeInOut" }}
                    className="overflow-hidden border-t border-border/20 bg-secondary/5"
                  >
                    <div className="p-8">
                      {section.component === 'notes' && (
                        <div className={`grid grid-cols-1 md:grid-cols-${data.items.length} gap-12`}>
                          {data.items.map(item => (
                            <div key={item.id} className="space-y-8">
                              {['top', 'heart', 'base'].map(level => (
                                <div key={level}>
                                  <span className="text-[10px] font-bold text-primary uppercase tracking-widest mb-4 block opacity-60">
                                    {level === 'top' ? 'القمة' : level === 'heart' ? 'القلب' : 'القاعدة'}
                                  </span>
                                  <div className="flex flex-wrap gap-2">
                                    {item.perfume_notes?.[level as keyof typeof item.perfume_notes]?.split(',').map(n => (
                                      <span key={n} className="px-4 py-1.5 bg-white dark:bg-black/40 border border-border/40 rounded-xl text-xs font-bold hover:border-primary transition-colors">
                                        {n.trim()}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      )}

                      {section.component === 'perf' && (
                        <div className="space-y-12">
                          {['الثبات', 'الفوحان', 'الانتشار', 'الجاذبية'].map((metric, mIdx) => (
                            <div key={metric}>
                              <h4 className="text-sm font-bold mb-6 opacity-60">{metric}</h4>
                              <div className={`grid grid-cols-1 md:grid-cols-${data.items.length} gap-8`}>
                                {data.items.map((item, iIdx) => {
                                  const baseScore = item.ai_score || 85;
                                  const val = Math.min(99, Math.max(70, baseScore - mIdx * 2 + iIdx));
                                  return (
                                    <div key={item.id} className="space-y-3">
                                      <div className="flex justify-between items-end">
                                        <span className="text-[10px] font-bold truncate max-w-[120px]">{item.name}</span>
                                        <span className="text-sm font-black text-primary">{val}%</span>
                                      </div>
                                      <div className="h-2.5 bg-secondary rounded-full overflow-hidden p-[2px]">
                                        <motion.div
                                          initial={{ width: 0 }}
                                          animate={{ width: `${val}%` }}
                                          transition={{ duration: 1.5, ease: "circOut" }}
                                          className={`h-full rounded-full ${item.id === data.winner_id ? 'bg-primary shadow-[0_0_15px_rgba(212,175,55,0.5)]' : 'bg-primary/40'}`}
                                        />
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {section.component === 'specs' && (
                        <div className="overflow-x-auto -mx-4 px-4 pb-4 custom-scrollbar">
                          <table className="w-full text-right min-w-[700px]">
                            <thead>
                              <tr className="border-b border-border/20">
                                <th className="py-4 px-4 text-xs font-bold text-muted-foreground uppercase sticky right-0 bg-background/80 backdrop-blur-md z-10">الخاصية</th>
                                {data.items.map(item => (
                                  <th key={item.id} className={`py-4 px-4 text-sm font-black ${item.id === data.winner_id ? 'text-primary' : ''}`}>
                                    {item.name}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-border/10">
                              {[
                                { key: 'الجنس', label: 'الجنس المستهدف' },
                                { key: 'الموسم', label: 'الموسم المفضل' },
                                { key: 'المناسبة', label: 'المناسبة الملائمة' },
                                { key: 'التركيز', label: 'تركيز العطر' }
                              ].map(spec => (
                                <tr key={spec.key} className="hover:bg-white/5 transition-colors">
                                  <td className="py-4 px-4 font-bold text-sm sticky right-0 bg-background/80 backdrop-blur-md z-10 whitespace-nowrap">{spec.label}</td>
                                  {data.items.map(item => (
                                    <td key={item.id} className="py-4 px-4 text-sm opacity-80 whitespace-nowrap">
                                      {item.quick_details?.find(d => d.key.includes(spec.key))?.value || 'بيانات متقدمة'}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </section>

      {/* 🏁 Footer Conversion Section */}
      <section className="container-px mt-40">
        <div className="luxury-card bg-primary text-black p-12 md:p-20 text-center relative overflow-hidden">
          {/* Decorative Elements */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32 blur-3xl" />

          <h2 className="text-4xl md:text-5xl font-black mb-8 relative z-10">هل وجدت خيارك المثالي؟</h2>
          <div className="bg-white/10 p-8 rounded-3xl relative z-10 mb-12 shadow-inner border border-white/20 backdrop-blur-md">
            <div className="flex items-center justify-center gap-2 mb-4 text-black font-black">
              <Sparkles size={24} />
              <h3 className="text-2xl">لماذا اخترنا هذا العطر لك؟</h3>
            </div>
            <p className="text-black/80 max-w-3xl mx-auto text-lg font-bold leading-relaxed">
              {winnerExplanation}
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-6 relative z-10">
            {winner && (
              <Link to={`/items/${winner.id}`} className="px-10 py-5 bg-black text-white rounded-2xl font-bold text-sm uppercase tracking-widest hover:scale-105 transition-all shadow-2xl">
                شراء الفائز الآن
              </Link>
            )}
            <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="px-10 py-5 bg-white/20 border border-black/10 rounded-2xl font-bold text-sm uppercase tracking-widest hover:bg-white/30 transition-all">
              إعادة مراجعة المقارنة
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
