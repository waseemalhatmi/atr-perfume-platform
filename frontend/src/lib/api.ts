import axios from 'axios'

// In development Vite proxies /api → http://127.0.0.1:5000
// In production the built files are served by Flask directly
const api = axios.create({
  baseURL: '/',
  withCredentials: true,          // send Flask session cookie
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000, // Increased to 30s to allow for heavy initial AI calculations
})

/**
 * Global 401 interceptor.
 *
 * When ANY protected endpoint returns 401 (session expired / invalid), we
 * dispatch a native browser event instead of importing authStore directly.
 * This avoids the circular dependency: authStore → api → authStore.
 *
 * App.tsx listens for this event and executes: clearUser() + navigate('/login').
 *
 * Endpoints excluded from auto-logout:
 *   • /api/auth/me    — fetchMe already handles 401 gracefully (returns null)
 *   • /api/auth/login — a 401 here means "wrong credentials", not session expiry
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status: number  = error.response?.status ?? 0
    const url: string     = error.config?.url ?? ''
    const isAuthInit      = url.includes('/api/auth/me') || url.includes('/api/auth/login')

    if (status === 401 && !isAuthInit) {
      window.dispatchEvent(new CustomEvent('auth:session-expired'))
    }

    return Promise.reject(error)
  },
)

// ── Types ────────────────────────────────────────────────────────────────────

export interface StoreLink {
  id: number
  store: { id: number; name: string; slug: string }
  price: number | null
  old_price: number | null
  currency: string | null
  affiliate_url: string
  availability: string | null
  is_active: boolean
}

export interface Variant {
  id: number
  title: string
  is_default: boolean
  attributes: Record<string, string>
  store_links: StoreLink[]
}

export interface ItemImage {
  path: string
  alt: string
}

export interface Item {
  id: number
  name: string
  slug: string
  description: string | null
  brand: { id: number; name: string; slug: string }
  category: { id: number; name: string; slug: string }
  images: ItemImage[]
  view_count: number
  click_count: number
  min_price: number
  currency: string
  // Full detail only
  variants?: Variant[]
  specs?: Record<string, Record<string, string>>
  perfume_notes?: { top: string | null; heart: string | null; base: string | null } | null
  quick_details?: { key: string; value: string }[]
  meta_description?: string | null
  // Comparison specific (Dynamic)
  ai_score?: number
  is_winner?: boolean
  match_score?: number
}

export interface Clone extends Item {
  match_score?: number
  price_diff?: number
}

export interface Pagination {
  page: number
  per_page: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface FilterOption { id: number; name: string; slug: string }

export interface AuthUser {
  id: number
  email: string
  is_admin: boolean
  provider: string | null
  is_subscribed: boolean
}

/** Response shape from POST /handle-interaction (save toggle). */
export interface SaveToggleResponse {
  success: boolean
  status: 'saved' | 'unsaved'
  message?: string
  error?: string
}

/** A saved item as returned by GET /api/auth/profile. */
export interface ProfileSavedItem {
  id: number
  name: string
  slug: string
  brand: string | null
  category: string | null
  images: { path: string }[]
  min_price: number
}

/** Full profile response data shape. */
export interface ProfileData {
  user: AuthUser
  saved_items: ProfileSavedItem[]
  saved_item_ids: number[]
  alert_item_ids: number[]
}

// ── Catalog API ──────────────────────────────────────────────────────────────

export const fetchItems = async (params: Record<string, unknown> = {}) => {
  const res = await api.get<{ success: boolean; data: { items: Item[]; pagination: Pagination } }>(
    '/api/items', { params }
  )
  return res.data.data
}

export const fetchItem = async (id: number) => {
  const res = await api.get<{ 
    success: boolean; 
    data: { item: Item; clones: Clone[]; similar: Clone[]; recommended: Item[] } 
  }>(
    `/api/items/${id}`
  )
  return res.data.data
}

export const searchItems = async (q: string) => {
  const res = await api.get<{ success: boolean; data: { results: Item[]; count: number; query: string } }>(
    '/api/search', { params: { q } }
  )
  return res.data.data
}

export const fetchCompareItems = async (ids: number[]) => {
  if (!ids || ids.length === 0) return { items: [], winner_id: null, seo: null }
  const res = await api.post<{ success: boolean; data: { items: Item[]; winner_id: number; seo: any } }>('/api/compare', { ids })
  return res.data.data
}

export const fetchFilters = async () => {
  const res = await api.get<{ success: boolean; data: { categories: FilterOption[]; brands: FilterOption[] } }>(
    '/api/filters'
  )
  return res.data.data
}

// ── Auth API ──────────────────────────────────────────────────────────────────

export const fetchMe = async (): Promise<AuthUser | null> => {
  try {
    const res = await api.get<{ success: boolean; data: AuthUser }>('/api/auth/me')
    return res.data.data
  } catch {
    return null
  }
}

export const login = async (email: string, password: string) => {
  const res = await api.post<{ success: boolean; data: AuthUser }>('/api/auth/login', { email, password })
  return res.data.data
}

export const register = async (email: string, password: string, subscribe = false) => {
  const res = await api.post<{ success: boolean; data: AuthUser }>('/api/auth/register', {
    email, password, subscribe,
  })
  return res.data.data
}

export const logout = async () => {
  await api.post('/api/auth/logout')
}

// ── Interaction API ───────────────────────────────────────────────────────────

export const toggleSaveItem = async (id: number): Promise<SaveToggleResponse> => {
  const formData = new URLSearchParams()
  formData.append('type', 'item')
  formData.append('id', id.toString())
  formData.append('interaction_type', 'save')

  const res = await api.post<SaveToggleResponse>('/handle-interaction', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export const fetchProfile = async (): Promise<{ success: boolean; data: ProfileData }> => {
  const res = await api.get<{ success: boolean; data: ProfileData }>('/api/auth/profile')
  return res.data
}

// TODO: connect this endpoint in future UI
export const subscribeNewsletter = async (email: string) => {
  // Backend reads request.form.get('email') and request.form.get('mode'),
  // so we MUST send URLSearchParams — NOT a plain object.
  // Axios only form-encodes when given a URLSearchParams instance.
  const body = new URLSearchParams()
  body.append('email', email)
  body.append('mode', 'guest')

  const res = await api.post('/subscribe', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export const subscribePriceAlert = async (itemId: number, email: string, targetPrice: number) => {
  const res = await api.post('/alerts/subscribe', {
    item_id: itemId, email, target_price: targetPrice,
  })
  return res.data
}

export const deletePriceAlert = async (itemId: number) => {
  const res = await api.delete(`/api/alerts/item/${itemId}`)
  return res.data
}

export const recordClick = async (linkId: number) => {
  const res = await api.post<{ redirect_url: string }>(`/item-click/${linkId}`)
  return res.data
}

// TODO: connect this endpoint in future UI
export const quizRecommend = async (answers: Record<string, string>) => {
  const res = await api.post('/api/quiz/recommend', answers)
  return res.data
}

// ── Price History ─────────────────────────────────────────────────────────────

// TODO: connect this endpoint in future UI
export const fetchPriceHistory = async (itemId: number) => {
  const res = await api.get(`/api/items/${itemId}/price-history`)
  return res.data
}

// ── Admin API ─────────────────────────────────────────────────────────────────

// TODO: connect this endpoint in future UI
export const fetchAdminUsers = async () => {
  const res = await api.get<any[]>('/admin/api/users')
  return res.data
}

// TODO: connect this endpoint in future UI
export const fetchAdminMessages = async () => {
  const res = await api.get<any[]>('/admin/api/messages')
  return res.data
}

// TODO: connect this endpoint in future UI
export const fetchAdminNewsletter = async () => {
  const res = await api.get<any[]>('/admin/api/newsletter')
  return res.data
}
// ── Notifications API ─────────────────────────────────────────────────────────

export const fetchNotifications = async () => {
  const res = await api.get('/api/notifications')
  return res.data
}

// TODO: connect this endpoint in future UI
export const readNotification = async (id: number) => {
  const res = await api.post(`/api/notifications/${id}/read`)
  return res.data
}

export const readAllNotifications = async () => {
  const res = await api.post('/api/notifications/read-all')
  return res.data
}
// TODO: connect this endpoint in future UI
export const fetchAdminStats = async () => {
  const res = await api.get('/admin/stats')
  return res.data
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** 
 * 🖼️ Professional Image URL Resolver
 * Resolves static paths from Flask to accessible URLs for React.
 */
export const imageUrl = (path: string | null | undefined) => {
  if (!path) return '/placeholder.jpg';
  
  // 1. If it's already an absolute external URL, return as is
  if (path.startsWith('http')) return path;
  
  // 2. Clean the path (remove leading slashes to prevent double slashes)
  let cleanPath = path.trim();
  while (cleanPath.startsWith('/')) {
    cleanPath = cleanPath.slice(1);
  }

  // 3. Prevent double 'static/' prefix if it's already in the DB path
  if (cleanPath.startsWith('static/')) {
    cleanPath = cleanPath.replace('static/', '');
  }
  
  // 4. Final resolve - served via Flask /static endpoint
  return `/static/${cleanPath}`;
}

export default api
