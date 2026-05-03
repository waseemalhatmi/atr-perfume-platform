import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, Plus, Filter, MoreVertical, Edit2, 
  Trash2, ExternalLink, Image as ImageIcon, 
  ChevronLeft, ChevronRight, X, Check, Eye
} from 'lucide-react'
import { fetchAdminItems, deleteAdminItem, fetchAdminFormMeta } from '@/lib/adminApi'
import toast from 'react-hot-toast'

export default function AdminItems() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data: items, isLoading } = useQuery({
    queryKey: ['adminItems'],
    queryFn: fetchAdminItems
  })

  const deleteMutation = useMutation({
    mutationFn: deleteAdminItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminItems'] })
      toast.success('تم حذف العطر بنجاح')
    },
    onError: () => toast.error('حدث خطأ أثناء الحذف')
  })

  const filteredItems = items?.filter((item: any) => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.brand_name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  const handleDelete = (id: number) => {
    if (window.confirm('هل أنت متأكد من حذف هذا العطر؟')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="space-y-8 pb-10">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold luxury-text">إدارة العطور</h1>
          <p className="text-muted-foreground">عرض وتعديل وإضافة العطور إلى الكتالوج الخاص بك.</p>
        </div>
        <button 
          onClick={() => { setSelectedItem(null); setIsModalOpen(true); }}
          className="luxury-button flex items-center gap-2"
        >
          <Plus size={20} /> إضافة عطر جديد
        </button>
      </header>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4 bg-secondary/30 p-4 rounded-3xl border border-border/50">
        <div className="relative flex-1">
          <Search className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
          <input 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="البحث بالاسم أو البراند..." 
            className="w-full bg-background/50 border border-border/50 rounded-2xl pr-12 pl-4 py-3 outline-none focus:border-primary transition-all" 
          />
        </div>
        <button className="flex items-center gap-2 p-3 px-6 rounded-2xl bg-secondary border border-border/50 hover:bg-secondary/80 transition-all font-bold">
          <Filter size={18} /> تصفية
        </button>
      </div>

      {/* Items Table */}
      <div className="glass rounded-3xl border border-border/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead>
              <tr className="bg-secondary/50 border-b border-border/50">
                <th className="p-6 font-bold text-sm">العطر</th>
                <th className="p-6 font-bold text-sm">التصنيف</th>
                <th className="p-6 font-bold text-sm">الماركة</th>
                <th className="p-6 font-bold text-sm">التفاعل</th>
                <th className="p-6 font-bold text-sm">الحالة</th>
                <th className="p-6 font-bold text-sm">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              <AnimatePresence mode='popLayout'>
                {isLoading ? (
                  <tr><td colSpan={6} className="p-20 text-center luxury-text animate-pulse">جاري جلب العطور...</td></tr>
                ) : filteredItems.map((item: any) => (
                  <motion.tr 
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    key={item.id} 
                    className="hover:bg-secondary/30 transition-all group"
                  >
                    <td className="p-6">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-secondary border border-border/50 overflow-hidden shrink-0">
                          {item.image_url ? (
                            <img src={item.image_url} alt={item.name} className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                              <ImageIcon size={20} />
                            </div>
                          )}
                        </div>
                        <div>
                          <p className="font-bold text-sm">{item.name}</p>
                          <p className="text-xs text-muted-foreground">{item.slug}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-6">
                      <span className="text-xs px-3 py-1 rounded-full bg-secondary border border-border/50">
                        {item.category_name}
                      </span>
                    </td>
                    <td className="p-6 text-sm font-medium">{item.brand_name}</td>
                    <td className="p-6">
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1"><Eye size={12} /> {item.views}</span>
                        <span className="flex items-center gap-1"><Check size={12} /> {item.clicks}</span>
                      </div>
                    </td>
                    <td className="p-6">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50" />
                        <span className="text-xs font-bold text-emerald-500">نشط</span>
                      </div>
                    </td>
                    <td className="p-6">
                      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all">
                        <button 
                          onClick={() => { setSelectedItem(item); setIsModalOpen(true); }}
                          className="p-2 hover:bg-primary hover:text-black rounded-lg transition-all"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button 
                          onClick={() => handleDelete(item.id)}
                          className="p-2 hover:bg-red-500 hover:text-white rounded-lg transition-all"
                        >
                          <Trash2 size={16} />
                        </button>
                        <a href={`/items/${item.id}`} target="_blank" className="p-2 hover:bg-secondary rounded-lg transition-all">
                          <ExternalLink size={16} />
                        </a>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-6 flex justify-between items-center bg-secondary/20 border-t border-border/50">
          <p className="text-xs text-muted-foreground">عرض {filteredItems.length} من أصل {items?.length || 0} عطر</p>
          <div className="flex gap-2">
            <button className="p-2 border border-border/50 rounded-xl hover:bg-secondary disabled:opacity-50" disabled>
              <ChevronRight size={18} />
            </button>
            <button className="p-2 border border-border/50 rounded-xl hover:bg-secondary disabled:opacity-50" disabled>
              <ChevronLeft size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
