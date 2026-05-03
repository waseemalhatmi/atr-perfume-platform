import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Users, Search, Mail, Shield, ShieldOff,
  User as UserIcon, Globe, Lock, Calendar,
  Crown, TrendingUp, UserCheck, ChevronLeft, ChevronRight
} from 'lucide-react'
import { fetchAdminUsers } from '@/lib/adminApi'

export default function AdminUsers() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'admin' | 'google' | 'local'>('all')
  const [page, setPage] = useState(1)
  const PER_PAGE = 10

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: fetchAdminUsers,
  })

  const filtered = useMemo(() => {
    let list = users as any[]
    if (search) list = list.filter((u: any) =>
      u.email.toLowerCase().includes(search.toLowerCase())
    )
    if (filter === 'admin') list = list.filter((u: any) => u.is_admin)
    if (filter === 'google') list = list.filter((u: any) => u.provider === 'google')
    if (filter === 'local') list = list.filter((u: any) => u.provider === 'local')
    return list
  }, [users, search, filter])

  const totalPages = Math.ceil(filtered.length / PER_PAGE)
  const paginated = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE)

  const stats = [
    {
      label: 'إجمالي الأعضاء',
      value: (users as any[]).length,
      icon: <Users size={22} />,
      color: 'from-blue-500 to-indigo-500',
      bg: 'bg-blue-500/10',
    },
    {
      label: 'المشرفون',
      value: (users as any[]).filter((u: any) => u.is_admin).length,
      icon: <Crown size={22} />,
      color: 'from-amber-400 to-orange-500',
      bg: 'bg-amber-500/10',
    },
    {
      label: 'حسابات Google',
      value: (users as any[]).filter((u: any) => u.provider === 'google').length,
      icon: <Globe size={22} />,
      color: 'from-green-400 to-emerald-500',
      bg: 'bg-green-500/10',
    },
    {
      label: 'حسابات محلية',
      value: (users as any[]).filter((u: any) => u.provider === 'local').length,
      icon: <Lock size={22} />,
      color: 'from-purple-400 to-violet-500',
      bg: 'bg-purple-500/10',
    },
  ]

  const FILTER_TABS = [
    { key: 'all', label: 'الكل' },
    { key: 'admin', label: 'المشرفون' },
    { key: 'google', label: 'Google' },
    { key: 'local', label: 'محلي' },
  ]

  const formatDate = (iso: string | null) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('ar-SA', { year: 'numeric', month: 'short', day: 'numeric' })
  }

  return (
    <div className="space-y-8 pb-10" dir="rtl">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold luxury-text">إدارة الأعضاء</h1>
          <p className="text-muted-foreground mt-1">
            راقب الأعضاء المسجلين، وادر الصلاحيات والحسابات بشكل كامل.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-2xl bg-secondary border border-border/50">
          <TrendingUp size={14} className="text-primary" />
          <span>{(users as any[]).length} عضو مسجل</span>
        </div>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="glass p-5 rounded-3xl border border-border/50 flex items-center gap-4 hover:shadow-xl hover:shadow-primary/5 transition-all group"
          >
            <div className={`p-3 rounded-2xl ${s.bg} bg-gradient-to-br ${s.color} bg-opacity-10`}>
              <div className={`bg-gradient-to-br ${s.color} bg-clip-text text-transparent`}>
                {s.icon}
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">{s.label}</p>
              <p className="text-2xl font-bold">{s.value}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Filters + Search */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
        {/* Search */}
        <div className="relative flex-1 w-full">
          <Search size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            placeholder="البحث بالبريد الإلكتروني..."
            className="w-full bg-secondary/30 border border-border/50 rounded-2xl pr-11 pl-4 py-3 text-sm outline-none focus:border-primary/50 transition-all"
          />
        </div>
        {/* Filter Tabs */}
        <div className="flex gap-2 bg-secondary/30 p-1.5 rounded-2xl border border-border/50">
          {FILTER_TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => { setFilter(tab.key as any); setPage(1) }}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                filter === tab.key
                  ? 'bg-primary text-black shadow-lg shadow-primary/20'
                  : 'hover:bg-secondary text-muted-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass rounded-3xl border border-border/50 overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead>
              <tr className="bg-secondary/50 border-b border-border/50">
                <th className="p-5 font-bold text-sm text-muted-foreground">#</th>
                <th className="p-5 font-bold text-sm text-muted-foreground">العضو</th>
                <th className="p-5 font-bold text-sm text-muted-foreground">نوع الحساب</th>
                <th className="p-5 font-bold text-sm text-muted-foreground">الصلاحية</th>
                <th className="p-5 font-bold text-sm text-muted-foreground">تاريخ الانضمام</th>
                <th className="p-5 font-bold text-sm text-muted-foreground">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              <AnimatePresence mode="popLayout">
                {isLoading ? (
                  [...Array(5)].map((_, i) => (
                    <tr key={i}>
                      {[...Array(6)].map((_, j) => (
                        <td key={j} className="p-5">
                          <div className="h-4 bg-secondary/60 rounded-full animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : paginated.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-20 text-center">
                      <div className="flex flex-col items-center gap-3 text-muted-foreground">
                        <UserCheck size={48} className="opacity-20" />
                        <p className="font-bold">لا يوجد أعضاء مطابقون</p>
                      </div>
                    </td>
                  </tr>
                ) : paginated.map((user: any, idx: number) => (
                  <motion.tr
                    layout
                    key={user.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="hover:bg-secondary/20 transition-all group"
                  >
                    {/* # */}
                    <td className="p-5 text-muted-foreground text-xs font-mono">
                      #{user.id}
                    </td>

                    {/* User */}
                    <td className="p-5">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20 flex items-center justify-center shrink-0">
                          <UserIcon size={16} className="text-primary" />
                        </div>
                        <div>
                          <p className="font-bold text-sm">{user.email.split('@')[0]}</p>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                    </td>

                    {/* Provider */}
                    <td className="p-5">
                      {user.provider === 'google' ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full bg-green-500/10 text-green-500 border border-green-500/20">
                          <Globe size={12} /> Google
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full bg-secondary border border-border/50 text-muted-foreground">
                          <Lock size={12} /> محلي
                        </span>
                      )}
                    </td>

                    {/* Role */}
                    <td className="p-5">
                      {user.is_admin ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20">
                          <Crown size={12} /> مشرف
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          <UserIcon size={12} /> عضو
                        </span>
                      )}
                    </td>

                    {/* Date */}
                    <td className="p-5">
                      <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Calendar size={12} /> {formatDate(user.created_at)}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="p-5">
                      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all">
                        <a
                          href={`mailto:${user.email}`}
                          className="p-2 hover:bg-primary hover:text-black rounded-xl transition-all"
                          title="مراسلة"
                        >
                          <Mail size={15} />
                        </a>
                        {user.is_admin ? (
                          <button className="p-2 hover:bg-red-500/10 hover:text-red-500 rounded-xl transition-all" title="إلغاء الإدارة">
                            <ShieldOff size={15} />
                          </button>
                        ) : (
                          <button className="p-2 hover:bg-amber-500/10 hover:text-amber-500 rounded-xl transition-all" title="منح صلاحية إدارة">
                            <Shield size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!isLoading && filtered.length > PER_PAGE && (
          <div className="p-5 flex justify-between items-center bg-secondary/20 border-t border-border/50">
            <p className="text-xs text-muted-foreground">
              عرض {(page - 1) * PER_PAGE + 1}–{Math.min(page * PER_PAGE, filtered.length)} من أصل {filtered.length}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 border border-border/50 rounded-xl hover:bg-secondary disabled:opacity-30 transition-all"
              >
                <ChevronRight size={16} />
              </button>
              {[...Array(totalPages)].map((_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i + 1)}
                  className={`w-9 h-9 rounded-xl text-xs font-bold transition-all ${
                    page === i + 1
                      ? 'bg-primary text-black'
                      : 'border border-border/50 hover:bg-secondary'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 border border-border/50 rounded-xl hover:bg-secondary disabled:opacity-30 transition-all"
              >
                <ChevronLeft size={16} />
              </button>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  )
}
