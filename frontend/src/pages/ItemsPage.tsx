import React, { useState, useCallback, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { SlidersHorizontal, X, LayoutGrid, List, ChevronRight, ChevronLeft, Zap } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { fetchItems, fetchFilters } from '@/lib/api'
import ItemCard from '@/components/ItemCard'
import SkeletonCard from '@/components/SkeletonCard'
import FilterContent from '@/components/filters/FilterContent'
import SEO from '@/components/SEO'
import { useProfileData } from '@/hooks/useProfileData'

// Fix #2: Professional Pagination Helper
const getPaginationRange = (current: number, total: number) => {
  const delta = 2;
  const range = [];
  const rangeWithDots = [];
  let l;

  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || i >= current - delta && i <= current + delta) {
      range.push(i);
    }
  }

  for (let i of range) {
    if (l) {
      if (i - l === 2) {
        rangeWithDots.push(l + 1);
      } else if (i - l !== 1) {
        rangeWithDots.push('...');
      }
    }
    rangeWithDots.push(i);
    l = i;
  }

  return rangeWithDots;
};

export default function ItemsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [sidebarOpen, setSidebar] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const page = Number(searchParams.get('page') || '1')
  const rawSort = searchParams.get('sort') || 'newest'
  const supportedSorts = ['newest', 'popular', 'price_asc', 'price_desc']
  const sortBy = supportedSorts.includes(rawSort) ? rawSort : 'newest'
  const categories = searchParams.getAll('category')
  const brands = searchParams.getAll('brand')

  const { data, isLoading: itemsLoading } = useQuery({
    queryKey: ['items', page, sortBy, categories.join(), brands.join()],
    queryFn: () => fetchItems({
      page, sort: sortBy,
      category: categories,
      brand: brands,
      per_page: 12,
    }),
  })

  const { savedSet, alertSet, isLoading: profileLoading } = useProfileData()
  const isLoading = itemsLoading || profileLoading

  const { data: filters } = useQuery({
    queryKey: ['filters'],
    queryFn: fetchFilters,
    staleTime: Infinity,
  })

  const setParam = useCallback((key: string, values: string[]) => {
    const next = new URLSearchParams(searchParams)
    next.delete(key)
    values.forEach((v) => next.append(key, v))
    next.set('page', '1')
    setSearchParams(next)
  }, [searchParams, setSearchParams])

  const toggleFilter = (key: 'category' | 'brand', val: string) => {
    const current = searchParams.getAll(key)
    if (current.includes(val)) setParam(key, current.filter((v) => v !== val))
    else setParam(key, [...current, val])
  }

  // Fix #1: FilterContent is now a separate React.memo component
  // to avoid large useMemo closures and re-mounts.

  return (
    <div className="container-px py-12">
      <SEO
        title="مجموعة العطور | منصة عطري"
        description="تصفح مجموعتنا الفاخرة من العطور العالمية والنيش، ابحث وقارن واختر العطر الأنسب لك."
      />
      {/* Header & Toolbar */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
        <div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">اكتشف <span className="luxury-text">المجموعات</span></h1>
          <p className="text-muted-foreground">تصفح أرقى العطور المختارة بعناية من حول العالم.</p>
        </div>

        <div className="flex items-center gap-3 glass p-2 rounded-2xl">
          <select
            value={sortBy}
            onChange={(e) => { const n = new URLSearchParams(searchParams); n.set('sort', e.target.value); n.set('page', '1'); setSearchParams(n) }}
            className="bg-transparent text-sm font-bold px-4 py-2 outline-none cursor-pointer"
          >
            <option value="newest">الأحدث وصولاً</option>
            <option value="popular">الأكثر رواجاً</option>
            <option value="price_asc">الأقل سعراً</option>
            <option value="price_desc">الأعلى سعراً</option>
          </select>

          <div className="w-px h-6 bg-border mx-2" />

          <button type="button" onClick={() => setViewMode('grid')} aria-label="عرض شبكي" className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-primary text-black shadow-sm' : 'hover:bg-secondary'}`}>
            <LayoutGrid size={18} />
          </button>
          <button type="button" onClick={() => setViewMode('list')} aria-label="عرض قائمة" className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-primary text-black shadow-sm' : 'hover:bg-secondary'}`}>
            <List size={18} />
          </button>

          <button type="button" onClick={() => setSidebar(true)} aria-label="فتح الفلاتر" className="lg:hidden flex items-center gap-2 px-4 py-2 bg-primary text-black rounded-xl font-bold text-sm">
            <SlidersHorizontal size={16} /> فلتر
          </button>
        </div>
      </div>

      <div className="flex gap-12">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:block w-72 flex-shrink-0">
          <div className="sticky top-24 space-y-10">
            <FilterContent categories={categories} brands={brands} filters={filters} toggleFilter={toggleFilter} />

            {/* Promo Card */}
            <div className="p-6 rounded-3xl bg-luxury-gradient text-black relative overflow-hidden">
              <Zap className="absolute -bottom-4 -right-4 w-24 h-24 opacity-20" />
              <h4 className="font-bold mb-2">عرض محدود!</h4>
              <p className="text-xs mb-4 opacity-80">احصل على خصم 20% عند شراء عطرين أو أكثر.</p>
              <button className="w-full bg-black text-white py-2 rounded-xl text-xs font-bold">تسوق العرض</button>
            </div>
          </div>
        </aside>

        {/* Content Area */}
        <div className="flex-1">
          {isLoading ? (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
              {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : (
            <>
              <div className={`grid gap-4 md:gap-8 ${viewMode === 'grid' ? 'grid-cols-2 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
                {data?.items.map((item, i) => (
                  <ItemCard
                    key={item.id}
                    item={item}
                    index={i}
                    isSaved={savedSet.has(item.id)}
                    hasAlert={alertSet.has(item.id)}
                  />
                ))}
              </div>

              {/* Pagination */}
              {data?.pagination && data.pagination.total_pages > 1 && (
                <div className="flex items-center justify-center gap-4 mt-20">
                  <button
                    disabled={!data.pagination.has_prev}
                    onClick={() => { const n = new URLSearchParams(searchParams); n.set('page', String(page - 1)); setSearchParams(n) }}
                    className="w-12 h-12 rounded-full glass flex items-center justify-center disabled:opacity-30 hover:border-primary transition-all"
                  >
                    <ChevronRight size={20} />
                  </button>

                  <div className="flex gap-2 items-center">
                    {getPaginationRange(page, data.pagination.total_pages).map((p, index) => {
                      if (p === '...') {
                        return <span key={`ellipsis-${index}`} className="text-muted-foreground px-2">...</span>
                      }
                      return (
                        <button
                          key={`page-${p}`}
                          onClick={() => { const n = new URLSearchParams(searchParams); n.set('page', String(p)); setSearchParams(n) }}
                          className={`w-10 h-10 rounded-xl font-bold text-sm transition-all ${page === p ? 'bg-primary text-black' : 'glass hover:bg-secondary'
                            }`}
                        >
                          {p}
                        </button>
                      )
                    })}
                  </div>

                  <button
                    disabled={!data.pagination.has_next}
                    onClick={() => { const n = new URLSearchParams(searchParams); n.set('page', String(page + 1)); setSearchParams(n) }}
                    className="w-12 h-12 rounded-full glass flex items-center justify-center disabled:opacity-30 hover:border-primary transition-all"
                  >
                    <ChevronLeft size={20} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {sidebarOpen && (
          <div className="fixed inset-0 z-[200] lg:hidden">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSidebar(false)} className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
            <motion.div initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }} transition={{ type: 'spring', damping: 25 }} className="absolute bottom-0 left-0 w-full h-[80vh] bg-background rounded-t-[3rem] p-8 overflow-y-auto">
              <div className="flex justify-between items-center mb-8">
                <span className="text-xl font-bold">تصفية المنتجات</span>
                <button type="button" aria-label="إغلاق الفلاتر" onClick={() => setSidebar(false)} className="w-10 h-10 rounded-full glass flex items-center justify-center"><X size={20} /></button>
              </div>
              <FilterContent categories={categories} brands={brands} filters={filters} toggleFilter={toggleFilter} />
              <button type="button" onClick={() => setSidebar(false)} className="btn-gold w-full mt-10 py-4">تطبيق الفلاتر</button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
