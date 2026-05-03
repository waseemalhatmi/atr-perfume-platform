import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Search, Moon, Sun, User, LogOut, ShieldCheck, Menu, X, ShoppingBag, Bell } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'
import { useCompareStore } from '@/store/compareStore'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchNotifications, readAllNotifications } from '@/lib/api'
import toast from 'react-hot-toast'

export default function Navbar() {
  const { user, logout } = useAuthStore()
  const { isDark, toggleTheme } = useThemeStore()
  const navigate = useNavigate()
  const location = useLocation()
  const compareCount = useCompareStore(s => s.ids.length)
  
  const [isScrolled, setIsScrolled] = useState(false)
  const [mobileOpen, setMobile]     = useState(false)
  const [searchOpen, setSearch]     = useState(false)
  const [notifOpen, setNotifOpen]   = useState(false)
  const [searchQ, setSearchQ]       = useState('')

  const queryClient = useQueryClient()
  
  const { data: notifData } = useQuery({
    queryKey: ['notifications'],
    queryFn: fetchNotifications,
    enabled: !!user,
    refetchInterval: 60000, // Poll every minute for alerts
  })

  const readAllMutation = useMutation({
    mutationFn: readAllNotifications,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] })
  })

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll)
    // Initialize theme class on mount
    if (isDark) document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
    return () => window.removeEventListener('scroll', handleScroll)
  }, [isDark])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQ.trim()) {
      setSearch(false)
      navigate(`/search?q=${encodeURIComponent(searchQ.trim())}`)
    }
  }

  return (
    <>
      <header
        className={`fixed top-0 left-0 w-full z-[100] transition-all duration-500 ${
          isScrolled ? 'py-3 glass shadow-lg' : 'py-6 bg-transparent'
        }`}
      >
        <div className="container-px flex items-center justify-between">
          
          {/* Mobile Menu Trigger */}
          <button type="button" onClick={() => setMobile(true)} aria-label="القائمة الرئيسية" className="lg:hidden p-2 text-foreground">
            <Menu size={24} />
          </button>

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-10 h-10 rounded-xl bg-luxury-gradient flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
              <ShoppingBag size={22} className="text-black" />
            </div>
            <span className="luxury-text text-2xl font-bold tracking-tighter">عطري</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-8">
            <Link to="/" className={`nav-link ${location.pathname === '/' ? 'text-primary' : ''}`}>الرئيسية</Link>
            <Link to="/items" className={`nav-link ${location.pathname === '/items' ? 'text-primary' : ''}`}>العطور</Link>
            <Link to="/search" className={`nav-link ${location.pathname === '/search' ? 'text-primary' : ''}`}>اكتشف</Link>
            <Link to="/compare" className={`px-4 py-1.5 rounded-full font-bold transition-all text-sm flex items-center gap-2 ${
              location.pathname === '/compare' 
              ? 'bg-primary text-primary-foreground shadow-lg' 
              : 'bg-secondary/50 text-muted-foreground hover:bg-secondary hover:text-foreground'
            }`}>
              المقارنة
              {compareCount > 0 && (
                <span className="flex items-center justify-center bg-black text-white text-[10px] w-4 h-4 rounded-full">
                  {compareCount}
                </span>
              )}
            </Link>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2 md:gap-4">
            <button type="button" onClick={() => setSearch(true)} aria-label="بحث" className="p-2 hover:text-primary transition-colors">
              <Search size={20} />
            </button>
            
            <button type="button" onClick={toggleTheme} aria-label="تبديل الوضع الليلي" className="p-2 hover:text-primary transition-colors hidden sm:block">
              {isDark ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            {user && (
              <div className="relative">
                <button type="button" onClick={() => setNotifOpen(!notifOpen)} aria-label="التنبيهات" className="p-2 hover:text-primary transition-colors relative">
                  <Bell size={20} />
                  {notifData?.unread_count > 0 && (
                    <span className="absolute top-1 right-2 w-2.5 h-2.5 bg-red-500 rounded-full border border-background shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
                  )}
                </button>

                <AnimatePresence>
                  {notifOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      className="absolute left-[-20px] sm:left-0 mt-4 w-[300px] sm:w-[320px] max-w-[90vw] max-h-[400px] overflow-y-auto glass p-4 shadow-2xl rounded-2xl z-50 border border-border origin-top-left"
                    >
                      <div className="flex justify-between items-center mb-4 border-b border-border/50 pb-2">
                        <h3 className="font-bold text-sm">التنبيهات</h3>
                        {notifData?.unread_count > 0 && (
                          <button type="button" onClick={() => readAllMutation.mutate()} aria-label="تحديد الكل كمقروء" className="text-[10px] text-primary hover:underline">
                            تحديد الكل كمقروء
                          </button>
                        )}
                      </div>
                      
                      {notifData?.data?.length > 0 ? (
                        <div className="space-y-3">
                          {notifData.data.map((n: any) => (
                            <Link key={n.id} to={n.link || '#'} onClick={() => setNotifOpen(false)} className={`block p-3 rounded-xl transition-colors ${n.is_read ? 'bg-secondary/20 hover:bg-secondary/50' : 'bg-primary/10 border border-primary/20 hover:bg-primary/20'}`}>
                              <h4 className="text-xs font-bold mb-1 flex items-center gap-2">
                                {!n.is_read && <span className="w-1.5 h-1.5 rounded-full bg-primary inline-block" />}
                                {n.title}
                              </h4>
                              <p className="text-[10px] text-muted-foreground leading-relaxed">{n.message}</p>
                              <span className="text-[8px] text-muted-foreground opacity-70 mt-2 block">
                                {new Date(n.created_at).toLocaleDateString('ar-SA')}
                              </span>
                            </Link>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-muted-foreground">
                          <Bell size={24} className="mx-auto mb-2 opacity-20" />
                          <p className="text-xs">لا توجد تنبيهات حالياً</p>
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {user ? (
              <Link to="/profile" className="flex items-center gap-2 p-1 pr-3 glass rounded-full hover:border-primary/50 transition-all">
                <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center overflow-hidden">
                  <User size={16} />
                </div>
                <span className="hidden md:block text-xs font-bold truncate max-w-[100px]">حسابي</span>
              </Link>
            ) : (
              <Link to="/login" className="btn-gold !py-2 !px-5 text-sm">دخول</Link>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Sidebar */}
      <AnimatePresence>
        {mobileOpen && (
          <div className="fixed inset-0 z-[200]">
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setMobile(false)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="absolute top-0 right-0 h-full w-[280px] glass p-8 shadow-2xl flex flex-col"
            >
              <div className="flex justify-between items-center mb-12">
                <span className="luxury-text text-2xl font-bold">عطري</span>
                <button type="button" onClick={() => setMobile(false)} aria-label="إغلاق القائمة" className="p-2 text-muted-foreground"><X size={24} /></button>
              </div>

              <nav className="flex flex-col gap-6 text-lg font-medium">
                <Link to="/" onClick={() => setMobile(false)} className="hover:text-primary">الرئيسية</Link>
                <Link to="/items" onClick={() => setMobile(false)} className="hover:text-primary">جميع العطور</Link>
                <Link to="/compare" onClick={() => setMobile(false)} className="hover:text-primary flex items-center justify-between">
                  <span>المقارنة</span>
                  {compareCount > 0 && <span className="badge--luxury text-[10px] px-2">{compareCount}</span>}
                </Link>
                <Link to="/profile" onClick={() => setMobile(false)} className="hover:text-primary">الملف الشخصي</Link>
              </nav>

              <div className="mt-auto pt-8 border-t border-border/50">
                {user ? (
                  <button type="button" onClick={logout} aria-label="تسجيل خروج" className="flex items-center gap-2 text-red-500 font-bold">
                    <LogOut size={20} /> تسجيل خروج
                  </button>
                ) : (
                  <Link to="/login" onClick={() => setMobile(false)} className="btn-gold w-full text-center">انضم إلينا</Link>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Search Overlay (Improved) */}
      <AnimatePresence>
        {searchOpen && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[300] glass flex flex-col items-center justify-start pt-[15vh] px-6"
            role="dialog"
            aria-modal="true"
          >
            <button type="button" onClick={() => setSearch(false)} aria-label="إغلاق البحث" className="absolute top-8 left-8 p-4 text-muted-foreground"><X size={32} /></button>
            
            <motion.div 
              initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
              className="w-full max-w-2xl"
            >
              <h2 className="luxury-text text-4xl md:text-5xl font-bold text-center mb-12">ابحث عن عطرك المفضل</h2>
              <form onSubmit={handleSearch} className="relative group">
                <input 
                  autoFocus
                  placeholder="ماركة، مكونات، أو اسم العطر..."
                  className="w-full bg-secondary/50 border-2 border-border p-6 pr-14 rounded-2xl text-xl focus:border-primary transition-all outline-none"
                  value={searchQ}
                  onChange={(e) => setSearchQ(e.target.value)}
                />
                <Search className="absolute right-5 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={24} />
                <button type="submit" className="absolute left-4 top-1/2 -translate-y-1/2 btn-gold !py-2 !px-6 text-sm">بحث</button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Spacer to prevent content jump */}
      <div className="h-20" />
    </>
  )
}
