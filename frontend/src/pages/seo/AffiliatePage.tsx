import { motion } from 'framer-motion'
import { Link2 } from 'lucide-react'

export default function AffiliatePage() {
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
            <Link2 size={32} />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">الإفصاح عن <span className="luxury-text">الروابط</span></h1>
          <p className="text-muted-foreground">الشفافية هي أساس ثقتنا</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="glass rounded-3xl p-8 md:p-16 space-y-12"
        >
          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">التزامنا بالشفافية</h2>
            <p className="text-muted-foreground leading-relaxed">
              في منصة "عطري"، نلتزم بتقديم أدق المعلومات وأفضل الأسعار لعملائنا في عالم العطور الفاخرة والنيش. من أجل الحفاظ على استمرارية الموقع وتطويره باستمرار مجاناً للزوار، نعتمد على برامج التسويق بالعمولة (Affiliate Marketing).
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">ماذا يعني هذا؟</h2>
            <p className="text-muted-foreground leading-relaxed">
              هذا يعني أنه عند النقر على رابط لشراء عطر معين من منصتنا وإتمام عملية الشراء في المتجر الوجهة، قد نحصل على عمولة صغيرة من المتجر دون أي تكلفة إضافية عليك. السعر الذي تدفعه هو نفس السعر المعروض لك دائماً وربما أقل بسبب أكواد الخصم الحصرية.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold text-primary">هل تؤثر العمولة على التقييمات؟</h2>
            <p className="text-muted-foreground leading-relaxed">
              إطلاقاً. إن خوارزميات ترتيب المتاجر وعرض الأسعار في "عطري" تعمل بشكل تلقائي وتعتمد فقط على "أرخص سعر متاح" وجودة المتجر، ولا يتم التلاعب بالأسعار أو تفضيل متجر على آخر بسبب نسب العمولة. ثقتكم هي أثمن ما نملك.
            </p>
          </section>
        </motion.div>
      </div>
    </div>
  )
}
