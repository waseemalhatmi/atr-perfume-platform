import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Brain, Trophy, Download, Target, Users,
  Shirt, Clock, Bot, Sparkles
} from 'lucide-react'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { fetchAdminAnalytics, exportAnalyticsCSV } from '@/lib/adminApi'

const COLORS = ['#d4af37', '#a78bfa', '#34d399', '#f87171', '#60a5fa', '#fb923c']

export default function AdminAnalytics() {
  const { data, isLoading } = useQuery({
    queryKey: ['adminAnalytics'],
    queryFn: fetchAdminAnalytics,
  })

  if (isLoading) return (
    <div className="flex flex-col items-center justify-center h-96 gap-4 text-muted-foreground">
      <Brain size={48} className="opacity-20 animate-pulse" />
      <p className="font-bold animate-pulse luxury-text">جاري تحميل بيانات الذكاء...</p>
    </div>
  )

  const vibeData = data?.quiz_vibe?.labels?.map((label: string, i: number) => ({
    subject: label, value: data.quiz_vibe.data[i] ?? 0,
  })) || []

  const genderData = data?.quiz_gender?.labels?.map((label: string, i: number) => ({
    name: label, value: data.quiz_gender.data[i] ?? 0,
  })) || []

  const apparelData = data?.quiz_apparel?.labels?.map((label: string, i: number) => ({
    name: label, value: data.quiz_apparel.data[i] ?? 0,
  })) || []

  const topRecommended: any[] = data?.top_recommended || []
  const recentLogs: any[] = data?.recent_logs || []

  const totalQuizzes = vibeData.reduce((s: number, d: any) => s + d.value, 0)

  return (
    <div className="space-y-8 pb-10" dir="rtl">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-violet-500/10 border border-violet-500/20">
              <Brain size={22} className="text-violet-400" />
            </div>
            <h1 className="text-3xl font-bold luxury-text">مركز الذكاء التحليلي</h1>
          </div>
          <p className="text-muted-foreground">
            راقب تفضيلات الزوار، حلل الأذواق، واكتشف العطور الأكثر ترشيحاً.
          </p>
        </div>
        <button
          onClick={exportAnalyticsCSV}
          className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500 hover:text-white transition-all font-bold text-sm"
        >
          <Download size={16} /> تصدير التقرير CSV
        </button>
      </header>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'إجمالي الاختبارات', value: totalQuizzes, icon: <Sparkles size={20} />, color: 'from-violet-500 to-purple-500' },
          { label: 'العطور الموصى بها', value: topRecommended.length, icon: <Trophy size={20} />, color: 'from-amber-400 to-orange-500' },
          { label: 'أنواع الـ Vibe', value: vibeData.length, icon: <Target size={20} />, color: 'from-blue-400 to-cyan-500' },
          { label: 'الأنماط المختلفة', value: apparelData.length, icon: <Shirt size={20} />, color: 'from-rose-400 to-pink-500' },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="glass p-5 rounded-3xl border border-border/50 flex items-center gap-4 hover:shadow-xl hover:shadow-primary/5 transition-all"
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

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vibe Radar Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="glass p-7 rounded-3xl border border-border/50"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-violet-500/10"><Target size={18} className="text-violet-400" /></div>
            <div>
              <h3 className="font-bold">التحليل النفسي (Vibe Analysis)</h3>
              <p className="text-xs text-muted-foreground">توزيع أنماط اختيار العطور</p>
            </div>
          </div>
          {vibeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={vibeData}>
                <PolarGrid stroke="var(--border)" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
                />
                <Radar
                  name="Vibe"
                  dataKey="value"
                  stroke="#a78bfa"
                  fill="#a78bfa"
                  fillOpacity={0.25}
                  strokeWidth={2}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--background)',
                    borderColor: 'var(--border)',
                    borderRadius: '12px',
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-muted-foreground">
              <p>لا توجد بيانات بعد</p>
            </div>
          )}
        </motion.div>

        {/* Top Recommended */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.25 }}
          className="glass p-7 rounded-3xl border border-border/50"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-amber-500/10"><Trophy size={18} className="text-amber-400" /></div>
            <div>
              <h3 className="font-bold">العطور الأكثر ترشيحاً</h3>
              <p className="text-xs text-muted-foreground">من نتائج اختبار الخبير العطري</p>
            </div>
          </div>
          <div className="space-y-3">
            {topRecommended.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-muted-foreground gap-3">
                <Bot size={40} className="opacity-20" />
                <p className="text-sm">لا توجد بيانات توصية كافية بعد</p>
              </div>
            ) : topRecommended.map((item: any, i: number) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.05 }}
                className="flex items-center gap-4 p-4 rounded-2xl bg-secondary/20 border border-border/30 hover:bg-secondary/40 transition-all group"
              >
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${
                  i === 0 ? 'bg-amber-400/20 text-amber-400 border border-amber-400/30'
                  : i === 1 ? 'bg-slate-400/20 text-slate-400 border border-slate-400/30'
                  : 'bg-orange-400/20 text-orange-400 border border-orange-400/30'
                }`}>
                  #{i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-sm truncate">{item.name}</p>
                  <p className="text-xs text-muted-foreground">{item.brand}</p>
                </div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-violet-400 bg-violet-500/10 px-3 py-1.5 rounded-full border border-violet-500/20 shrink-0">
                  <Bot size={11} /> {item.recommend_count} مرة
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gender Pie */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass p-7 rounded-3xl border border-border/50"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-rose-500/10"><Users size={18} className="text-rose-400" /></div>
            <div>
              <h3 className="font-bold">التوزيع الديموغرافي</h3>
              <p className="text-xs text-muted-foreground">توزيع الزوار حسب الجنس</p>
            </div>
          </div>
          {genderData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={genderData}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, percent }) => `${name} (${((percent || 0) * 100).toFixed(0)}%)`}
                  labelLine={false}
                >
                  {genderData.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--background)',
                    borderColor: 'var(--border)',
                    borderRadius: '12px',
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-muted-foreground">لا توجد بيانات</div>
          )}
        </motion.div>

        {/* Apparel Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="glass p-7 rounded-3xl border border-border/50"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-sky-500/10"><Shirt size={18} className="text-sky-400" /></div>
            <div>
              <h3 className="font-bold">ستايل الأزياء المفضل</h3>
              <p className="text-xs text-muted-foreground">الأنماط الأكثر شيوعاً في الاختبارات</p>
            </div>
          </div>
          {apparelData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={apparelData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" opacity={0.3} />
                <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} />
                <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} width={70} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--background)',
                    borderColor: 'var(--border)',
                    borderRadius: '12px',
                  }}
                />
                <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                  {apparelData.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-muted-foreground">لا توجد بيانات</div>
          )}
        </motion.div>
      </div>

      {/* Recent Logs Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass rounded-3xl border border-border/50 overflow-hidden"
      >
        <div className="p-6 border-b border-border/50 bg-secondary/30 flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary/10"><Clock size={16} className="text-primary" /></div>
          <div>
            <h3 className="font-bold">سجل التحليلات المباشر</h3>
            <p className="text-xs text-muted-foreground">آخر {recentLogs.length} عملية اختبار</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead>
              <tr className="bg-secondary/20 border-b border-border/30">
                {['التاريخ والوقت', 'الجنس', 'نمط الملابس', 'الـ Vibe', 'المستخدم'].map(h => (
                  <th key={h} className="p-4 text-xs font-bold text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/20">
              {recentLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-16 text-center text-muted-foreground">
                    <Bot size={40} className="mx-auto opacity-20 mb-3" />
                    <p>لا توجد سجلات بعد</p>
                  </td>
                </tr>
              ) : recentLogs.map((log: any, i: number) => (
                <motion.tr
                  key={log.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4 + i * 0.02 }}
                  className="hover:bg-secondary/20 transition-all"
                >
                  <td className="p-4 text-xs text-muted-foreground">
                    {new Date(log.created_at).toLocaleString('ar-SA', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="p-4">
                    <span className="text-xs font-bold px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {log.gender || '—'}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-xs font-bold px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      {log.apparel || '—'}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-xs font-bold px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20">
                      {log.vibe || '—'}
                    </span>
                  </td>
                  <td className="p-4 text-xs text-muted-foreground">
                    {log.user !== 'Guest'
                      ? <span className="font-bold text-foreground">{log.user}</span>
                      : <span className="text-muted-foreground/50">زائر مجهول</span>
                    }
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  )
}
