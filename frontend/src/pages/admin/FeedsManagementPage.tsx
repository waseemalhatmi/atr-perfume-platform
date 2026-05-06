import { useState, useEffect } from 'react'
import { 
  Rss, RefreshCw, Play, Eye, Plus, 
  Database, AlertCircle, CheckCircle2, 
  Clock, Activity, Info
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { 
  fetchAdminStores, syncAdminStore, createAdminStore, 
  updateAdminStore, fetchAdminStoreSyncLogs, previewAdminFeed,
  StoreAdmin, FeedSyncLog 
} from '@/lib/api'

/** Format an ISO date string to a readable Arabic-friendly format */
const formatDate = (iso: string | null): string => {
  if (!iso) return 'لم تتم بعد'
  try {
    return new Date(iso).toLocaleString('ar-SA', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  } catch {
    return iso
  }
}

export default function FeedsManagementPage() {
  const [stores, setStores] = useState<StoreAdmin[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedStore, setSelectedStore] = useState<StoreAdmin | null>(null)
  const [logs, setLogs] = useState<FeedSyncLog[]>([])
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [previewData, setPreviewData] = useState<{ total_count: number; preview: any[] } | null>(null)
  
  const [formData, setFormData] = useState<Partial<StoreAdmin>>({
    name: '',
    xml_feed_url: '',
    currency: 'SAR',
    country: 'Global',
    is_auto_sync: false
  })

  useEffect(() => {
    loadStores()
  }, [])

  const loadStores = async () => {
    try {
      const data = await fetchAdminStores()
      setStores(data)
    } catch (err) {
      toast.error('فشل في تحميل المتاجر')
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async (id: number) => {
    try {
      toast.loading('جاري بدء المزامنة في الخلفية...', { id: 'sync' })
      await syncAdminStore(id)
      toast.success('بدأت المزامنة بنجاح', { id: 'sync' })
      loadStores()
    } catch (err) {
      toast.error('فشل في تشغيل المزامنة', { id: 'sync' })
    }
  }

  const handlePreview = async (url: string) => {
    if (!url) return toast.error('يرجى إدخال رابط الـ XML أولاً')
    try {
      toast.loading('جاري جلب البيانات للمعاينة...', { id: 'preview' })
      const data = await previewAdminFeed(url)
      setPreviewData(data)
      setIsPreviewOpen(true)
      toast.success('تم جلب المعاينة', { id: 'preview' })
    } catch (err) {
      toast.error('فشل في جلب المعاينة. تأكد من صحة الرابط.', { id: 'preview' })
    }
  }

  const loadLogs = async (id: number) => {
    try {
      const data = await fetchAdminStoreSyncLogs(id)
      setLogs(data)
    } catch (err) {
      toast.error('فشل في تحميل السجلات')
    }
  }

  const handleSaveStore = async () => {
    try {
      if (selectedStore) {
        await updateAdminStore(selectedStore.id, formData)
        toast.success('تم تحديث المتجر')
      } else {
        await createAdminStore(formData)
        toast.success('تم إضافة المتجر بنجاح')
      }
      setIsModalOpen(false)
      loadStores()
    } catch (err) {
      toast.error('حدث خطأ أثناء الحفظ')
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold luxury-text mb-2 flex items-center gap-3">
            <Rss className="text-primary" /> إدارة المزامنة والـ XML
          </h1>
          <p className="text-muted-foreground">تحكم في جلب المنتجات آلياً من Admitad والمتاجر الشريكة.</p>
        </div>
        <button 
          onClick={() => {
            setSelectedStore(null)
            setFormData({ name: '', xml_feed_url: '', currency: 'SAR', country: 'Global', is_auto_sync: false })
            setIsModalOpen(true)
          }}
          className="bg-primary text-black font-bold p-4 px-8 rounded-2xl flex items-center gap-3 shadow-lg shadow-primary/20 hover:scale-105 transition-all"
        >
          <Plus size={20} /> إضافة متجر جديد
        </button>
      </div>

      {/* Stores Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {stores.map((store) => (
          <motion.div 
            key={store.id}
            layout
            className="glass border border-border/50 rounded-3xl p-6 hover:border-primary/30 transition-colors"
          >
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center overflow-hidden border border-border/30">
                  {store.logo_url ? (
                    <img src={store.logo_url} alt={store.name} className="w-full h-full object-contain" />
                  ) : (
                    <Database size={30} className="text-muted-foreground/30" />
                  )}
                </div>
                <div>
                  <h3 className="text-xl font-bold mb-1">{store.name}</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-secondary/50 p-1 px-2 rounded-lg border border-border/50">{store.country}</span>
                    <span className="text-xs bg-primary/10 text-primary p-1 px-2 rounded-lg border border-primary/20">{store.currency}</span>
                  </div>
                </div>
              </div>
              <div className={`p-2 px-4 rounded-xl text-xs font-bold flex items-center gap-2 ${
                store.sync_status === 'success' ? 'bg-green-500/10 text-green-500 border border-green-500/20' :
                store.sync_status === 'running' ? 'bg-blue-500/10 text-blue-500 border border-blue-500/20 animate-pulse' :
                store.sync_status === 'error' ? 'bg-red-500/10 text-red-500 border border-red-500/20' :
                'bg-secondary text-muted-foreground'
              }`}>
                {store.sync_status === 'running' && <RefreshCw size={14} className="animate-spin" />}
                {store.sync_status === 'success' && <CheckCircle2 size={14} />}
                {store.sync_status === 'error' && <AlertCircle size={14} />}
                {store.sync_status === 'idle' && <Clock size={14} />}
                {store.sync_status.toUpperCase()}
              </div>
            </div>

            <div className="space-y-4 mb-8">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground flex items-center gap-2"><Clock size={16} /> آخر مزامنة:</span>
                <span className="font-medium">
                  {store.last_synced_at ? formatDate(store.last_synced_at) : 'لم تتم بعد'}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground flex items-center gap-2"><Activity size={16} /> المزامنة التلقائية:</span>
                <span className={store.is_auto_sync ? 'text-primary font-bold' : 'text-muted-foreground'}>
                  {store.is_auto_sync ? 'مفعّلة (يومياً)' : 'معطّلة'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <button 
                onClick={() => handleSync(store.id)}
                disabled={store.sync_status === 'running'}
                className="p-3 rounded-2xl bg-primary text-black font-bold text-xs flex flex-col items-center gap-2 hover:opacity-90 disabled:opacity-50"
              >
                <Play size={18} /> مزامنة الآن
              </button>
              <button 
                onClick={() => handlePreview(store.xml_feed_url || '')}
                className="p-3 rounded-2xl bg-secondary hover:bg-secondary/80 font-bold text-xs flex flex-col items-center gap-2"
              >
                <Eye size={18} /> معاينة الرابط
              </button>
              <button 
                onClick={() => {
                  setSelectedStore(store)
                  loadLogs(store.id)
                }}
                className="p-3 rounded-2xl bg-secondary hover:bg-secondary/80 font-bold text-xs flex flex-col items-center gap-2"
              >
                <Activity size={18} /> السجلات
              </button>
              <button 
                onClick={() => {
                  setSelectedStore(store)
                  setFormData(store)
                  setIsModalOpen(true)
                }}
                className="p-3 rounded-2xl bg-secondary hover:bg-secondary/80 font-bold text-xs flex flex-col items-center gap-2"
              >
                <Plus size={18} /> تعديل
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Logs Table */}
      <AnimatePresence>
        {selectedStore && !isModalOpen && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="glass border border-border/50 rounded-3xl overflow-hidden"
          >
            <div className="p-6 border-b border-border/50 flex items-center justify-between">
              <h3 className="text-xl font-bold flex items-center gap-3">
                <Activity className="text-primary" /> سجلات المزامنة لـ {selectedStore.name}
              </h3>
              <button onClick={() => setSelectedStore(null)} className="text-sm text-muted-foreground hover:text-foreground">إغلاق</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-right">
                <thead className="bg-secondary/30 text-xs text-muted-foreground">
                  <tr>
                    <th className="p-4">التاريخ</th>
                    <th className="p-4 text-center">الحالة</th>
                    <th className="p-4 text-center">إجمالي المنتجات</th>
                    <th className="p-4 text-center text-green-500">أُضيف</th>
                    <th className="p-4 text-center text-blue-500">حُدّث</th>
                    <th className="p-4 text-center text-red-500">أُخفي</th>
                    <th className="p-4">الملاحظات</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {logs.length > 0 ? logs.map((log) => (
                    <tr key={log.id} className="text-sm hover:bg-secondary/20 transition-colors">
                      <td className="p-4 font-medium whitespace-nowrap">
                        {formatDate(log.started_at)}
                      </td>
                      <td className="p-4 text-center">
                        <span className={`p-1 px-3 rounded-lg text-[10px] font-bold ${
                          log.status === 'success' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
                        }`}>
                          {log.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-4 text-center font-bold">{log.total_found}</td>
                      <td className="p-4 text-center text-green-500 font-bold">+{log.new_added}</td>
                      <td className="p-4 text-center text-blue-500 font-bold">{log.updated}</td>
                      <td className="p-4 text-center text-red-500 font-bold">{log.deactivated}</td>
                      <td className="p-4 text-xs text-muted-foreground truncate max-w-xs" title={log.error_msg || ''}>
                        {log.error_msg || '-'}
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-muted-foreground">لا توجد سجلات بعد لهذا المتجر.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add/Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="glass border border-border/50 rounded-3xl w-full max-w-lg overflow-hidden"
          >
            <div className="p-6 border-b border-border/50">
              <h3 className="text-xl font-bold">{selectedStore ? 'تعديل متجر' : 'إضافة متجر جديد'}</h3>
            </div>
            <div className="p-6 space-y-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-muted-foreground">اسم المتجر</label>
                <input 
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-secondary/50 border border-border/50 rounded-xl p-3 outline-none focus:border-primary transition-all" 
                  placeholder="مثال: AliExpress"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-muted-foreground">رابط XML Feed</label>
                <input 
                  value={formData.xml_feed_url || ''}
                  onChange={(e) => setFormData({...formData, xml_feed_url: e.target.value})}
                  className="w-full bg-secondary/50 border border-border/50 rounded-xl p-3 outline-none focus:border-primary transition-all" 
                  placeholder="https://example.com/feed.xml"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-muted-foreground">الدولة</label>
                  <input 
                    value={formData.country}
                    onChange={(e) => setFormData({...formData, country: e.target.value})}
                    className="w-full bg-secondary/50 border border-border/50 rounded-xl p-3 outline-none focus:border-primary transition-all" 
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-muted-foreground">العملة</label>
                  <input 
                    value={formData.currency}
                    onChange={(e) => setFormData({...formData, currency: e.target.value})}
                    className="w-full bg-secondary/50 border border-border/50 rounded-xl p-3 outline-none focus:border-primary transition-all" 
                  />
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-primary/10 rounded-2xl border border-primary/20">
                <input 
                  type="checkbox"
                  checked={formData.is_auto_sync}
                  onChange={(e) => setFormData({...formData, is_auto_sync: e.target.checked})}
                  id="auto_sync"
                  className="w-5 h-5 accent-primary"
                />
                <label htmlFor="auto_sync" className="text-sm font-bold cursor-pointer">تفعيل المزامنة التلقائية (يومياً)</label>
              </div>
            </div>
            <div className="p-6 bg-secondary/30 flex gap-3">
              <button 
                onClick={handleSaveStore}
                className="flex-1 bg-primary text-black font-bold p-3 rounded-xl hover:opacity-90 transition-all"
              >
                حفظ البيانات
              </button>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="flex-1 bg-secondary font-bold p-3 rounded-xl hover:bg-secondary/80 transition-all"
              >
                إلغاء
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Preview Modal */}
      {isPreviewOpen && previewData && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="glass border border-border/50 rounded-3xl w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col"
          >
            <div className="p-6 border-b border-border/50 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold flex items-center gap-3"><Eye className="text-primary" /> معاينة محتوى الرابط</h3>
                <p className="text-xs text-muted-foreground mt-1">تم العثور على {previewData.total_count} منتج في الرابط.</p>
              </div>
              <button onClick={() => setIsPreviewOpen(false)} className="p-2 hover:bg-secondary rounded-lg transition-all">إغلاق</button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex gap-3">
                <Info className="text-blue-500 flex-shrink-0" />
                <p className="text-xs text-blue-500/80 leading-relaxed">هذه عينة من أول 10 منتجات موجودة في الملف حالياً. المزامنة الفعلية ستشمل كافة المنتجات المطابقة لقواعد الفلترة.</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {previewData.preview.map((p, idx) => (
                  <div key={idx} className="p-4 bg-secondary/20 rounded-2xl border border-border/30 flex gap-4">
                    <img src={p.image_url} alt={p.name} className="w-16 h-16 object-contain bg-white rounded-lg p-1" />
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-bold truncate">{p.name}</h4>
                      <p className="text-[10px] text-muted-foreground">{p.brand} | {p.external_id}</p>
                      <div className="mt-2 flex items-center gap-2">
                        <span className="text-primary font-bold">{p.price} {p.currency}</span>
                        {p.old_price && <span className="text-[10px] text-muted-foreground line-through">{p.old_price}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-6 bg-secondary/30">
              <button 
                onClick={() => setIsPreviewOpen(false)}
                className="w-full bg-primary text-black font-bold p-4 rounded-2xl hover:opacity-90"
              >
                فهمت، إغلاق المعاينة
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
