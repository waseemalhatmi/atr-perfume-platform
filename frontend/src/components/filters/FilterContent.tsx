import React from 'react'

interface FilterOption {
  id: number | string
  name: string
  slug?: string
}

interface FilterContentProps {
  categories: string[]
  brands: string[]
  filters: {
    categories: FilterOption[]
    brands: FilterOption[]
  } | undefined
  toggleFilter: (key: 'category' | 'brand', val: string) => void
}

const FilterContent: React.FC<FilterContentProps> = ({ categories, brands, filters, toggleFilter }) => {
  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-sm font-bold uppercase tracking-widest text-primary mb-6">التصنيفات</h3>
        <div className="flex flex-col gap-3">
          {filters?.categories?.map((c) => (
            <label key={c.id} className="flex items-center gap-3 cursor-pointer group">
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                categories.includes(String(c.id)) ? 'bg-primary border-primary' : 'border-border group-hover:border-primary/50'
              }`}>
                {categories.includes(String(c.id)) && <div className="w-2 h-2 bg-black rounded-full" />}
              </div>
              <input 
                type="checkbox" 
                className="hidden" 
                checked={categories.includes(String(c.id))} 
                onChange={() => toggleFilter('category', String(c.id))} 
              />
              <span className={`text-sm transition-colors ${categories.includes(String(c.id)) ? 'font-bold' : 'text-muted-foreground'}`}>
                {c.name}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold uppercase tracking-widest text-primary mb-6">الماركات</h3>
        <div className="grid grid-cols-1 gap-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
          {filters?.brands?.map((b) => (
            <label key={b.id} className="flex items-center gap-3 cursor-pointer group">
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                brands.includes(String(b.id)) ? 'bg-primary border-primary' : 'border-border group-hover:border-primary/50'
              }`}>
                {brands.includes(String(b.id)) && <div className="w-2 h-2 bg-black rounded-full" />}
              </div>
              <input 
                type="checkbox" 
                className="hidden" 
                checked={brands.includes(String(b.id))} 
                onChange={() => toggleFilter('brand', String(b.id))} 
              />
              <span className={`text-sm transition-colors ${brands.includes(String(b.id)) ? 'font-bold' : 'text-muted-foreground'}`}>
                {b.name}
              </span>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}

export default React.memo(FilterContent)
