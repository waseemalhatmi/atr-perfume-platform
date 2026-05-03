import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Search, Users, Mail, TrendingUp,
  Calendar, Download, ChevronLeft, ChevronRight,
  CheckCircle2, Clock
} from 'lucide-react'
import { fetchAdminNewsletter } from '@/lib/adminApi'

export default function AdminNewsletter() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const PER_PAGE = 12

  const { data: subs = [], isLoading } = useQuery({
    queryKey: ['adminNewsletter'],
    queryFn: fetchAdminNewsletter,
  })

  const subscribers = subs as any[]

  const filtered = useMemo(() =>
    subscribers.filter(s =>
      s.email?.toLowerCase().includes(search.toLowerCase())
    ), [subscribers, search])

  const totalPages = Math.ceil(filtered.length / PER_PAGE)
  const paginated = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE)

  const formatDate = (iso: string | null) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('ar-SA', {
      year: 'numeric', month: 'long', day: 'numeric'
    })
  }

  const exportCSV = () => {
    const rows = [['البريد الإلكتروني', 'تاريخ الاشتراك']]
    subscribers.forEach(s => rows.push([s.email, formatDate(s.subscribed_at)]))
    const csv = rows.map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'newsletter_subscribers.csv'
    a.click()
  }

  return (
    <div className="space-y-8 pb-10" dir="rtl">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold luxury-text">القائمة البريدية</h1>
          <p className="text-muted-foreground mt-1">إدارة المشتركين في النشرة البريدية وتصديرها.</p>
        </div>
        <button
          onClick={exportCSV}
          className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500 hover:text-white transition-all font-bold text-sm"
        >
          <Download size={16} /> تصدير CSV
        </button>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            label: 'إجمالي المشتركين',
            value: subscribers.length,
            icon: <Users size={22} />,
            color: 'from-blue-500 to-indigo-500',
            desc: 'مشترك في القائمة البريدية',
          },
          {
            label: 'اشتراكات هذا الشهر',
            value: subscribers.filter(s => {
              if (!s.subscribed_at) return false
              const d = new Date(s.subscribed_at)
              const now = new Date()
              return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
            }).length,
            icon: <TrendingUp size={22} />,
            color: 'from-emerald-400 to-teal-500',
            desc: 'خلال الشهر الحالي',
          },
          {
            label: 'معدل النمو',
            value: subscribers.length > 0 ? '+' + Math.round((subscribers.length / 30)).toLocaleString() : '0',
            icon: <Send size={22} />,
            color: 'from-purple-400 to-violet-500',
            desc: 'مشترك جديد تقريباً / شهر',
          },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass p-6 rounded-3xl border border-border/50 relative overflow-hidden group hover:shadow-xl hover:shadow-primary/5 transition-all"
          >
            <div className={`absolute -top-10 -left-10 w-32 h-32 bg-gradient-to-br ${s.color} opacity-5 blur-3xl group-hover:opacity-15 transition-opacity rounded-full`} />
            <div className={`p-3 rounded-2xl bg-gradient-to-br ${s.color} shadow-lg w-fit mb-4`}>
              <div className="text-white">{s.icon}</div>
            </div>
            <p className="text-4xl font-bold mb-1">{s.value}</p>
            <p className="text-sm font-bold mb-0.5">{s.label}</p>
            <p className="text-xs text-muted-foreground">{s.desc}</p>
          </motion.div>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          placeholder="البحث بالبريد الإلكتروني..."
          className="w-full bg-secondary/30 border border-border/50 rounded-2xl pr-11 pl-4 py-3 text-sm outline-none focus:border-primary/50 transition-all"
        />
      </div>

      {/* Subscribers Grid */}
      <div className="glass rounded-3xl border border-border/50 overflow-hidden">
        <div className="p-5 border-b border-border/50 bg-secondary/30 flex justify-between items-center">
          <p className="text-sm font-bold">قائمة المشتركين</p>
          <span className="text-xs text-muted-foreground">{filtered.length} مشترك</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
          <AnimatePresence>
            {isLoading ? (
              [...Array(6)].map((_, i) => (
                <div key={i} className="h-24 bg-secondary/30 rounded-2xl animate-pulse" />
              ))
            ) : paginated.length === 0 ? (
              <div className="col-span-3 p-20 text-center text-muted-foreground flex flex-col items-center gap-3">
                <Mail size={48} className="opacity-20" />
                <p className="font-bold">لا يوجد مشتركون</p>
              </div>
            ) : paginated.map((sub: any, i: number) => (
              <motion.div
                key={sub.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.02 }}
                className="group flex items-center gap-4 p-4 rounded-2xl border border-border/30 bg-secondary/10 hover:bg-secondary/30 hover:border-primary/20 transition-all"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20 flex items-center justify-center shrink-0">
                  <Mail size={16} className="text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold truncate">{sub.email}</p>
                  <p className="text-[11px] text-muted-foreground flex items-center gap-1 mt-0.5">
                    <Calendar size={10} /> {formatDate(sub.subscribed_at)}
                  </p>
                </div>
                <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Pagination */}
        {!isLoading && filtered.length > PER_PAGE && (
          <div className="p-5 flex justify-between items-center bg-secondary/20 border-t border-border/50">
            <p className="text-xs text-muted-foreground">
              عرض {(page - 1) * PER_PAGE + 1}–{Math.min(page * PER_PAGE, filtered.length)} من {filtered.length}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 border border-border/50 rounded-xl hover:bg-secondary disabled:opacity-30 transition-all"
              >
                <ChevronRight size={16} />
              </button>
              {[...Array(Math.min(totalPages, 5))].map((_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i + 1)}
                  className={`w-9 h-9 rounded-xl text-xs font-bold transition-all ${
                    page === i + 1 ? 'bg-primary text-black' : 'border border-border/50 hover:bg-secondary'
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
      </div>
    </div>
  )
}
