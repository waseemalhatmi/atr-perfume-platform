import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, Phone, MapPin, Send, Loader2 } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import SEO from '@/components/SEO'

export default function ContactPage() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    const formData = new FormData(e.currentTarget)
    
    try {
      const res = await axios.post('/api/contact', formData)
      if (res.data.success) {
        toast.success(res.data.message || 'تم إرسال رسالتك بنجاح!')
        ;(e.target as HTMLFormElement).reset()
      } else {
        toast.error(res.data.error || 'حدث خطأ أثناء الإرسال')
      }
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'حدث خطأ غير متوقع')
    } finally {
      setIsSubmitting(false)
    }
  }

  const fadeInUp = {
    initial: { opacity: 0, y: 30 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true },
    transition: { duration: 0.8 }
  }

  return (
    <div className="pt-32 pb-20 overflow-hidden" dir="rtl">
      <SEO 
        title="تواصل معنا" 
        description="نحن هنا للإجابة على استفساراتك وتلبية متطلباتك الراقية في عالم العطور." 
      />
      <section className="container-px mb-16 text-center relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
        <motion.div {...fadeInUp} className="relative z-10 max-w-2xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">تواصل <span className="luxury-text">معنا</span></h1>
          <p className="text-muted-foreground text-lg">نحن هنا للإجابة على استفساراتك وتلبية متطلباتك الراقية. لا تتردد في مراسلتنا.</p>
        </motion.div>
      </section>

      <section className="container-px">
        <div className="grid lg:grid-cols-3 gap-10">
          {/* Contact Info */}
          <motion.div {...fadeInUp} className="lg:col-span-1 space-y-6">
            {[
              { icon: <Mail />, title: 'البريد الإلكتروني', detail: 'contact@36ry.com' },
              { icon: <Phone />, title: 'رقم الهاتف', detail: '+966 50 123 4567' },
              { icon: <MapPin />, title: 'المقر الرئيسي', detail: 'الرياض، المملكة العربية السعودية' },
            ].map((info, i) => (
              <div key={i} className="luxury-card p-8 flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                  {info.icon}
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">{info.title}</h3>
                  <p className="text-muted-foreground text-sm" dir="ltr">{info.detail}</p>
                </div>
              </div>
            ))}
          </motion.div>

          {/* Contact Form */}
          <motion.div 
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="lg:col-span-2 glass rounded-3xl p-8 md:p-12"
          >
            <h2 className="text-2xl font-bold mb-8">أرسل رسالة</h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-bold text-muted-foreground">الاسم الكامل</label>
                  <input type="text" name="name" required className="w-full glass bg-background/50 border border-border/50 rounded-xl px-4 py-3 outline-none focus:border-primary/50 transition-all" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-bold text-muted-foreground">البريد الإلكتروني</label>
                  <input type="email" name="email" required className="w-full glass bg-background/50 border border-border/50 rounded-xl px-4 py-3 outline-none focus:border-primary/50 transition-all text-left" dir="ltr" />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold text-muted-foreground">الموضوع</label>
                <input type="text" name="subject" required className="w-full glass bg-background/50 border border-border/50 rounded-xl px-4 py-3 outline-none focus:border-primary/50 transition-all" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold text-muted-foreground">الرسالة</label>
                <textarea name="message" rows={5} required className="w-full glass bg-background/50 border border-border/50 rounded-xl px-4 py-3 outline-none focus:border-primary/50 transition-all resize-none"></textarea>
              </div>
              <button type="submit" disabled={isSubmitting} className="btn-gold w-full md:w-auto mt-4 px-12 py-4 text-lg">
                {isSubmitting ? <Loader2 className="animate-spin" size={24} /> : <><Send size={20} /> إرسال الرسالة</>}
              </button>
            </form>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
