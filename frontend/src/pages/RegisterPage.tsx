import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { UserPlus, Mail, Lock, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { register } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

export default function RegisterPage() {
  const { setUser } = useAuthStore()
  const navigate = useNavigate()
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirm: '',
    newsletter: true
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (formData.password !== formData.confirm) {
      return toast.error('كلمات المرور غير متطابقة.')
    }
    
    setLoading(true)
    try {
      const user = await register(formData.email, formData.password, formData.newsletter)
      setUser(user)
      toast.success('تم إنشاء حسابك بنجاح! 🎉')
      navigate('/')
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'فشل في إنشاء الحساب.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[90vh] flex items-center justify-center container-px py-20 relative">
      <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] bg-primary/10 blur-[150px] rounded-full -z-10" />

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass p-8 md:p-12 rounded-[2.5rem] w-full max-w-xl shadow-2xl relative overflow-hidden"
      >
        <div className="grid md:grid-cols-2 gap-12 items-center">
          
          <div className="hidden md:flex flex-col gap-8">
            <h1 className="text-4xl font-bold luxury-text">انضم <br /> إلى النخبة</h1>
            <ul className="space-y-6">
              {[
                "تنبيهات انخفاض الأسعار الفورية",
                "قائمة عطور مفضلة خاصة بك",
                "مقالات ونشرة بريدية حصرية",
                "توصيات مخصصة لذوقك"
              ].map((text, i) => (
                <li key={i} className="flex items-center gap-3 text-sm font-medium">
                  <CheckCircle2 className="text-primary" size={20} />
                  {text}
                </li>
              ))}
            </ul>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="md:hidden text-center mb-8">
              <h1 className="text-3xl font-bold">إنشاء حساب</h1>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider pr-2">البريد الإلكتروني</label>
              <div className="relative group">
                <Mail className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={16} />
                <input 
                  type="email" 
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                  placeholder="email@example.com"
                  className="w-full bg-secondary/30 border-2 border-transparent focus:border-primary/30 p-4 pr-12 rounded-2xl outline-none transition-all text-sm"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider pr-2">كلمة المرور</label>
              <div className="relative group">
                <Lock className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={16} />
                <input 
                  type="password" 
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                  placeholder="••••••••"
                  className="w-full bg-secondary/30 border-2 border-transparent focus:border-primary/30 p-4 pr-12 rounded-2xl outline-none transition-all text-sm"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider pr-2">تأكيد الكلمة</label>
              <div className="relative group">
                <Lock className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={16} />
                <input 
                  type="password" 
                  value={formData.confirm}
                  onChange={(e) => setFormData({...formData, confirm: e.target.value})}
                  required
                  placeholder="••••••••"
                  className="w-full bg-secondary/30 border-2 border-transparent focus:border-primary/30 p-4 pr-12 rounded-2xl outline-none transition-all text-sm"
                />
              </div>
            </div>

            <label className="flex items-center gap-3 cursor-pointer group py-2">
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                formData.newsletter ? 'bg-primary border-primary' : 'border-border'
              }`}>
                {formData.newsletter && <div className="w-2 h-2 bg-black rounded-full" />}
              </div>
              <input 
                type="checkbox" 
                className="hidden" 
                checked={formData.newsletter} 
                onChange={() => setFormData({...formData, newsletter: !formData.newsletter})} 
              />
              <span className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors">أرغب في الاشتراك بالنشرة البريدية</span>
            </label>

            <button 
              type="submit" 
              disabled={loading}
              className="btn-gold w-full py-4 text-lg flex items-center justify-center gap-2 disabled:opacity-50 mt-4"
            >
              {loading ? 'جاري التنفيذ...' : <><UserPlus size={20} /> انضم إلينا</>}
            </button>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border/50"></div></div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-4 text-muted-foreground">أو عبر</span>
              </div>
            </div>

            <button 
              type="button"
              onClick={() => window.location.href = '/api/auth/google'}
              className="w-full py-4 rounded-2xl border-2 border-border/50 hover:border-primary/50 hover:bg-primary/5 transition-all flex items-center justify-center gap-3 font-bold"
            >
              <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5" />
              التسجيل السريع بجوجل
            </button>

            <p className="text-center text-sm text-muted-foreground pt-4">
              لديك حساب بالفعل؟{' '}
              <Link to="/login" className="text-primary font-bold hover:underline">سجل دخولك</Link>
            </p>
          </form>
        </div>
      </motion.div>
    </div>
  )
}
