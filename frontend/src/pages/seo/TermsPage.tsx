import { motion } from 'framer-motion'
import { FileText } from 'lucide-react'

export default function TermsPage() {
  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.8 }
  }

  return (
    <div className="pt-32 pb-20 overflow-hidden" dir="rtl">
      <div className="container-px max-w-4xl mx-auto">
        <motion.div {...fadeInUp} className="text-center mb-16">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-6">
            <FileText size={32} />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">شروط <span className="luxury-text">الاستخدام</span></h1>
          <p className="text-muted-foreground">اخر تحديث: مايو 2026</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="glass rounded-3xl p-8 md:p-16 space-y-12"
        >
          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">1. قبول الشروط</h2>
            <p className="text-muted-foreground leading-relaxed">
              باستخدامك لمنصة "عطري"، فإنك توافق على الالتزام بشروط الاستخدام هذه. إذا كنت لا توافق على أي جزء من هذه الشروط، يرجى التوقف عن استخدام الموقع فوراً.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">2. طبيعة الخدمة</h2>
            <p className="text-muted-foreground leading-relaxed">
              عطري هو محرك بحث ومنصة مقارنة أسعار. نحن لا نبيع العطور بشكل مباشر، بل نوجهك إلى أفضل المتاجر الإلكترونية الموثوقة التي تقدم المنتجات التي تبحث عنها. 
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">3. دقة المعلومات</h2>
            <p className="text-muted-foreground leading-relaxed">
              نحن نسعى جاهدين لتوفير أسعار دقيقة ومحدثة على مدار الساعة، إلا أن الأسعار والتوافر قد يتغيران في المتاجر الوجهة دون إشعار مسبق. لا تتحمل "عطري" مسؤولية أي تفاوت بين السعر المعروض وسعر المتجر النهائي.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">4. حقوق الملكية الفكرية</h2>
            <p className="text-muted-foreground leading-relaxed">
              جميع المحتويات على هذه المنصة، بما في ذلك النصوص، التصاميم، الجرافيك، والشعارات، هي ملك لـ "عطري" أو للعلامات التجارية المعنية. يُمنع إعادة استخدام المحتوى التجاري دون إذن كتابي مسبق.
            </p>
          </section>
        </motion.div>
      </div>
    </div>
  )
}
