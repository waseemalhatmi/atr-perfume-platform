// TODO: connect this component in future admin UI
import { useState, useEffect } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { X, Upload, Save, AlertCircle } from 'lucide-react'
import { addAdminItem, updateAdminItem, fetchAdminFormMeta } from '@/lib/adminApi'
import toast from 'react-hot-toast'

interface ModalProps {
  item?: any
  isOpen: boolean
  onClose: () => void
}

export default function AdminItemModal({ item, isOpen, onClose }: ModalProps) {
  const queryClient = useQueryClient()
  const { data: meta } = useQuery({ queryKey: ['adminFormMeta'], queryFn: fetchAdminFormMeta })

  const [formData, setFormData] = useState({
    name: '',
    brand_id: '',
    category_id: '',
    description: '',
    price: '',
    stock: '',
    is_active: true
  })
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  useEffect(() => {
    if (item) {
      setFormData({
        name: item.name || '',
        brand_id: item.brand_id || '',
        category_id: item.category_id || '',
        description: item.description || '',
        price: item.price || '',
        stock: item.stock || '',
        is_active: item.is_active ?? true
      })
      setPreview(item.image_url || null)
    } else {
      setFormData({ name: '', brand_id: '', category_id: '', description: '', price: '', stock: '', is_active: true })
      setPreview(null)
    }
  }, [item, isOpen])

  const mutation = useMutation({
    mutationFn: (data: FormData) => item ? updateAdminItem(item.id, data) : addAdminItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminItems'] })
      toast.success(item ? 'تم تحديث العطر بنجاح' : 'تم إضافة العطر بنجاح')
      onClose()
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error || 'حدث خطأ ما')
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data = new FormData()
    Object.entries(formData).forEach(([key, value]) => data.append(key, String(value)))
    if (imageFile) data.append('image', imageFile)
    mutation.mutate(data)
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setImageFile(file)
      setPreview(URL.createObjectURL(file))
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col rounded-3xl border border-border/50"
      >
        <header className="p-6 border-b border-border/50 flex justify-between items-center bg-secondary/30">
          <h2 className="text-xl font-bold luxury-text">{item ? 'تعديل العطر' : 'إضافة عطر جديد'}</h2>
          <button onClick={onClose} className="p-2 hover:bg-secondary rounded-xl transition-all"><X size={20}/></button>
        </header>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Left side: Image Upload */}
            <div className="space-y-4">
              <label className="block text-sm font-bold mb-2">صورة العطر</label>
              <div 
                className="aspect-[3/4] rounded-3xl border-2 border-dashed border-border/50 bg-secondary/20 flex flex-col items-center justify-center relative overflow-hidden group cursor-pointer"
                onClick={() => document.getElementById('image-upload')?.click()}
              >
                {preview ? (
                  <img src={preview} alt="Preview" className="w-full h-full object-cover" />
                ) : (
                  <div className="text-center p-6">
                    <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center mx-auto mb-4">
                      <Upload size={32} className="text-primary" />
                    </div>
                    <p className="text-sm font-bold">اضغط لرفع الصورة</p>
                    <p className="text-xs text-muted-foreground mt-2">JPG, PNG أو WebP (بحد أقصى 5MB)</p>
                  </div>
                )}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <span className="text-white text-sm font-bold bg-primary/20 backdrop-blur-md px-4 py-2 rounded-xl">تغيير الصورة</span>
                </div>
              </div>
              <input type="file" id="image-upload" className="hidden" accept="image/*" onChange={handleImageChange} />
            </div>

            {/* Right side: Form Fields */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold mb-2">اسم العطر</label>
                <input 
                  required
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all"
                  placeholder="مثال: كريد أفينتوس"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold mb-2">الماركة</label>
                  <select 
                    required
                    value={formData.brand_id}
                    onChange={e => setFormData({...formData, brand_id: e.target.value})}
                    className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all"
                  >
                    <option value="">اختر الماركة</option>
                    {meta?.brands.map((b: any) => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold mb-2">التصنيف</label>
                  <select 
                    required
                    value={formData.category_id}
                    onChange={e => setFormData({...formData, category_id: e.target.value})}
                    className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all"
                  >
                    <option value="">اختر التصنيف</option>
                    {meta?.categories.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold mb-2">السعر التقريبي</label>
                  <input 
                    type="number"
                    value={formData.price}
                    onChange={e => setFormData({...formData, price: e.target.value})}
                    className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold mb-2">الحالة</label>
                  <select 
                    value={String(formData.is_active)}
                    onChange={e => setFormData({...formData, is_active: e.target.value === 'true'})}
                    className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all"
                  >
                    <option value="true">نشط</option>
                    <option value="false">مسودة</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold mb-2">الوصف</label>
                <textarea 
                  rows={4}
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all resize-none"
                  placeholder="اكتب وصفاً تفصيلياً للعطر..."
                />
              </div>
            </div>
          </div>
        </form>

        <footer className="p-6 border-t border-border/50 bg-secondary/30 flex justify-end gap-4">
          <button onClick={onClose} className="px-6 py-3 rounded-2xl hover:bg-secondary transition-all font-bold">إلغاء</button>
          <button 
            onClick={handleSubmit}
            disabled={mutation.isPending}
            className="luxury-button flex items-center gap-2 min-w-[140px] justify-center"
          >
            {mutation.isPending ? 'جاري الحفظ...' : (
              <>
                <Save size={18} /> {item ? 'حفظ التعديلات' : 'إضافة العطر'}
              </>
            )}
          </button>
        </footer>
      </motion.div>
    </div>
  )
}
