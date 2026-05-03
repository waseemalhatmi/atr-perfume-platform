import { motion } from 'framer-motion'
import { Sparkles, ShieldCheck, Gem, Target, Users } from 'lucide-react'
import SEO from '@/components/SEO'

export default function AboutPage() {
  const fadeInUp = {
    initial: { opacity: 0, y: 30 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true },
    transition: { duration: 0.8 }
  }

  return (
    <div className="pt-32 pb-20 overflow-hidden" dir="rtl">
      <SEO 
        title="عن عطري - رحلتنا في عالم العطور" 
        description="نحن منصة عطري، وجهتك الأولى لاكتشاف أرقى العطور النيش والعالمية بأفضل الأسعار الموثوقة." 
      />
      {/* Hero Section */}
      <section className="container-px text-center mb-24 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
        
        <motion.div {...fadeInUp} className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border-primary/20 text-primary text-sm font-bold mb-6">
            <Sparkles size={16} />
            رحلتنا في عالم العطور
          </div>
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            شغفنا هو إيصالك لـ <span className="luxury-text">العطر المثالي</span>
          </h1>
          <p className="text-muted-foreground text-lg md:text-xl leading-relaxed">
            نحن منصة "عطري"، وجهتك الأولى لاكتشاف أرقى العطور النيش والعالمية. صُممت منصتنا لتكون دليلك الذكي الذي يجمع بين أصالة الروائح وأفضل الأسعار من المتاجر الموثوقة.
          </p>
        </motion.div>
      </section>

      {/* Stats/Values */}
      <section className="container-px mb-24">
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { icon: <Gem size={32} />, title: "الجودة والفخامة", desc: "ننتقي أفضل العطور الأصلية بنسبة 100% من أعرق الماركات." },
            { icon: <Target size={32} />, title: "الذكاء والدقة", desc: "محرك بحث متقدم يضمن حصولك على عروض لا تقبل المنافسة." },
            { icon: <ShieldCheck size={32} />, title: "المصداقية", desc: "شراكات استراتيجية مع متاجر موثقة تضمن حقوق المستهلك." },
          ].map((item, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2, duration: 0.8 }}
              className="luxury-card p-10 text-center"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-6">
                {item.icon}
              </div>
              <h3 className="text-2xl font-bold mb-4">{item.title}</h3>
              <p className="text-muted-foreground leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Story Section */}
      <section className="container-px">
        <motion.div {...fadeInUp} className="glass rounded-[3rem] p-10 md:p-20 relative overflow-hidden">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-5xl font-bold mb-6">قصتنا</h2>
              <div className="space-y-6 text-muted-foreground text-lg leading-relaxed">
                <p>
                  بدأت فكرة "عطري" من الحاجة الملحة في السوق العربي لمنصة شفافة تجمع شتات المتاجر، وتقارن الأسعار، وتكشف عن جواهر العطور النيش المخفية.
                </p>
                <p>
                  اليوم، نفخر بأننا نخدم الآلاف من عشاق العطور شهرياً، نقدم لهم تجربة تسوق فخمة، ذكية، وموفرة للوقت والمال.
                </p>
              </div>
            </div>
            <div className="relative h-[400px] rounded-3xl overflow-hidden shadow-luxury">
              <img 
                src="https://images.unsplash.com/photo-1594035910387-fea47734261f?auto=format&fit=crop&q=80&w=800" 
                alt="Our Story" 
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </motion.div>
      </section>
    </div>
  )
}
