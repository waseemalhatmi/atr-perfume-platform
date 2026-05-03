import { motion } from 'framer-motion'
import { ShieldAlert } from 'lucide-react'

export default function PrivacyPage() {
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
            <ShieldAlert size={32} />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">سياسة <span className="luxury-text">الخصوصية</span></h1>
          <p className="text-muted-foreground">اخر تحديث: مايو 2026</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="glass rounded-3xl p-8 md:p-16 space-y-12"
        >
          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">1. مقدمة</h2>
            <p className="text-muted-foreground leading-relaxed">
              نحن في "عطري" نأخذ خصوصيتك على محمل الجد. توضح سياسة الخصوصية هذه كيف نقوم بجمع، استخدام، وحماية معلوماتك الشخصية عند استخدامك لمنصتنا لغرض تصفح ومقارنة أسعار العطور.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">2. المعلومات التي نجمعها</h2>
            <ul className="list-disc list-inside text-muted-foreground leading-relaxed space-y-2">
              <li>المعلومات الشخصية التي تقدمها طواعية عند التسجيل (الاسم، البريد الإلكتروني).</li>
              <li>بيانات التصفح والتحليلات لتحسين تجربة المستخدم.</li>
              <li>سجل الاختبارات والخيارات المفضلة في مركز "الذكاء العطري".</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">3. حماية بياناتك</h2>
            <p className="text-muted-foreground leading-relaxed">
              نستخدم أحدث تقنيات التشفير وبروتوكولات الأمان (SSL) لضمان سرية بياناتك. نحن لا نقوم ببيع أو تأجير معلوماتك الشخصية لأي أطراف ثالثة لأغراض تسويقية.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">4. الروابط الخارجية (Affiliate)</h2>
            <p className="text-muted-foreground leading-relaxed">
              تحتوي منصتنا على روابط لمتاجر خارجية. يرجى العلم أن سياسة الخصوصية هذه لا تنطبق على تلك المتاجر، وننصح بقراءة سياسات الخصوصية الخاصة بها عند الانتقال إليها.
            </p>
          </section>
        </motion.div>
      </div>
    </div>
  )
}
