import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：注入 Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res.data,
  err => {
    // 401 说明登录失效
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      // 如果不是在登录页，则跳转
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    const msg = err.response?.data?.detail || err.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default api

// ─── API 模块 ───────────────────────────────────────────────

export const authApi = {
  login: (data) => {
    const formData = new FormData()
    formData.append('username', data.username)
    formData.append('password', data.password)
    return api.post('/auth/login', formData)
  },
  me: () => api.get('/auth/me'),
  logs: () => api.get('/auth/logs'),
}

export const userApi = {
  list: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  updatePassword: (data) => api.put('/users/password', data),
  delete: (id) => api.delete(`/users/${id}`),
}

export const creatorApi = {
  list: () => api.get('/creators'),
  create: (data) => api.post('/creators', data),
  update: (id, data) => api.put(`/creators/${id}`, data),
  delete: (id) => api.delete(`/creators/${id}`),
  runNow: (id) => api.post(`/creators/${id}/run-now`),
  pause: (id) => api.post(`/creators/${id}/pause`),
  resume: (id) => api.post(`/creators/${id}/resume`),
}

export const videoApi = {
  list: (params) => api.get('/videos', { params }),
  get: (awemeId) => api.get(`/videos/${awemeId}`),
  streamUrl: (awemeId) => `/api/videos/${awemeId}/stream`,
}

export const notificationApi = {
  channels: () => api.get('/notifications/channels'),
  list: () => api.get('/notifications'),
  create: (data) => api.post('/notifications', data),
  update: (id, data) => api.put(`/notifications/${id}`, data),
  delete: (id) => api.delete(`/notifications/${id}`),
  test: (id) => api.post(`/notifications/${id}/test`),
}

export const aiApi = {
  trigger: (awemeId) => api.post(`/ai/summarize/${awemeId}`),
  getSummary: (awemeId) => api.get(`/ai/summary/${awemeId}`),
  providers: () => api.get('/ai/providers'),
}

export const settingApi = {
  get: (key) => api.get(`/settings/${key}`),
  set: (key, data) => api.post(`/settings/${key}`, data),
  autoFetch: () => api.post('/settings/auto-fetch'),
}

export const logApi = {
  list: (params) => api.get('/logs', { params }),
}

export const statsApi = {
  get: () => api.get('/stats'),
}
