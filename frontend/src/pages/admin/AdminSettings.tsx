import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Settings, Tag, Grid3X3, Save,
  Plus, Trash2, Check, X, Loader2,
  Palette, Globe, Type, Info
} from 'lucide-react'
import {
  fetchAdminBrands, addAdminBrand, deleteAdminBrand,
  fetchAdminCategories, addAdminCategory, deleteAdminCategory,
  fetchAdminSettings, updateAdminSettings
} from '@/lib/adminApi'
import toast from 'react-hot-toast'

function TagManager({
  title, icon, color, items, onAdd, onDelete, isLoading
}: {
  title: string, icon: React.ReactNode, color: string,
  items: any[], onAdd: (name: string) => void,
  onDelete: (id: number) => void, isLoading: boolean
}) {
  const [input, setInput] = useState('')

  const handleAdd = () => {
    const trimmed = input.trim()
    if (!trimmed) return
    onAdd(trimmed)
    setInput('')
  }

  return (
    <div className="glass p-7 rounded-3xl border border-border/50 space-y-5">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-xl ${color}`}>{icon}</div>
        <div>
          <h3 className="font-bold">{title}</h3>
          <p className="text-xs text-muted-foreground">{items.length} عنصر مضاف</p>
        </div>
      </div>

      {/* Add input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAdd()}
          placeholder={`إضافة ${title} جديد...`}
          className="flex-1 bg-secondary/30 border border-border/50 rounded-2xl px-4 py-2.5 text-sm outline-none focus:border-primary/50 transition-all"
        />
        <button
          onClick={handleAdd}
          disabled={!input.trim()}
          className="p-2.5 rounded-2xl bg-primary text-black hover:opacity-90 transition-all disabled:opacity-40"
        >
          <Plus size={18} />
        </button>
      </div>

      {/* Items */}
      <div className="flex flex-wrap gap-2 min-h-[60px]">
        {isLoading ? (
          [...Array(4)].map((_, i) => (
            <div key={i} className="h-8 w-24 rounded-full bg-secondary/60 animate-pulse" />
          ))
        ) : items.length === 0 ? (
          <p className="text-xs text-muted-foreground self-center">لا توجد عناصر بعد</p>
        ) : (
          <AnimatePresence>
            {items.map((item: any) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="group flex items-center gap-2 px-3 py-1.5 rounded-full border border-border/50 bg-secondary/30 hover:border-red-500/30 hover:bg-red-500/5 transition-all text-sm"
              >
                <span className="font-medium">{item.name}</span>
                <button
                  onClick={() => onDelete(item.id)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity text-red-500 hover:scale-110"
                >
                  <X size={13} />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  )
}

export default function AdminSettings() {
  const queryClient = useQueryClient()

  // Brands
  const { data: brands = [], isLoading: brandsLoading } = useQuery({
    queryKey: ['adminBrands'], queryFn: fetchAdminBrands
  })
  const addBrand = useMutation({
    mutationFn: addAdminBrand,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['adminBrands'] }); toast.success('تم إضافة البراند') },
    onError: () => toast.error('فشل في الإضافة')
  })
  const deleteBrand = useMutation({
    mutationFn: deleteAdminBrand,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['adminBrands'] }); toast.success('تم الحذف') },
    onError: () => toast.error('لا يمكن حذف براند مرتبط بعطور')
  })

  // Categories
  const { data: categories = [], isLoading: catsLoading } = useQuery({
    queryKey: ['adminCategories'], queryFn: fetchAdminCategories
  })
  const addCategory = useMutation({
    mutationFn: addAdminCategory,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['adminCategories'] }); toast.success('تم إضافة التصنيف') },
    onError: () => toast.error('فشل في الإضافة')
  })
  const deleteCategory = useMutation({
    mutationFn: deleteAdminCategory,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['adminCategories'] }); toast.success('تم الحذف') },
    onError: () => toast.error('لا يمكن حذف تصنيف مرتبط بعطور')
  })

  // Site Settings
  const { data: settingsArr = [] } = useQuery({
    queryKey: ['adminSettings'], queryFn: fetchAdminSettings
  })
  const [settingsForm, setSettingsForm] = useState<Record<string, string>>({})
  const [settingsDirty, setSettingsDirty] = useState(false)

  const settingsData = settingsArr as any[]
  const getVal = (key: string) =>
    settingsForm[key] ?? settingsData.find((s: any) => s.key === key)?.value ?? ''

  const handleSettingChange = (key: string, val: string) => {
    setSettingsForm(prev => ({ ...prev, [key]: val }))
    setSettingsDirty(true)
  }

  const updateSettings = useMutation({
    mutationFn: updateAdminSettings,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['adminSettings'] }); toast.success('تم حفظ الإعدادات'); setSettingsDirty(false) },
    onError: () => toast.error('فشل في الحفظ')
  })

  const SETTING_FIELDS = [
    { key: 'site_name', label: 'اسم الموقع', icon: <Type size={16} />, placeholder: 'مثال: عطري' },
    { key: 'site_description', label: 'وصف الموقع', icon: <Info size={16} />, placeholder: 'وصف مختصر للموقع...', multiline: true },
    { key: 'site_color', label: 'اللون الرئيسي', icon: <Palette size={16} />, placeholder: '#d4af37', type: 'color' },
    { key: 'site_language', label: 'اللغة الافتراضية', icon: <Globe size={16} />, placeholder: 'ar' },
  ]

  return (
    <div className="space-y-8 pb-10" dir="rtl">
      {/* Header */}
      <header>
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-primary/10 border border-primary/20">
            <Settings size={22} className="text-primary" />
          </div>
          <h1 className="text-3xl font-bold luxury-text">الإعدادات العامة</h1>
        </div>
        <p className="text-muted-foreground">إدارة البراندات والتصنيفات وإعدادات الموقع.</p>
      </header>

      {/* Brands & Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TagManager
          title="الماركات (Brands)"
          icon={<Tag size={18} className="text-amber-400" />}
          color="bg-amber-500/10"
          items={brands as any[]}
          isLoading={brandsLoading}
          onAdd={(name) => addBrand.mutate(name)}
          onDelete={(id) => deleteBrand.mutate(id)}
        />
        <TagManager
          title="التصنيفات (Categories)"
          icon={<Grid3X3 size={18} className="text-blue-400" />}
          color="bg-blue-500/10"
          items={categories as any[]}
          isLoading={catsLoading}
          onAdd={(name) => addCategory.mutate(name)}
          onDelete={(id) => deleteCategory.mutate(id)}
        />
      </div>

      {/* Site Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass p-7 rounded-3xl border border-border/50 space-y-6"
      >
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10">
              <Settings size={18} className="text-primary" />
            </div>
            <div>
              <h3 className="font-bold">إعدادات الموقع</h3>
              <p className="text-xs text-muted-foreground">البيانات الأساسية للمنصة</p>
            </div>
          </div>
          <button
            onClick={() => updateSettings.mutate(settingsForm)}
            disabled={!settingsDirty || updateSettings.isPending}
            className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-primary text-black font-bold text-sm hover:opacity-90 transition-all disabled:opacity-40"
          >
            {updateSettings.isPending
              ? <Loader2 size={16} className="animate-spin" />
              : <Save size={16} />}
            حفظ التغييرات
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {SETTING_FIELDS.map(field => (
            <div key={field.key} className="space-y-2">
              <label className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                {field.icon} {field.label}
              </label>
              {field.type === 'color' ? (
                <div className="flex items-center gap-3">
                  <input
                    type="color"
                    value={getVal(field.key) || '#d4af37'}
                    onChange={e => handleSettingChange(field.key, e.target.value)}
                    className="w-12 h-12 rounded-xl border border-border/50 cursor-pointer bg-transparent"
                  />
                  <input
                    type="text"
                    value={getVal(field.key)}
                    onChange={e => handleSettingChange(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    className="flex-1 bg-secondary/30 border border-border/50 rounded-2xl px-4 py-3 text-sm outline-none focus:border-primary/50 transition-all font-mono"
                  />
                </div>
              ) : field.multiline ? (
                <textarea
                  value={getVal(field.key)}
                  onChange={e => handleSettingChange(field.key, e.target.value)}
                  placeholder={field.placeholder}
                  rows={3}
                  className="w-full bg-secondary/30 border border-border/50 rounded-2xl px-4 py-3 text-sm outline-none focus:border-primary/50 transition-all resize-none"
                />
              ) : (
                <input
                  type="text"
                  value={getVal(field.key)}
                  onChange={e => handleSettingChange(field.key, e.target.value)}
                  placeholder={field.placeholder}
                  className="w-full bg-secondary/30 border border-border/50 rounded-2xl px-4 py-3 text-sm outline-none focus:border-primary/50 transition-all"
                />
              )}
            </div>
          ))}
        </div>

        {settingsDirty && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 text-xs text-amber-500 bg-amber-500/10 px-4 py-3 rounded-2xl border border-amber-500/20"
          >
            <Info size={14} /> لديك تغييرات غير محفوظة — انقر "حفظ" لتطبيقها.
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
