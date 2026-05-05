import { useState, useEffect } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Upload, Save, Plus, Trash2 } from 'lucide-react'
import { addAdminItem, updateAdminItem, fetchAdminFormMeta, fetchAdminItem } from '@/lib/adminApi'
import toast from 'react-hot-toast'

interface ModalProps {
  item?: any
  isOpen: boolean
  onClose: () => void
}

export default function AdminItemModal({ item, isOpen, onClose }: ModalProps) {
  const queryClient = useQueryClient()
  const { data: meta } = useQuery({ queryKey: ['adminFormMeta'], queryFn: fetchAdminFormMeta })

  const [activeTab, setActiveTab] = useState<'basics' | 'variants' | 'specs'>('basics')
  
  // Basic info state
  const [formData, setFormData] = useState({
    name: '',
    brand_id: '',
    category_id: '',
    description: '',
  })
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  // Advanced data state
  const [variants, setVariants] = useState<any[]>([])
  const [specs, setSpecs] = useState<any>({ 'مكونات العطر': { 'القمة': '', 'القلب': '', 'القاعدة': '' } })
  const [isLoadingFullItem, setIsLoadingFullItem] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setActiveTab('basics')
      if (item) {
        // We have a selected item (basic details from list), fetch full details
        setIsLoadingFullItem(true)
        fetchAdminItem(item.id).then(fullItem => {
          setFormData({
            name: fullItem.name || '',
            brand_id: fullItem.brand_id || '',
            category_id: fullItem.category_id || '',
            description: fullItem.description || '',
          })
          setPreview(fullItem.image_url || null)
          setVariants(fullItem.variants || [])
          
          const dbSpecs = fullItem.specifications || {}
          setSpecs({
            'مكونات العطر': {
              'القمة': dbSpecs['مكونات العطر']?.['القمة'] || '',
              'القلب': dbSpecs['مكونات العطر']?.['القلب'] || '',
              'القاعدة': dbSpecs['مكونات العطر']?.['القاعدة'] || ''
            }
          })
          setIsLoadingFullItem(false)
        }).catch(() => {
          toast.error("فشل جلب تفاصيل العطر كاملة")
          setIsLoadingFullItem(false)
        })
      } else {
        // Reset for new item
        setFormData({ name: '', brand_id: '', category_id: '', description: '' })
        setPreview(null)
        setImageFile(null)
        setVariants([])
        setSpecs({ 'مكونات العطر': { 'القمة': '', 'القلب': '', 'القاعدة': '' } })
      }
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
    if (!formData.name || !formData.brand_id || !formData.category_id) {
      toast.error("الاسم، الماركة، والتصنيف حقول مطلوبة")
      return
    }

    const data = new FormData()
    Object.entries(formData).forEach(([key, value]) => data.append(key, String(value)))
    if (imageFile) data.append('image', imageFile)
    
    // Add advanced data (variants, links, specs) as JSON string
    const advancedData = {
      variants,
      specifications: specs
    }
    data.append('advanced_data', JSON.stringify(advancedData))

    mutation.mutate(data)
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setImageFile(file)
      setPreview(URL.createObjectURL(file))
    }
  }

  // Add a new empty variant
  const addVariant = () => {
    setVariants([...variants, {
      title: '', sku: '', attributes: { 'حجم': '100ml' }, is_default: variants.length === 0, store_links: []
    }])
  }

  // Remove a variant
  const removeVariant = (index: number) => {
    setVariants(variants.filter((_, i) => i !== index))
  }

  // Add store link to variant
  const addStoreLink = (variantIndex: number) => {
    const newVariants = [...variants]
    newVariants[variantIndex].store_links.push({
      store_id: '', affiliate_url: '', price: '', currency: 'USD', is_active: true
    })
    setVariants(newVariants)
  }

  // Remove store link
  const removeStoreLink = (variantIndex: number, linkIndex: number) => {
    const newVariants = [...variants]
    newVariants[variantIndex].store_links = newVariants[variantIndex].store_links.filter((_: any, i: number) => i !== linkIndex)
    setVariants(newVariants)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass w-full max-w-5xl h-[90vh] overflow-hidden flex flex-col rounded-3xl border border-border/50"
      >
        <header className="p-6 border-b border-border/50 flex justify-between items-center bg-secondary/30 shrink-0">
          <div className="flex items-center gap-6">
            <h2 className="text-xl font-bold luxury-text">{item ? 'تعديل بيانات العطر' : 'إضافة عطر احترافي'}</h2>
            
            {/* Tabs */}
            <div className="flex bg-secondary/50 rounded-xl p-1 border border-border/50 hidden md:flex">
              <button 
                onClick={(e) => { e.preventDefault(); setActiveTab('basics'); }}
                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'basics' ? 'bg-primary text-black shadow-lg shadow-primary/20' : 'text-muted-foreground hover:text-white'}`}
              >
                المعلومات الأساسية
              </button>
              <button 
                onClick={(e) => { e.preventDefault(); setActiveTab('variants'); }}
                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'variants' ? 'bg-primary text-black shadow-lg shadow-primary/20' : 'text-muted-foreground hover:text-white'}`}
              >
                الأحجام والمتاجر
              </button>
              <button 
                onClick={(e) => { e.preventDefault(); setActiveTab('specs'); }}
                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'specs' ? 'bg-primary text-black shadow-lg shadow-primary/20' : 'text-muted-foreground hover:text-white'}`}
              >
                المكونات العطرية
              </button>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-secondary rounded-xl transition-all"><X size={20}/></button>
        </header>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto bg-black/20">
          {isLoadingFullItem ? (
            <div className="h-full flex items-center justify-center text-muted-foreground animate-pulse">
              جاري جلب تفاصيل العطر...
            </div>
          ) : (
            <div className="p-8">
              
              {/* TAB 1: Basics */}
              <div style={{ display: activeTab === 'basics' ? 'block' : 'none' }}>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Left side: Image Upload */}
                  <div className="space-y-4 lg:col-span-1">
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
                        </div>
                      )}
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <span className="text-white text-sm font-bold bg-primary/20 backdrop-blur-md px-4 py-2 rounded-xl">تغيير الصورة</span>
                      </div>
                    </div>
                    <input type="file" id="image-upload" className="hidden" accept="image/*" onChange={handleImageChange} />
                  </div>

                  {/* Right side: Basic Fields */}
                  <div className="space-y-6 lg:col-span-2">
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

                    <div>
                      <label className="block text-sm font-bold mb-2">وصف العطر</label>
                      <textarea 
                        rows={6}
                        value={formData.description}
                        onChange={e => setFormData({...formData, description: e.target.value})}
                        className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all resize-none leading-relaxed"
                        placeholder="اكتب وصفاً تفصيلياً للعطر..."
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* TAB 2: Variants & Stores */}
              <div style={{ display: activeTab === 'variants' ? 'block' : 'none' }} className="space-y-8">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-bold">الأحجام وروابط المتاجر</h3>
                  <button type="button" onClick={addVariant} className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-xl hover:bg-secondary/80 text-sm font-bold">
                    <Plus size={16} /> إضافة حجم / نسخة
                  </button>
                </div>

                {variants.length === 0 ? (
                  <div className="p-12 text-center bg-secondary/20 rounded-3xl border border-border/50 border-dashed text-muted-foreground">
                    لم تتم إضافة أي أحجام بعد. أضف الحجم الأول ثم أضف المتاجر التي يتوفر بها.
                  </div>
                ) : (
                  variants.map((variant, vIdx) => (
                    <div key={vIdx} className="p-6 bg-secondary/10 rounded-3xl border border-border/50 space-y-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 grid grid-cols-3 gap-4">
                          <div>
                            <label className="block text-xs font-bold mb-1 text-muted-foreground">اسم النسخة (اختياري)</label>
                            <input 
                              value={variant.title || ''}
                              onChange={e => { const nv = [...variants]; nv[vIdx].title = e.target.value; setVariants(nv); }}
                              className="w-full bg-background border border-border/50 rounded-xl px-3 py-2 text-sm outline-none focus:border-primary"
                              placeholder="مثال: إصدار محدود"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-bold mb-1 text-muted-foreground">الحجم (مل)</label>
                            <input 
                              value={variant.attributes?.['حجم'] || ''}
                              onChange={e => { 
                                const nv = [...variants]; 
                                nv[vIdx].attributes = { ...nv[vIdx].attributes, 'حجم': e.target.value }; 
                                setVariants(nv); 
                              }}
                              className="w-full bg-background border border-border/50 rounded-xl px-3 py-2 text-sm outline-none focus:border-primary text-left"
                              dir="ltr"
                              placeholder="100ml"
                            />
                          </div>
                          <div className="flex items-end gap-2">
                            <label className="flex items-center gap-2 h-[38px] px-3 bg-background border border-border/50 rounded-xl text-sm cursor-pointer w-full">
                              <input 
                                type="radio" 
                                name="default_variant" 
                                checked={variant.is_default}
                                onChange={() => {
                                  const nv = [...variants].map(v => ({ ...v, is_default: false }));
                                  nv[vIdx].is_default = true;
                                  setVariants(nv);
                                }}
                                className="accent-primary"
                              />
                              النسخة الافتراضية
                            </label>
                          </div>
                        </div>
                        <button type="button" onClick={() => removeVariant(vIdx)} className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg">
                          <Trash2 size={18} />
                        </button>
                      </div>

                      {/* Store Links within Variant */}
                      <div className="pl-4 md:pl-10 space-y-4 border-r-2 border-primary/20">
                        <div className="flex justify-between items-center">
                          <h4 className="text-sm font-bold text-muted-foreground">روابط المتاجر لهذا الحجم:</h4>
                          <button type="button" onClick={() => addStoreLink(vIdx)} className="text-xs flex items-center gap-1 text-primary hover:text-primary/80">
                            <Plus size={14} /> إضافة متجر
                          </button>
                        </div>
                        
                        {variant.store_links.length === 0 ? (
                          <div className="text-xs text-muted-foreground p-4 bg-background/50 rounded-xl">لا توجد متاجر مرتبطة بهذا الحجم.</div>
                        ) : (
                          <div className="space-y-2">
                            {variant.store_links.map((link: any, lIdx: number) => (
                              <div key={lIdx} className="flex flex-wrap md:flex-nowrap gap-2 bg-background/50 p-2 rounded-xl border border-border/30 items-center">
                                <select 
                                  value={link.store_id}
                                  onChange={e => { const nv = [...variants]; nv[vIdx].store_links[lIdx].store_id = e.target.value; setVariants(nv); }}
                                  className="bg-transparent border border-border/50 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-primary flex-1 min-w-[100px]"
                                >
                                  <option value="">المتجر...</option>
                                  {meta?.stores?.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                                </select>
                                <input 
                                  value={link.price}
                                  onChange={e => { const nv = [...variants]; nv[vIdx].store_links[lIdx].price = e.target.value; setVariants(nv); }}
                                  type="number"
                                  placeholder="السعر"
                                  className="bg-transparent border border-border/50 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-primary w-[80px]"
                                />
                                <select 
                                  value={link.currency}
                                  onChange={e => { const nv = [...variants]; nv[vIdx].store_links[lIdx].currency = e.target.value; setVariants(nv); }}
                                  className="bg-transparent border border-border/50 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-primary w-[70px]"
                                >
                                  <option value="SAR">SAR</option>
                                  <option value="AED">AED</option>
                                  <option value="USD">USD</option>
                                </select>
                                <input 
                                  value={link.affiliate_url}
                                  onChange={e => { const nv = [...variants]; nv[vIdx].store_links[lIdx].affiliate_url = e.target.value; setVariants(nv); }}
                                  placeholder="رابط الشراء (URL)"
                                  className="bg-transparent border border-border/50 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-primary flex-[2] min-w-[200px]"
                                  dir="ltr"
                                />
                                <button type="button" onClick={() => removeStoreLink(vIdx, lIdx)} className="p-1.5 text-red-400 hover:bg-red-500/20 rounded-md">
                                  <X size={14} />
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* TAB 3: Specs */}
              <div style={{ display: activeTab === 'specs' ? 'block' : 'none' }}>
                <div className="max-w-2xl space-y-6">
                  <h3 className="text-xl font-bold mb-6">المكونات العطرية (الهرم العطري)</h3>
                  
                  <div>
                    <label className="block text-sm font-bold mb-2 text-primary">القمة (Top Notes)</label>
                    <input 
                      value={specs['مكونات العطر']?.['القمة'] || ''}
                      onChange={e => setSpecs({...specs, 'مكونات العطر': {...specs['مكونات العطر'], 'القمة': e.target.value}})}
                      className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all"
                      placeholder="مثال: البرغموت، الليمون، الفلفل الوردي"
                    />
                    <p className="text-xs text-muted-foreground mt-1">الرائحة التي تظهر فور رش العطر وتدوم لـ 15 دقيقة.</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-bold mb-2 text-primary">القلب (Heart Notes)</label>
                    <input 
                      value={specs['مكونات العطر']?.['القلب'] || ''}
                      onChange={e => setSpecs({...specs, 'مكونات العطر': {...specs['مكونات العطر'], 'القلب': e.target.value}})}
                      className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all"
                      placeholder="مثال: الياسمين، الورد، زنبق الوادي"
                    />
                    <p className="text-xs text-muted-foreground mt-1">قلب العطر وشخصيته الأساسية، تدوم لعدة ساعات.</p>
                  </div>

                  <div>
                    <label className="block text-sm font-bold mb-2 text-primary">القاعدة (Base Notes)</label>
                    <input 
                      value={specs['مكونات العطر']?.['القاعدة'] || ''}
                      onChange={e => setSpecs({...specs, 'مكونات العطر': {...specs['مكونات العطر'], 'القاعدة': e.target.value}})}
                      className="w-full bg-secondary/50 border border-border/50 rounded-2xl px-4 py-3 outline-none focus:border-primary transition-all"
                      placeholder="مثال: خشب الصندل، المسك، الفانيليا، العود"
                    />
                    <p className="text-xs text-muted-foreground mt-1">أساس العطر الذي يثبت على الجلد لآخر اليوم.</p>
                  </div>
                </div>
              </div>

            </div>
          )}
        </form>

        <footer className="p-6 border-t border-border/50 bg-secondary/30 flex justify-between shrink-0">
          <div className="md:hidden flex gap-2">
            {/* Mobile Tab Nav */}
            <select 
              value={activeTab} 
              onChange={e => setActiveTab(e.target.value as any)}
              className="bg-secondary border border-border/50 rounded-xl px-4 py-2 font-bold outline-none"
            >
              <option value="basics">الأساسيات</option>
              <option value="variants">الأحجام والمتاجر</option>
              <option value="specs">المكونات</option>
            </select>
          </div>
          <div className="flex gap-4 ml-auto">
            <button type="button" onClick={onClose} className="px-6 py-3 rounded-2xl hover:bg-secondary transition-all font-bold">إلغاء</button>
            <button 
              onClick={handleSubmit}
              disabled={mutation.isPending || isLoadingFullItem}
              className="luxury-button flex items-center gap-2 min-w-[140px] justify-center"
            >
              {mutation.isPending ? 'جاري الحفظ...' : (
                <>
                  <Save size={18} /> {item ? 'حفظ التعديلات الشاملة' : 'اعتماد العطر والنشر'}
                </>
              )}
            </button>
          </div>
        </footer>
      </motion.div>
    </div>
  )
}
