import { Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { useAuthStore } from '@/store/authStore'
import { Navigate } from 'react-router-dom'
import AdminLayout from '@/components/layout/AdminLayout'

// Admin Pages (Fix #4: Admin Bundle Optimization)
const AdminDashboard = lazy(() => import('@/pages/admin/AdminDashboard'))
const AdminItems = lazy(() => import('@/pages/admin/AdminItems'))
const AdminUsers = lazy(() => import('@/pages/admin/AdminUsers'))
const AdminMessages = lazy(() => import('@/pages/admin/AdminMessages'))
const AdminNewsletter = lazy(() => import('@/pages/admin/AdminNewsletter'))
const AdminAnalytics = lazy(() => import('@/pages/admin/AdminAnalytics'))
const AdminSettings = lazy(() => import('@/pages/admin/AdminSettings'))

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuthStore()

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  )
  if (!user || !user.is_admin) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function AdminApp() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <Routes>
        <Route element={<AdminRoute><AdminLayout /></AdminRoute>}>
          <Route index          element={<AdminDashboard />} />
          <Route path="items"      element={<AdminItems />} />
          <Route path="users"      element={<AdminUsers />} />
          <Route path="messages"   element={<AdminMessages />} />
          <Route path="newsletter" element={<AdminNewsletter />} />
          <Route path="analytics"  element={<AdminAnalytics />} />
          <Route path="settings"   element={<AdminSettings />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
