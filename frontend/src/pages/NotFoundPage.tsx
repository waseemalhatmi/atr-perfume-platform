import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Home } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
        <p className="text-8xl mb-4">🌸</p>
        <h1 className="luxury-text font-serif text-5xl font-bold mb-4">404</h1>
        <p className="text-muted-foreground text-lg mb-8">الصفحة التي تبحث عنها غير موجودة.</p>
        <Link to="/" className="btn btn--luxury btn--lg px-8 gap-2">
          <Home size={18} /> العودة للرئيسية
        </Link>
      </motion.div>
    </div>
  )
}
