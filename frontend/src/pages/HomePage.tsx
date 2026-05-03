import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ChevronLeft, Sparkles, Award, Zap, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { fetchItems, subscribeNewsletter } from '@/lib/api'
import ItemCard from '@/components/ItemCard'
import SkeletonCard from '@/components/SkeletonCard'
import SEO from '@/components/SEO'
import { useAnalytics } from '@/hooks/useAnalytics'
import { useProfileData } from '@/hooks/useProfileData'
import toast from 'react-hot-toast'

export default function HomePage() {
  const { data, isLoading: itemsLoading } = useQuery({
    queryKey: ['items', 'home'],
    queryFn:  () => fetchItems({ per_page: 8, sort: 'newest' }),
  })

  const { savedSet, alertSet, isLoading: profileLoading } = useProfileData()
  const isLoading = itemsLoading || profileLoading

  const [email, setEmail] = useState('')
  const [isSubscribing, setIsSubscribing] = useState(false)
  const { track } = useAnalytics()

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmedEmail = email.trim()
    
    if (!trimmedEmail) {
      toast.error('يرجى إدخال بريدك الإلكتروني')
      return
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(trimmedEmail)) {
      toast.error('صيغة البريد الإلكتروني غير صحيحة')
      return
    }

    if (isSubscribing) return

    setIsSubscribing(true)
    try {
      await subscribeNewsletter(trimmedEmail)
      track('newsletter_subscribed', { email: trimmedEmail })
      toast.success('تم اشتراكك بنجاح! شكراً لك.', { icon: '🎉' })
      setEmail('')
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'حدث خطأ أثناء الاشتراك. يرجى المحاولة لاحقاً.')
    } finally {
      setIsSubscribing(false)
    }
  }

  const fadeInUp = {
    initial: { opacity: 0, y: 30 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true },
    transition: { duration: 0.8 }
  }

  return (
    <div className="overflow-hidden">
      <SEO 
        title="الرئيسية | منصة عطري" 
        description="اكتشف عالم العطور الفاخرة والنيش بأسعار تنافسية من أفضل المتاجر الموثوقة." 
      />
      {/* ── Hero Section (Ultra Premium) ────────────────────────── */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
        {/* Background Particles/Glow */}
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-primary/20 blur-[150px] rounded-full pointer-events-none" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-gold-glow blur-[120px] rounded-full pointer-events-none" />
        
        {/* ── Cinematic Background Video ── */}
        <div className="absolute inset-0 z-0 pointer-events-none flex items-center justify-center overflow-hidden bg-[#050505]">
          {/* Dark Overlays to ensure text readability while keeping the video clear */}
          <div className="absolute inset-0 bg-black/20 z-10" />
          <div className="absolute inset-0 bg-gradient-to-l from-black/70 via-black/20 to-transparent z-10" />
          
          <video 
            autoPlay 
            loop 
            muted 
            playsInline
            className="w-full h-full object-cover lg:object-left mix-blend-screen opacity-100 scale-105"
          >
            <source src="/video/gemini_generated_video_553b0f73.mp4" type="video/mp4" />
          </video>
        </div>

        <div className="container-px relative z-20 grid lg:grid-cols-2 gap-12 items-center py-20">
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border-primary/20 text-primary text-sm font-bold mb-6">
              <Sparkles size={16} />
              اكتشف عالم العطور النيش
            </div>
            <h1 className="text-5xl md:text-7xl font-bold leading-[1.1] mb-8">
              روائح تروي <br />
              <span className="luxury-text italic">قصصـاً لا تُنسى</span>
            </h1>
            <p className="text-white font-semibold drop-shadow-md text-lg md:text-xl max-w-lg mb-10 leading-relaxed">
              نجمع لك أرقى العطور العالمية بأسعار تنافسية من أفضل المتاجر الموثوقة. ابحث، قارن، وتسوق بذكاء.
            </p>
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <Link to="/items" className="btn-gold w-full sm:w-auto px-10 py-4 text-lg">تصفح العطور</Link>
              <Link to="/quiz" className="w-full sm:w-auto glass flex items-center justify-center px-10 py-4 rounded-full font-bold hover:bg-secondary transition-all">اكتشف عطرك المثالي</Link>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.4 }}
            className="relative hidden lg:block h-full min-h-[500px]"
          >
            {/* 
               The video is rendering behind this grid column.
               We keep this column empty so the cinematic video shines through clearly,
               but we add some floating luxury badges to enhance the premium feel.
            */}
            <div className="absolute top-1/4 -right-12 glass p-4 rounded-2xl shadow-xl z-20 flex items-center gap-4 animate-float [animation-delay:1s]">
              <div className="w-12 h-12 rounded-full bg-green-500/20 text-green-500 flex items-center justify-center">
                <ShieldCheck size={24} />
              </div>
              <div>
                <p className="text-sm font-bold text-white">متاجر موثوقة</p>
                <p className="text-xs text-muted-foreground">100% أصلي</p>
              </div>
            </div>
            
            <div className="absolute bottom-1/3 left-0 glass p-4 rounded-2xl shadow-xl z-20 flex items-center gap-4 animate-float">
              <div className="w-12 h-12 rounded-full bg-primary/20 text-primary flex items-center justify-center">
                <Award size={24} />
              </div>
              <div>
                <p className="text-sm font-bold text-white">أرقى الماركات</p>
                <p className="text-xs text-muted-foreground">أسعار تنافسية</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Features Section ─────────────────────────────────────── */}
      <section className="container-px py-20 border-y border-border/50">
        <div className="grid md:grid-cols-3 gap-12">
          {[
            { icon: <Award className="text-primary" />, title: "أفضل الماركات", desc: "نجمع لك أكثر من 500 ماركة عالمية ونيش في مكان واحد." },
            { icon: <Zap className="text-primary" />, title: "تحديث لحظي", desc: "أسعار محدثة على مدار الساعة من كافة المتاجر الكبرى." },
            { icon: <ShieldCheck className="text-primary" />, title: "تنبيهات السعر", desc: "سجل تنبيهاً وسنخبرك فور وصول العطر للسعر الذي تريده." },
          ].map((feat, i) => (
            <motion.div key={i} {...fadeInUp} className="text-center group">
              <div className="w-16 h-16 rounded-2xl glass flex items-center justify-center mx-auto mb-6 group-hover:scale-110 group-hover:bg-primary/10 transition-all">
                {feat.icon}
              </div>
              <h3 className="text-xl font-bold mb-3">{feat.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{feat.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Trending Section ─────────────────────────────────────── */}
      <section className="container-px py-24">
        <div className="flex flex-col md:flex-row items-end justify-between mb-12 gap-6">
          <motion.div {...fadeInUp}>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">الأكثر <span className="luxury-text">رواجـاً</span></h2>
            <p className="text-muted-foreground">استكشف العطور التي خطفت الأنظار هذا الموسم.</p>
          </motion.div>
          <Link to="/items" className="nav-link flex items-center gap-2 group">
            مشاهدة الكل
            <ChevronLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-8">
          {itemsLoading
            ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
            : data?.items.map((item, i) => (
                <ItemCard 
                  key={item.id} 
                  item={item} 
                  index={i} 
                  isSaved={savedSet.has(item.id)}
                  hasAlert={alertSet.has(item.id)}
                />
              ))
          }
        </div>
      </section>

      {/* ── Newsletter Section (Luxury) ─────────────────────────── */}
      <section className="container-px py-24">
        <div className="relative glass rounded-[3rem] p-12 md:p-24 overflow-hidden text-center shadow-2xl">
          <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 blur-[80px] rounded-full" />
          <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-primary/10 blur-[80px] rounded-full" />
          
          <motion.div {...fadeInUp} className="relative z-10 max-w-2xl mx-auto">
            <Sparkles className="mx-auto mb-6 text-primary" size={40} />
            <h2 className="text-3xl md:text-5xl font-bold mb-6">انضم إلى قائمة النخبة</h2>
            <p className="text-muted-foreground text-lg mb-10">
              كن أول من يعرف عن الخصومات الحصرية وإطلاق العطور النادرة والجديدة.
            </p>
            <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-4">
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="بريدك الإلكتروني"
                className="flex-1 glass border-2 border-border/50 p-4 rounded-full outline-none focus:border-primary transition-all text-center sm:text-right"
                disabled={isSubscribing}
              />
              <button 
                type="submit" 
                disabled={isSubscribing}
                className="btn-gold px-12 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isSubscribing ? 'جاري الاشتراك...' : 'اشتراك'}
              </button>
            </form>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
