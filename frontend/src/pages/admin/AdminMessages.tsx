import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare, Mail, MailOpen, Trash2,
  Search, Eye, Clock, CheckCheck, AlertCircle,
  X, User as UserIcon, ChevronLeft, ChevronRight
} from 'lucide-react'
import { fetchAdminMessages, markMessageRead, deleteAdminMessage } from '@/lib/adminApi'
import toast from 'react-hot-toast'

export default function AdminMessages() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all')
  const [selected, setSelected] = useState<any>(null)

  const { data: messages = [], isLoading } = useQuery({
    queryKey: ['adminMessages'],
    queryFn: fetchAdminMessages,
  })

  const markReadMutation = useMutation({
    mutationFn: markMessageRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminMessages'] })
      toast.success('تم تعليم الرسالة كمقروءة')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteAdminMessage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminMessages'] })
      setSelected(null)
      toast.success('تم حذف الرسالة')
    },
    onError: () => toast.error('حدث خطأ أثناء الحذف'),
  })

  const msgs = messages as any[]
  const unreadCount = msgs.filter(m => !m.is_read).length

  const filtered = msgs.filter(m => {
    const matchSearch = m.name?.toLowerCase().includes(search.toLowerCase()) ||
      m.email?.toLowerCase().includes(search.toLowerCase()) ||
      m.subject?.toLowerCase().includes(search.toLowerCase())
    const matchFilter = filter === 'all' || (filter === 'unread' ? !m.is_read : m.is_read)
    return matchSearch && matchFilter
  })

  const formatDate = (iso: string | null) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('ar-SA', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  }

  const handleOpen = (msg: any) => {
    setSelected(msg)
    if (!msg.is_read) markReadMutation.mutate(msg.id)
  }

  return (
    <div className="space-y-8 pb-10" dir="rtl">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold luxury-text">الرسائل الواردة</h1>
          <p className="text-muted-foreground mt-1">راجع رسائل الزوار والتواصل المباشر معهم.</p>
        </div>
        {unreadCount > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500">
            <AlertCircle size={16} />
            <span className="text-sm font-bold">{unreadCount} رسالة غير مقروءة</span>
          </div>
        )}
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'إجمالي الرسائل', value: msgs.length, icon: <MessageSquare size={20} />, color: 'from-blue-500 to-indigo-500' },
          { label: 'غير مقروءة', value: unreadCount, icon: <Mail size={20} />, color: 'from-red-400 to-rose-500' },
          { label: 'مقروءة', value: msgs.length - unreadCount, icon: <MailOpen size={20} />, color: 'from-emerald-400 to-green-500' },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="glass p-5 rounded-3xl border border-border/50 flex items-center gap-4"
          >
            <div className={`p-3 rounded-2xl bg-gradient-to-br ${s.color} shadow-lg`}>
              <div className="text-white">{s.icon}</div>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className="text-2xl font-bold">{s.value}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="البحث بالاسم أو البريد أو الموضوع..."
            className="w-full bg-secondary/30 border border-border/50 rounded-2xl pr-11 pl-4 py-3 text-sm outline-none focus:border-primary/50 transition-all"
          />
        </div>
        <div className="flex gap-2 bg-secondary/30 p-1.5 rounded-2xl border border-border/50">
          {[
            { key: 'all', label: 'الكل' },
            { key: 'unread', label: 'غير مقروءة' },
            { key: 'read', label: 'مقروءة' },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key as any)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                filter === tab.key
                  ? 'bg-primary text-black shadow-md shadow-primary/20'
                  : 'hover:bg-secondary text-muted-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Two-pane layout */}
      <div className="flex gap-6 min-h-[500px]">
        {/* Message List */}
        <div className="flex-1 glass rounded-3xl border border-border/50 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-border/50 bg-secondary/30">
            <p className="text-xs text-muted-foreground font-bold">{filtered.length} رسالة</p>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-border/30">
            <AnimatePresence>
              {isLoading ? (
                [...Array(5)].map((_, i) => (
                  <div key={i} className="p-5 space-y-2 animate-pulse">
                    <div className="h-4 bg-secondary/60 rounded-full w-1/3" />
                    <div className="h-3 bg-secondary/40 rounded-full w-2/3" />
                  </div>
                ))
              ) : filtered.length === 0 ? (
                <div className="p-20 text-center text-muted-foreground flex flex-col items-center gap-3">
                  <MessageSquare size={48} className="opacity-20" />
                  <p className="font-bold">لا توجد رسائل</p>
                </div>
              ) : filtered.map((msg: any) => (
                <motion.button
                  key={msg.id}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  onClick={() => handleOpen(msg)}
                  className={`w-full text-right p-5 hover:bg-secondary/30 transition-all group flex items-start gap-3 ${
                    selected?.id === msg.id ? 'bg-primary/5 border-r-2 border-primary' : ''
                  }`}
                >
                  {/* Avatar */}
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20 flex items-center justify-center shrink-0">
                    <UserIcon size={18} className="text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start gap-2">
                      <p className={`text-sm truncate ${!msg.is_read ? 'font-bold' : 'font-medium text-muted-foreground'}`}>
                        {msg.name}
                      </p>
                      {!msg.is_read && (
                        <span className="w-2 h-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-lg shadow-primary/50" />
                      )}
                    </div>
                    <p className={`text-xs truncate mt-0.5 ${!msg.is_read ? 'text-foreground' : 'text-muted-foreground'}`}>
                      {msg.subject}
                    </p>
                    <p className="text-[10px] text-muted-foreground/60 mt-1 flex items-center gap-1">
                      <Clock size={10} /> {formatDate(msg.created_at)}
                    </p>
                  </div>
                </motion.button>
              ))}
            </AnimatePresence>
          </div>
        </div>

        {/* Message Detail */}
        <AnimatePresence mode="wait">
          {selected ? (
            <motion.div
              key={selected.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="w-[45%] glass rounded-3xl border border-border/50 flex flex-col overflow-hidden"
            >
              {/* Toolbar */}
              <div className="p-5 border-b border-border/50 bg-secondary/30 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  {selected.is_read ? (
                    <span className="flex items-center gap-1.5 text-xs text-emerald-500 font-bold">
                      <CheckCheck size={14} /> مقروءة
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-xs text-primary font-bold">
                      <Mail size={14} /> جديدة
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <a
                    href={`mailto:${selected.email}?subject=Re: ${selected.subject}`}
                    className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-xl bg-primary/10 text-primary hover:bg-primary hover:text-black transition-all"
                  >
                    <Mail size={13} /> رد
                  </a>
                  <button
                    onClick={() => deleteMutation.mutate(selected.id)}
                    className="p-2 hover:bg-red-500/10 hover:text-red-500 rounded-xl transition-all"
                  >
                    <Trash2 size={15} />
                  </button>
                  <button
                    onClick={() => setSelected(null)}
                    className="p-2 hover:bg-secondary rounded-xl transition-all"
                  >
                    <X size={15} />
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <div>
                  <h2 className="text-xl font-bold mb-1">{selected.subject}</h2>
                  <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><UserIcon size={12} /> {selected.name}</span>
                    <span className="flex items-center gap-1"><Mail size={12} /> {selected.email}</span>
                    <span className="flex items-center gap-1"><Clock size={12} /> {formatDate(selected.created_at)}</span>
                  </div>
                </div>
                <div className="h-px bg-border/50" />
                <div className="bg-secondary/20 rounded-2xl p-5 text-sm leading-relaxed whitespace-pre-wrap border border-border/30">
                  {selected.message}
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="w-[45%] glass rounded-3xl border border-border/50 flex flex-col items-center justify-center text-muted-foreground gap-4"
            >
              <Eye size={48} className="opacity-15" />
              <p className="font-bold text-sm">اختر رسالة للعرض</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
