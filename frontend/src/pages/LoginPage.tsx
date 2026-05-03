import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { LogIn, Mail, Lock, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'
import { login } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

export default function LoginPage() {
  const { setUser } = useAuthStore()
  const navigate = useNavigate()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const user = await login(email, password)
      setUser(user)
      toast.success(`مرحباً بك مجدداً! 👋`, {
        icon: '✨',
        style: { borderRadius: '1rem', background: '#18181b', color: '#fff' }
      })
      navigate('/')
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'بيانات الدخول غير صحيحة.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[90vh] flex items-center justify-center container-px py-20 relative">
      {/* Abstract Background Shapes */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/5 blur-[120px] rounded-full -z-10" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass p-8 md:p-12 rounded-[2.5rem] w-full max-w-lg shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 blur-3xl" />
        
        <div className="text-center mb-12">
          <div className="w-16 h-16 bg-luxury-gradient rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl animate-float">
            <Lock className="text-black" size={28} />
          </div>
          <h1 className="text-3xl font-bold mb-2">تسجيل الدخول</h1>
          <p className="text-muted-foreground">مرحباً بك في عالم الفخامة والجمال</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-bold pr-2">البريد الإلكتروني</label>
            <div className="relative group">
              <Mail className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="email@example.com"
                className="w-full bg-secondary/50 border-2 border-transparent focus:border-primary/30 p-4 pr-12 rounded-2xl outline-none transition-all"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center px-2">
              <label className="text-sm font-bold">كلمة المرور</label>
              <button type="button" className="text-xs text-primary hover:underline">نسيت الكلمة؟</button>
            </div>
            <div className="relative group">
              <Lock className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
              <input 
                type={showPass ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full bg-secondary/50 border-2 border-transparent focus:border-primary/30 p-4 pr-12 pl-12 rounded-2xl outline-none transition-all"
              />
              <button 
                type="button" 
                onClick={() => setShowPass(!showPass)}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
              >
                {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="btn-gold w-full py-4 text-lg flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? 'جاري التحقق...' : <><LogIn size={20} /> دخول آمن</>}
          </button>
        </form>

        <div className="relative my-8">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border/50"></div></div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-4 text-muted-foreground">أو عبر</span>
          </div>
        </div>

        <button 
          onClick={() => window.location.href = '/api/auth/google'}
          className="w-full py-4 rounded-2xl border-2 border-border/50 hover:border-primary/50 hover:bg-primary/5 transition-all flex items-center justify-center gap-3 font-bold"
        >
          <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5" />
          المتابعة باستخدام جوجل
        </button>

        <div className="mt-10 pt-8 border-t border-border/50 text-center">
          <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground mb-6">
            <ShieldCheck size={14} className="text-primary" />
            تشفير بياناتك محمي بنظام SSL المتطور
          </div>
          <p className="text-sm text-muted-foreground">
            ليس لديك حساب بعد؟{' '}
            <Link to="/register" className="text-primary font-bold hover:underline">أنشئ حسابك الآن</Link>
          </p>
        </div>
      </motion.div>
    </div>
  )
}
