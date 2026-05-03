import { Link, useNavigate, useLocation, Outlet } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard, Package, Users, Settings, 
  MessageSquare, Mail, Home, LogOut, ChevronRight, 
  Bell, Search, User as UserIcon, Brain
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'

export default function AdminLayout() {
  const { user, logout } = useAuthStore()
  const { isDark } = useThemeStore()
  const location = useLocation()
  const navigate = useNavigate()

  if (!user?.is_admin) {
    // This is a safety check, but we'll also have a Route guard
    return <div className="p-20 text-center font-bold text-red-500 text-2xl">عذراً، لا تملك صلاحيات الوصول.</div>
  }

  const menuItems = [
    { name: 'لوحة التحكم',    icon: <LayoutDashboard size={20} />, path: '/admin' },
    { name: 'إدارة العطور',   icon: <Package size={20} />,        path: '/admin/items' },
    { name: 'المستخدمين',     icon: <Users size={20} />,          path: '/admin/users' },
    { name: 'الرسائل',        icon: <MessageSquare size={20} />,  path: '/admin/messages' },
    { name: 'النشرة البريدية',icon: <Mail size={20} />,           path: '/admin/newsletter' },
    { name: 'مركز الذكاء',   icon: <Brain size={20} />,          path: '/admin/analytics' },
    { name: 'الإعدادات',      icon: <Settings size={20} />,       path: '/admin/settings' },
  ]

  return (
    <div className="flex min-h-screen bg-secondary/30">
      
      {/* Sidebar */}
      <aside className="w-72 glass border-l border-border/50 sticky top-0 h-screen hidden lg:flex flex-col p-6 z-50">
        <div className="flex items-center gap-3 mb-12 px-2">
          <div className="w-10 h-10 rounded-xl bg-luxury-gradient flex items-center justify-center shadow-lg">
            <LayoutDashboard size={22} className="text-black" />
          </div>
          <span className="luxury-text text-xl font-bold tracking-tight">إدارة عطري</span>
        </div>

        <nav className="flex-1 space-y-2">
          {menuItems.map((item) => {
            const isActive = item.path === '/admin'
              ? location.pathname === '/admin'
              : location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 p-3 px-4 rounded-2xl font-bold text-sm transition-all group ${
                  isActive
                    ? 'bg-primary text-black shadow-lg shadow-primary/20'
                    : 'hover:bg-secondary text-muted-foreground hover:text-foreground'
                }`}
              >
                {item.icon}
                {item.name}
                {isActive && <ChevronRight size={16} className="mr-auto" />}
              </Link>
            )
          })}
        </nav>

        <div className="pt-6 border-t border-border/50">
          <Link to="/" className="flex items-center gap-3 p-3 px-4 rounded-2xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-all mb-2">
            <Home size={18} /> العودة للموقع
          </Link>
          <button 
            onClick={() => { logout(); navigate('/login'); }}
            className="w-full flex items-center gap-3 p-3 px-4 rounded-2xl hover:bg-red-500/10 text-red-500 transition-all font-bold"
          >
            <LogOut size={18} /> تسجيل خروج
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Topbar */}
        <header className="h-20 glass border-b border-border/50 flex items-center justify-between px-8 sticky top-0 z-40">
          <div className="flex items-center gap-4 bg-secondary/50 p-2 px-4 rounded-xl border border-border/50">
            <Search size={18} className="text-muted-foreground" />
            <input placeholder="بحث سريع..." className="bg-transparent border-none outline-none text-sm w-64" />
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2 glass rounded-xl relative">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full" />
            </button>
            <div className="h-8 w-px bg-border/50 mx-2" />
            <div className="flex items-center gap-3">
              <div className="text-left hidden md:block">
                <p className="text-xs font-bold leading-tight">{user?.email ? user.email.split('@')[0] : 'المسؤول'}</p>
                <p className="text-[10px] text-muted-foreground">المدير العام</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center overflow-hidden border border-border/50">
                <UserIcon size={20} />
              </div>
            </div>
          </div>
        </header>

        <main className="p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  )
}
