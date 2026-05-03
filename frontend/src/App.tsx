import { Routes, Route, useLocation, Navigate, useNavigate } from 'react-router-dom'
import { lazy, Suspense, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'
import ChatAssistant from '@/components/ChatAssistant'

// Lazy loaded components for production performance
const HomePage = lazy(() => import('@/pages/HomePage'))
const ItemsPage = lazy(() => import('@/pages/ItemsPage'))
const ItemDetailPage = lazy(() => import('@/pages/ItemDetailPage'))
const SearchPage = lazy(() => import('@/pages/SearchPage'))
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/RegisterPage'))
const ProfilePage = lazy(() => import('@/pages/ProfilePage'))
const ComparePage = lazy(() => import('@/pages/ComparePage'))
const QuizPage = lazy(() => import('@/pages/QuizPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

// SEO Pages (Fix #3: Eager Loading for Search Engines)
import AboutPage from '@/pages/seo/AboutPage'
import ContactPage from '@/pages/seo/ContactPage'
import PrivacyPage from '@/pages/seo/PrivacyPage'
import TermsPage from '@/pages/seo/TermsPage'
import AffiliatePage from '@/pages/seo/AffiliatePage'

// Admin App (Fix #4: Lazy Loaded Separate Module)
const AdminApp = lazy(() => import('@/admin/AdminApp'))

// Error Boundary (Bonus #9)
import ErrorBoundary from '@/components/ErrorBoundary'

export default function App() {
  const initialize   = useAuthStore((s) => s.initialize)
  const refreshAuth  = useAuthStore((s) => s.refreshAuth)
  const setUser      = useAuthStore((s) => s.setUser)
  const location     = useLocation()
  const navigate     = useNavigate()
  const isAdminPath  = location.pathname.startsWith('/admin')

  // One-time init on mount
  useEffect(() => {
    initialize()
  }, [initialize])

  // Silent session re-validation:
  //   1. When user returns to this tab (visibilitychange)
  //   2. Every 10 minutes in the background
  // Uses refreshAuth() which is a no-op if nothing changed.
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === 'visible') refreshAuth()
    }
    document.addEventListener('visibilitychange', onVisible)
    const interval = setInterval(refreshAuth, 10 * 60 * 1000) // 10 min
    return () => {
      document.removeEventListener('visibilitychange', onVisible)
      clearInterval(interval)
    }
  }, [refreshAuth])

  /**
   * Global session-expiry handler.
   *
   * Fired by the axios 401 interceptor in api.ts via:
   *   window.dispatchEvent(new CustomEvent('auth:session-expired'))
   *
   * We handle it here (inside Router) so we can call useNavigate() safely.
   * This avoids the circular dependency: authStore → api → authStore.
   */
  const handleSessionExpired = useCallback(() => {
    setUser(null)                        // clear auth state (no API call needed)
    toast.error('انتهت جلستك. يرجى تسجيل الدخول مجدداً.', {
      icon: '🔐',
      duration: 4000,
    })
    navigate('/login', { replace: true })
  }, [setUser, navigate])

  useEffect(() => {
    window.addEventListener('auth:session-expired', handleSessionExpired)
    return () => window.removeEventListener('auth:session-expired', handleSessionExpired)
  }, [handleSessionExpired])

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--background)', color: 'var(--foreground)' }}>
      <ErrorBoundary>
      {!isAdminPath && <Navbar />}

      <main className="flex-1">
        <Suspense fallback={
          <div className="min-h-[60vh] flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        }>
          <Routes>
          {/* Public Routes */}
          <Route path="/"              element={<HomePage />} />
          <Route path="/items"         element={<ItemsPage />} />
          <Route path="/items/:id"     element={<ItemDetailPage />} />
          <Route path="/search"        element={<SearchPage />} />
          <Route path="/login"         element={<LoginPage />} />
          <Route path="/register"      element={<RegisterPage />} />
          <Route path="/profile"       element={<ProfilePage />} />
          <Route path="/compare"       element={<ComparePage />} />
          <Route path="/quiz"          element={<QuizPage />} />
          
          {/* SEO / Static Routes */}
          <Route path="/about"         element={<AboutPage />} />
          <Route path="/contact"       element={<ContactPage />} />
          <Route path="/privacy"       element={<PrivacyPage />} />
          <Route path="/terms"         element={<TermsPage />} />
          <Route path="/affiliate"     element={<AffiliatePage />} />

          {/* Admin Application (Fix #4) */}
          <Route path="/admin/*" element={<AdminApp />} />

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
        </Suspense>
      </main>

      {!isAdminPath && <Footer />}
      {!isAdminPath && <ChatAssistant />}
      </ErrorBoundary>
    </div>
  )
}
