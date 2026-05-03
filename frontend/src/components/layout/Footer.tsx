import { Link } from 'react-router-dom'
import { Globe, Mail, MessageCircle, Heart } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t mt-20" style={{ borderColor: 'var(--border)', background: 'var(--card)' }}>
      <div className="container py-12 grid grid-cols-1 md:grid-cols-3 gap-10">
        {/* Brand */}
        <div>
          <span className="luxury-text font-serif text-3xl font-bold">عطري</span>
          <p className="mt-3 text-sm" style={{ color: 'var(--muted-foreground)' }}>
            اكتشف أرقى العطور العالمية وقارن الأسعار من أفضل المتاجر في مكان واحد.
          </p>
          <div className="flex gap-3 mt-4">
            <a href="#" aria-label="Website"
              className="btn btn--ghost btn--sm !p-2 rounded-full hover:text-primary transition-colors">
              <Globe size={18} />
            </a>
            <a href="#" aria-label="Mail"
              className="btn btn--ghost btn--sm !p-2 rounded-full hover:text-primary transition-colors">
              <Mail size={18} />
            </a>
            <a href="#" aria-label="WhatsApp"
              className="btn btn--ghost btn--sm !p-2 rounded-full hover:text-primary transition-colors">
              <MessageCircle size={18} />
            </a>
          </div>
        </div>

        {/* Links */}
        <div>
          <h3 className="font-bold mb-4 text-sm uppercase tracking-wider" style={{ color: 'var(--primary)' }}>
            روابط سريعة
          </h3>
          <ul className="space-y-2 text-sm" style={{ color: 'var(--muted-foreground)' }}>
            {[
              ['/items',    'جميع العطور'],
              ['/search',   'البحث'],
              ['/login',    'تسجيل الدخول'],
              ['/register', 'إنشاء حساب'],
            ].map(([to, label]) => (
              <li key={to}>
                <Link to={to} className="hover:text-gold-primary transition-colors">{label}</Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Legal */}
        <div>
          <h3 className="font-bold mb-4 text-sm uppercase tracking-wider" style={{ color: 'var(--primary)' }}>
            قانوني
          </h3>
          <ul className="space-y-2 text-sm" style={{ color: 'var(--muted-foreground)' }}>
            {[
              ['/about',     'من نحن'],
              ['/contact',   'اتصل بنا'],
              ['/privacy',   'سياسة الخصوصية'],
              ['/terms',     'شروط الاستخدام'],
              ['/affiliate', 'الإفصاح عن الروابط'],
            ].map(([to, label]) => (
              <li key={to}>
                <Link to={to} className="hover:text-primary transition-colors">{label}</Link>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="border-t py-4 text-center text-xs" style={{ borderColor: 'var(--border)', color: 'var(--muted-foreground)' }}>
        صُنع بـ <Heart size={12} className="inline text-red-400" /> © {new Date().getFullYear()} عطري. جميع الحقوق محفوظة.
      </div>
    </footer>
  )
}
