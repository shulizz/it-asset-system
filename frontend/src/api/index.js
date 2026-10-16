import axios from 'axios'

export const DEFAULT_SERVER_URL = 'https://slzz.cloud'

export function getServerURL() {
  const saved = localStorage.getItem('server_url')
  const legacy = ['https://promptly-equation-cinch.ngrok-free.dev', 'http://134.175.25.196:8000']
  if (saved && legacy.includes(saved.replace(/\/+$/, ''))) {
    localStorage.setItem('server_url', DEFAULT_SERVER_URL)
    return DEFAULT_SERVER_URL
  }
  return saved || DEFAULT_SERVER_URL
}

export function getBaseURL() {
  if (import.meta.env.DEV) return '/api'
  if (window.location.protocol === 'file:') {
    return getServerURL() + '/api'
  }
  return '/api'
}

const api = axios.create({ baseURL: getBaseURL() })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export function setServerURL(url) {
  localStorage.setItem('server_url', url)
  api.defaults.baseURL = url + '/api'
}

export default api
