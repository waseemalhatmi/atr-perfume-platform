import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { usePriceHistory } from '@/hooks/usePriceHistory'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Props {
  itemId: number
  currency?: string
}

const CustomTooltip = ({ active, payload, label, currency }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass p-4 rounded-xl border border-border/50 shadow-2xl">
        <p className="text-muted-foreground text-sm mb-1">{label}</p>
        <p className="text-primary font-bold text-lg">
          {payload[0].value} {currency}
        </p>
      </div>
    )
  }
  return null
}

const PriceHistoryChart = ({ itemId, currency = 'SAR' }: Props) => {
  const { data, isLoading, isError } = usePriceHistory(itemId)

  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) return []
    return data.map((d: any) => ({
      date: new Date(d.date).toLocaleDateString('ar-SA', { month: 'short', day: 'numeric' }),
      price: Number(d.price),
    }))
  }, [data])

  const stats = useMemo(() => {
    if (chartData.length < 2) return null
    const prices = chartData.map(d => d.price)
    const currentPrice = prices[prices.length - 1]
    const firstPrice = prices[0]
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)
    
    let trend = 'neutral'
    if (currentPrice > firstPrice) trend = 'up'
    if (currentPrice < firstPrice) trend = 'down'

    return { minPrice, maxPrice, trend }
  }, [chartData])

  if (isLoading) {
    return (
      <div className="w-full h-72 glass rounded-3xl p-6 flex flex-col justify-between">
        <div className="flex justify-between items-center mb-4">
          <div className="h-6 w-32 bg-secondary/50 rounded-full animate-pulse" />
          <div className="h-6 w-24 bg-secondary/50 rounded-full animate-pulse" />
        </div>
        <div className="flex-1 bg-secondary/20 rounded-xl animate-pulse" />
      </div>
    )
  }

  if (isError || chartData.length === 0) {
    return (
      <div className="w-full h-72 glass rounded-3xl p-6 flex flex-col items-center justify-center text-center">
        <Minus className="text-muted-foreground/30 mb-2" size={32} />
        <h3 className="font-bold text-lg mb-1">لا يوجد سجل أسعار حالياً</h3>
        <p className="text-sm text-muted-foreground">لم نتمكن من العثور على تغيرات سابقة في سعر هذا العطر.</p>
      </div>
    )
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full glass rounded-3xl p-4 md:p-6 shadow-xl"
    >
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h3 className="font-bold text-lg md:text-xl">مؤشر تغير السعر</h3>
        
        {stats && (
          <div className="flex items-center gap-4 text-sm font-bold bg-secondary/30 px-4 py-2 rounded-full">
            <div className="flex items-center gap-1">
              <span className="text-muted-foreground">الأدنى:</span>
              <span className="text-green-500">{stats.minPrice}</span>
            </div>
            <div className="w-px h-4 bg-border/50" />
            <div className="flex items-center gap-1">
              <span className="text-muted-foreground">الأعلى:</span>
              <span className="text-red-500">{stats.maxPrice}</span>
            </div>
            <div className="w-px h-4 bg-border/50" />
            <div className="flex items-center gap-1">
              {stats.trend === 'up' && <TrendingUp size={16} className="text-red-500" aria-label="السعر يرتفع" />}
              {stats.trend === 'down' && <TrendingDown size={16} className="text-green-500" aria-label="السعر ينخفض" />}
              {stats.trend === 'neutral' && <Minus size={16} className="text-muted-foreground" aria-label="السعر ثابت" />}
            </div>
          </div>
        )}
      </div>

      <div className="h-64 w-full" dir="ltr">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="date" 
              stroke="rgba(255,255,255,0.3)" 
              fontSize={12} 
              tickLine={false}
              axisLine={false}
              dy={10}
            />
            <YAxis 
              stroke="rgba(255,255,255,0.3)" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}`}
              dx={-10}
              domain={['dataMin - 50', 'auto']}
            />
            <Tooltip content={<CustomTooltip currency={currency} />} cursor={{ stroke: 'rgba(212,175,55,0.2)', strokeWidth: 2 }} />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#d4af37" 
              strokeWidth={3}
              dot={{ fill: '#18181b', stroke: '#d4af37', strokeWidth: 2, r: 4 }}
              activeDot={{ fill: '#d4af37', stroke: '#fff', strokeWidth: 2, r: 6 }}
              animationDuration={1500}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  )
}

export default React.memo(PriceHistoryChart)
