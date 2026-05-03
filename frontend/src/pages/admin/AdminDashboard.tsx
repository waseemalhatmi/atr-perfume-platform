import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  TrendingUp, Users, Package, Eye, 
  ArrowUpRight, ArrowDownRight, Clock,
  ChevronLeft, ChevronRight
} from 'lucide-react'
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts'
import { fetchAdminStats } from '@/lib/adminApi'

export default function AdminDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['adminStats'],
    queryFn: fetchAdminStats
  })

  if (isLoading) return <div className="p-20 text-center luxury-text animate-pulse font-bold">جاري تحميل البيانات الذكية...</div>
  
  if (!data) return (
    <div className="p-20 text-center text-red-500 glass rounded-3xl border border-red-500/20">
      <p className="font-bold text-xl mb-2">خطأ في تحميل البيانات</p>
      <p className="text-sm opacity-70">تعذر الاتصال بالخادم أو انتهت صلاحية الجلسة. يرجى إعادة تسجيل الدخول.</p>
    </div>
  )

  const stats = [
    { label: 'إجمالي العطور', value: data?.totals?.items ?? 0, icon: <Package size={24} />, color: 'from-blue-500 to-cyan-400', trend: '+12%' },
    { label: 'الزيارات الكلية', value: data?.totals?.total_views ?? 0, icon: <Eye size={24} />, color: 'from-purple-500 to-pink-400', trend: '+18%' },
    { label: 'إجمالي النقرات', value: data?.totals?.total_clicks ?? 0, icon: <TrendingUp size={24} />, color: 'from-amber-500 to-orange-400', trend: '+5%' },
    { label: 'المستخدمين', value: data?.totals?.users ?? 0, icon: <Users size={24} />, color: 'from-emerald-500 to-teal-400', trend: '+2%' },
  ]

  const chartData = data?.daily_stats?.map((d: any) => ({
    name: d?.date ?? '---',
    views: d?.views ?? 0,
    clicks: d?.clicks ?? 0
  })) || []

  return (
    <div className="space-y-8 pb-10">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold luxury-text">نظرة عامة على الأداء</h1>
        <p className="text-muted-foreground">مرحباً بك في مركز التحكم. إليك ملخص نشاط المنصة لهذا اليوم.</p>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass p-6 rounded-3xl border border-border/50 relative overflow-hidden group hover:shadow-2xl hover:shadow-primary/5 transition-all"
          >
            <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${stat.color} opacity-5 blur-3xl group-hover:opacity-20 transition-opacity`} />
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-2xl bg-gradient-to-br ${stat.color} shadow-lg shadow-black/10`}>
                {stat.icon}
              </div>
              <span className={`text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1 ${stat.trend.startsWith('+') ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                {stat.trend.startsWith('+') ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                {stat.trend}
              </span>
            </div>
            <p className="text-sm text-muted-foreground font-medium mb-1">{stat.label}</p>
            <h3 className="text-2xl font-bold">{stat.value?.toLocaleString()}</h3>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Chart */}
        <div className="lg:col-span-2 glass p-8 rounded-3xl border border-border/50">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h3 className="text-xl font-bold">تحليلات الزيارات والنقرات</h3>
              <p className="text-sm text-muted-foreground">مقارنة بين عدد المشاهدات والنقرات الفعلية</p>
            </div>
            <select className="bg-secondary/50 border border-border/50 rounded-xl px-4 py-2 text-sm outline-none">
              <option>آخر 30 يوم</option>
              <option>آخر 7 أيام</option>
            </select>
          </div>
          <div className="h-[350px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.3} />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }} 
                  dy={10}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }} 
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--background)', 
                    borderColor: 'var(--border)',
                    borderRadius: '16px',
                    boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="views" 
                  stroke="var(--primary)" 
                  strokeWidth={3}
                  fillOpacity={1} 
                  fill="url(#colorViews)" 
                />
                <Area 
                  type="monotone" 
                  dataKey="clicks" 
                  stroke="#fbbf24" 
                  strokeWidth={3}
                  fill="transparent" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="glass p-8 rounded-3xl border border-border/50 flex flex-col">
          <h3 className="text-xl font-bold mb-6">أحدث الأنشطة</h3>
          <div className="flex-1 space-y-6 overflow-y-auto max-h-[400px] pr-2">
            {[1,2,3,4,5].map((_, i) => (
              <div key={i} className="flex gap-4 items-start group">
                <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center shrink-0 border border-border/50 group-hover:bg-primary group-hover:text-black transition-colors">
                  <Clock size={18} />
                </div>
                <div>
                  <p className="text-sm font-bold">إضافة عطر جديد</p>
                  <p className="text-xs text-muted-foreground mb-1">تمت إضافة "كريد أفينتوس" بنجاح</p>
                  <span className="text-[10px] text-muted-foreground/60">منذ 15 دقيقة</span>
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-6 p-3 rounded-2xl bg-secondary hover:bg-secondary/80 transition-all text-sm font-bold">
            مشاهدة كل السجلات
          </button>
        </div>
      </div>
    </div>
  )
}
