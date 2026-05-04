import axios from 'axios'

const API = axios.create({
  baseURL: '/api/admin',
  withCredentials: true,
})

// Dashboard Stats
export const fetchAdminStats = async () => {
  const res = await axios.get('/api/admin/stats', { withCredentials: true })
  return res.data
}

// Items
export const fetchAdminItems = async () => {
  const res = await API.get('/items')
  return res.data
}

export const fetchAdminFormMeta = async () => {
  const res = await API.get('/items/form-data')
  return res.data
}

export const addAdminItem = async (formData: FormData) => {
  const res = await API.post('/items', formData)
  return res.data
}

export const updateAdminItem = async (id: number, formData: FormData) => {
  const res = await API.put(`/items/${id}`, formData)
  return res.data
}

export const deleteAdminItem = async (id: number) => {
  const res = await API.delete(`/items/${id}`)
  return res.data
}

// Users & Messages
export const fetchAdminUsers = async () => {
  const res = await API.get('/users')
  return res.data
}

export const fetchAdminMessages = async () => {
  const res = await API.get('/messages')
  return res.data
}

export const markMessageRead = async (id: number) => {
  const res = await API.post(`/messages/${id}/read`)
  return res.data
}

export const deleteAdminMessage = async (id: number) => {
  const res = await API.delete(`/messages/${id}`)
  return res.data
}

export const fetchAdminNewsletter = async () => {
  const res = await API.get('/newsletter')
  return res.data
}

// Expert Analytics
export const fetchAdminAnalytics = async () => {
  const res = await axios.get('/api/admin/expert-analytics/data', { withCredentials: true })
  return res.data
}

export const exportAnalyticsCSV = () => {
  window.location.href = '/api/admin/expert-analytics/export'
}

// Settings
export const fetchAdminSettings = async () => {
  const res = await API.get('/settings')
  return res.data
}

export const updateAdminSettings = async (data: any) => {
  const res = await API.put('/settings', data)
  return res.data
}

export const fetchAdminBrands = async () => {
  const res = await API.get('/brands')
  return res.data
}

export const addAdminBrand = async (name: string) => {
  const res = await API.post('/brands', { name })
  return res.data
}

export const deleteAdminBrand = async (id: number) => {
  const res = await API.delete(`/brands/${id}`)
  return res.data
}

export const fetchAdminCategories = async () => {
  const res = await API.get('/categories')
  return res.data
}

export const addAdminCategory = async (name: string) => {
  const res = await API.post('/categories', { name })
  return res.data
}

export const deleteAdminCategory = async (id: number) => {
  const res = await API.delete(`/categories/${id}`)
  return res.data
}
