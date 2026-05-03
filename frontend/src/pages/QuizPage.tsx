import { useState, useEffect, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ChevronRight, ChevronLeft, Sparkles, Check, ArrowRight, Share2, Bookmark } from 'lucide-react'
import { quizQuestions } from '@/config/quiz'
import { quizRecommend, type Item } from '@/lib/api'
import ItemCard from '@/components/ItemCard'
import SEO from '@/components/SEO'
import { useAnalytics } from '@/hooks/useAnalytics'
import toast from 'react-hot-toast'

export default function QuizPage() {
  const [step, setStep] = useState(-1) // -1 is landing, length is results
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [results, setResults] = useState<Item[]>([])
  const { track } = useAnalytics()

  // Load saved progress
  useEffect(() => {
    try {
      const savedAnswers = localStorage.getItem('quiz_answers')
      const savedStep = localStorage.getItem('quiz_step')
      if (savedAnswers && savedStep) {
        setAnswers(JSON.parse(savedAnswers))
        const pStep = parseInt(savedStep, 10)
        // If not finished, we can resume
        if (pStep >= 0 && pStep < quizQuestions.length) {
          setStep(pStep)
        }
      }
    } catch {}
  }, [])

  // Save progress
  useEffect(() => {
    if (step >= 0 && step < quizQuestions.length) {
      localStorage.setItem('quiz_answers', JSON.stringify(answers))
      localStorage.setItem('quiz_step', step.toString())
    }
  }, [step, answers])

  const handleStart = () => {
    track('quiz_started')
    setStep(0)
  }

  const handleSelect = useCallback((key: string, value: string) => {
    setAnswers(prev => ({ ...prev, [key]: value }))
  }, [])

  const handleNext = async () => {
    if (step < quizQuestions.length - 1) {
      setStep(s => s + 1)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      // Submit
      track('quiz_completed', answers)
      setIsSubmitting(true)
      setStep(quizQuestions.length) // Loading results screen
      window.scrollTo({ top: 0, behavior: 'smooth' })
      try {
        const res = await quizRecommend(answers)
        setResults(res.items || [])
        // Clear progress
        localStorage.removeItem('quiz_answers')
        localStorage.removeItem('quiz_step')
      } catch (err) {
        toast.error('حدث خطأ أثناء تحليل النتائج، يرجى المحاولة لاحقاً')
        setStep(quizQuestions.length - 1) // go back to last question
      } finally {
        setIsSubmitting(false)
      }
    }
  }

  const handlePrev = () => {
    setStep(s => Math.max(-1, s - 1))
  }

  // Explainability Generator
  const getExplanation = useCallback((item: Item) => {
    const q1 = quizQuestions.find(q => q.backendKey === 'gender')?.options.find(o => o.id === answers['gender'])?.label || ''
    const q2 = quizQuestions.find(q => q.backendKey === 'apparel')?.options.find(o => o.id === answers['apparel'])?.label || ''
    const q3 = quizQuestions.find(q => q.backendKey === 'activity')?.options.find(o => o.id === answers['activity'])?.label || ''
    const q4 = quizQuestions.find(q => q.backendKey === 'vibe')?.options.find(o => o.id === answers['vibe'])?.label || ''
    
    return `اخترنا "${item.name}" خصيصاً لك لأنه يعكس طابعك الـ ${q4} ويتناسب تماماً مع استخدامك في ${q3} بأسلوب ${q2}.`
  }, [answers])

  // Landing Screen
  if (step === -1) {
    return (
      <div className="min-h-screen flex items-center justify-center container-px py-20 relative overflow-hidden">
        <SEO title="اكتشف عطرك المثالي | منصة عطري" description="اختبار ذكي يحلل شخصيتك وتفضيلاتك ليقترح لك العطر المثالي." />
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/10 -z-10" />
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-primary/10 blur-[100px] rounded-full -z-10 animate-pulse" />
        
        <motion.div 
          initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}
          className="max-w-2xl mx-auto text-center glass p-12 md:p-20 rounded-[3rem] shadow-2xl relative"
        >
          <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-8 border border-primary/20">
            <Sparkles className="text-primary" size={32} />
          </div>
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            اكتشف <span className="luxury-text">عطرك المثالي</span>
          </h1>
          <p className="text-muted-foreground text-lg mb-12 leading-relaxed">
            من خلال الذكاء الاصطناعي وتحليل أكثر من 10,000 عطر عالمي ونيش، 
            سنجد لك البصمة العطرية التي تعبر عن شخصيتك وتلبي احتياجاتك في 5 أسئلة فقط.
          </p>
          <button onClick={handleStart} className="btn-gold px-12 py-5 text-lg w-full sm:w-auto shadow-[0_0_40px_rgba(212,175,55,0.3)] hover:scale-105 transition-all">
            ابدأ الاختبار الآن
          </button>
        </motion.div>
      </div>
    )
  }

  // Results / Loading Screen
  if (step === quizQuestions.length) {
    return (
      <div className="min-h-screen container-px py-32">
        <SEO title="نتائجك العطرية | منصة عطري" />
        {isSubmitting ? (
          <div className="flex flex-col items-center justify-center text-center h-[50vh]">
            <div className="relative w-32 h-32 mb-8">
              <div className="absolute inset-0 border-4 border-secondary rounded-full" />
              <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              <Sparkles className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-primary" size={32} />
            </div>
            <h2 className="text-3xl font-bold mb-4">جاري تحليل تفضيلاتك...</h2>
            <p className="text-muted-foreground">نطابق إجاباتك مع أكبر قاعدة بيانات للعطور النيش والعالمية</p>
          </div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <span className="badge--luxury mb-4">AI Recommended</span>
              <h2 className="text-4xl md:text-6xl font-bold mb-6">مجموعتك <span className="luxury-text">الخاصة</span></h2>
              <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                بناءً على تحليلاتنا الدقيقة لشخصيتك وأسلوب حياتك، هذه هي العطور التي ستكمل أناقتك وتمنحك الحضور الذي تستحقه.
              </p>
            </div>

            {results.length === 0 ? (
              <div className="text-center glass p-16 rounded-3xl">
                <h3 className="text-2xl font-bold mb-4">عذراً، لم نجد تطابقاً كاملاً</h3>
                <p className="text-muted-foreground mb-8">حاول تعديل بعض إجاباتك للحصول على نتائج أدق.</p>
                <button onClick={() => setStep(0)} className="btn-gold px-8">إعادة الاختبار</button>
              </div>
            ) : (
              <div className="space-y-12">
                {results.map((item, i) => (
                  <motion.div 
                    key={item.id}
                    initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                    className="glass p-6 md:p-8 rounded-[2rem] flex flex-col md:flex-row gap-8 items-center md:items-stretch group hover:border-primary/30 transition-colors"
                  >
                    <div className="w-full md:w-1/3 flex-shrink-0">
                      <ItemCard item={item} />
                    </div>
                    <div className="flex-1 flex flex-col justify-center">
                      <div className="bg-secondary/30 p-6 rounded-2xl mb-6 relative">
                        <div className="absolute -left-3 -top-3 w-8 h-8 bg-primary text-black rounded-full flex items-center justify-center font-black">
                          {i + 1}
                        </div>
                        <h4 className="font-bold text-primary mb-2 flex items-center gap-2">
                          <Sparkles size={16} /> لماذا اخترنا هذا العطر لك؟
                        </h4>
                        <p className="text-muted-foreground leading-relaxed">
                          {getExplanation(item)}
                        </p>
                      </div>
                      
                      <div className="flex flex-wrap gap-4 mt-auto">
                        <button className="flex-1 glass py-4 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-primary hover:text-black transition-colors">
                          <Bookmark size={18} /> حفظ النتيجة
                        </button>
                        <button onClick={() => {
                          navigator.clipboard.writeText(window.location.href)
                          toast.success('تم نسخ الرابط')
                        }} className="flex-1 glass py-4 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-secondary transition-colors">
                          <Share2 size={18} /> شارك
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}

            <div className="mt-20 text-center">
              <div className="w-full h-px bg-border/50 mb-12" />
              <Link to="/items" className="inline-flex items-center gap-2 text-lg font-bold hover:text-primary transition-colors">
                تصفح جميع العطور المتاحة في المتجر <ArrowRight size={20} />
              </Link>
            </div>
          </motion.div>
        )}
      </div>
    )
  }

  // Active Question
  const currentQ = quizQuestions[step]
  const selectedValue = answers[currentQ.backendKey]
  const progress = ((step + 1) / quizQuestions.length) * 100

  return (
    <div className="min-h-screen pt-32 pb-20 container-px max-w-4xl mx-auto flex flex-col">
      <SEO title="الاختبار | منصة عطري" />
      
      {/* Progress Bar */}
      <div className="mb-12">
        <div className="flex justify-between items-end mb-4 text-sm font-bold text-muted-foreground">
          <button onClick={handlePrev} className="flex items-center gap-1 hover:text-primary transition-colors">
            <ChevronRight size={16} /> السابق
          </button>
          <span>سؤال {step + 1} من {quizQuestions.length}</span>
        </div>
        <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
          <motion.div 
            className="h-full bg-primary"
            initial={{ width: `${(step / quizQuestions.length) * 100}%` }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeInOut" }}
          />
        </div>
      </div>

      {/* Question Area */}
      <div className="flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentQ.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            <div className="mb-12 text-center md:text-right">
              <h2 className="text-3xl md:text-5xl font-bold mb-4">{currentQ.title}</h2>
              {currentQ.subtitle && (
                <p className="text-muted-foreground text-lg">{currentQ.subtitle}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {currentQ.options.map((opt) => {
                const isSelected = selectedValue === opt.id
                return (
                  <button
                    key={opt.id}
                    onClick={() => handleSelect(currentQ.backendKey, opt.id)}
                    className={`relative p-8 rounded-3xl text-right transition-all duration-300 border-2 group ${
                      isSelected 
                        ? 'bg-primary/10 border-primary shadow-[0_0_20px_rgba(212,175,55,0.15)]' 
                        : 'glass border-transparent hover:border-primary/40'
                    }`}
                  >
                    {isSelected && (
                      <div className="absolute top-4 left-4 w-6 h-6 bg-primary text-black rounded-full flex items-center justify-center">
                        <Check size={14} strokeWidth={3} />
                      </div>
                    )}
                    <h3 className={`text-xl font-bold mb-2 transition-colors ${isSelected ? 'text-primary' : ''}`}>
                      {opt.label}
                    </h3>
                    {opt.description && (
                      <p className="text-sm text-muted-foreground group-hover:text-foreground/80 transition-colors">
                        {opt.description}
                      </p>
                    )}
                  </button>
                )
              })}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Footer Nav */}
      <div className="mt-12 flex justify-end">
        <button
          onClick={handleNext}
          disabled={!selectedValue}
          className="btn-gold px-12 py-4 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group"
        >
          {step === quizQuestions.length - 1 ? 'إظهار النتائج' : 'التالي'}
          <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  )
}
