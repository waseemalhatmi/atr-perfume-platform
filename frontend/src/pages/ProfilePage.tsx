import { useQuery } from '@tanstack/react-query'
import { Navigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { User, Heart, ShieldCheck, LogOut, Bell, Settings, Award, AlertCircle } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { fetchProfile, type ProfileSavedItem } from '@/lib/api'
import { useSavedItems } from '@/hooks/useSavedItems'
import { useMemo } from 'react'
import ItemCard from '@/components/ItemCard'
import SkeletonCard from '@/components/SkeletonCard'

export default function ProfilePage() {
  const { user: storeUser, logout } = useAuthStore()

  /**
   * Uses the shared `fetchProfile` helper (axios-based) instead of raw fetch.
   * Benefits:
   *   - Automatic 401/403/500 error propagation via axios interceptors
   *   - Full TypeScript types on the response
   *   - Consistent error handling with the rest of the app
   *   - React Query caching (stale-while-revalidate for instant navigation)
   */
  const { data, isLoading, isError } = useQuery({
    queryKey: ['profile'],
    queryFn:  fetchProfile,
    enabled:  !!storeUser,
    retry:    1,
    staleTime: 30_000, // 30 s — profile data rarely changes mid-session
  })

  // Not logged in → redirect to login
  if (!storeUser && !isLoading) return <Navigate to="/login" replace />

  const profile = data?.data

  const itemIds = useMemo(() => profile?.saved_items?.map((i: any) => i.id) || [], [profile?.saved_items])
  const { data: savedBatch } = useSavedItems(itemIds)

  // ── Error State ────────────────────────────────────────────────────────────
  if (isError) {
    return (
      <div className="container-px py-32 text-center">
        <div className="glass rounded-[3rem] p-16 max-w-md mx-auto flex flex-col items-center gap-6">
          <AlertCircle size={48} className="text-red-500" />
          <h2 className="text-2xl font-bold">تعذّر تحميل الملف الشخصي</h2>
          <p className="text-muted-foreground">يرجى التأكد من اتصالك بالإنترنت والمحاولة مجدداً.</p>
          <button
            onClick={() => window.location.reload()}
            className="btn-gold px-10"
          >
            إعادة المحاولة
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container-px py-12 md:py-20">
      <div className="grid lg:grid-cols-4 gap-8 items-start">

        {/* ── Sidebar ──────────────────────────────────────────────── */}
        <aside className="lg:col-span-1 space-y-6">
          <div className="glass p-8 rounded-[2.5rem] text-center relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-primary/10 blur-3xl" />
            <div className="relative z-10">
              <div className="w-24 h-24 rounded-full bg-luxury-gradient p-1 mx-auto mb-6 shadow-xl">
                <div className="w-full h-full rounded-full bg-background flex items-center justify-center">
                  <User size={40} className="text-primary" />
                </div>
              </div>
              <h2 className="text-xl font-bold mb-1 truncate">{storeUser?.email.split('@')[0]}</h2>
              <p className="text-xs text-muted-foreground mb-6">{storeUser?.email}</p>

              <div className="flex flex-col gap-2">
                <Link to="/profile" className="flex items-center gap-3 p-3 rounded-2xl bg-primary text-black font-bold text-sm">
                  <User size={18} /> نظرة عامة
                </Link>
                <button
                  aria-label="التنبيهات"
                  className="flex items-center gap-3 p-3 rounded-2xl hover:bg-secondary transition-all text-sm font-bold"
                >
                  <Bell size={18} /> التنبيهات
                </button>
                <button
                  aria-label="الإعدادات"
                  className="flex items-center gap-3 p-3 rounded-2xl hover:bg-secondary transition-all text-sm font-bold"
                >
                  <Settings size={18} /> الإعدادات
                </button>
                <button
                  onClick={logout}
                  aria-label="تسجيل خروج"
                  className="flex items-center gap-3 p-3 rounded-2xl hover:bg-red-500/10 text-red-500 transition-all text-sm font-bold mt-4"
                >
                  <LogOut size={18} /> تسجيل خروج
                </button>
              </div>
            </div>
          </div>

          {storeUser?.is_admin && (
            <a
              href="/admin"
              className="block glass p-6 rounded-[2rem] border-primary/20 group hover:border-primary transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-black transition-all">
                  <ShieldCheck size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-sm">لوحة الإدارة</h3>
                  <p className="text-[10px] text-muted-foreground">تحكم في النظام</p>
                </div>
              </div>
            </a>
          )}
        </aside>

        {/* ── Main Content ─────────────────────────────────────────── */}
        <main className="lg:col-span-3 space-y-12">

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: 'العطور المحفوظة', val: profile?.saved_items?.length ?? 0, icon: <Heart size={20} /> },
              { label: 'تنبيهات السعر',   val: 0,     icon: <Bell  size={20} /> },
              { label: 'نقاط الولاء',     val: '500', icon: <Award size={20} /> },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass p-6 rounded-3xl"
              >
                <div className="text-primary mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold">{stat.val}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider">{stat.label}</div>
              </motion.div>
            ))}
          </div>

          {/* Saved Items */}
          <section>
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-2xl font-bold flex items-center gap-3">
                <Heart size={24} className="text-red-500 fill-current" />
                العطور المحفوظة
              </h3>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
                {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
              </div>
            ) : profile?.saved_items && profile.saved_items.length > 0 ? (
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
                {profile.saved_items.map((item: ProfileSavedItem, i: number) => (
                  <ItemCard 
                    key={item.id} 
                    item={item as any} 
                    index={i} 
                    isSavedBatch={savedBatch?.[`item:${item.id}`] ?? true} 
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-24 glass rounded-[3rem] border-dashed border-2">
                <div className="w-20 h-20 bg-secondary rounded-full flex items-center justify-center mx-auto mb-6">
                  <Heart size={40} className="text-muted-foreground/30" />
                </div>
                <p className="text-muted-foreground mb-8 text-lg">
                  لم تقم بحفظ أي عطور في قائمتك المفضلة حتى الآن.
                </p>
                <Link to="/items" className="btn-gold px-10">ابدأ الاستكشاف</Link>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  )
}
