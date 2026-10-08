import axios from 'axios'

export function getBaseURL() {
  if (import.meta.env.DEV) return '/api'
  if (window.location.protocol === 'file:') {
    const saved = localStorage.getItem('server_url')
    return (saved || 'https://promptly-equation-cinch.ngrok-free.dev') + '/api'
  }
  return '/api'
}

const api = axios.create({ baseURL: getBaseURL() })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  config.headers['ngrok-skip-browser-warning'] = 'true'
  return config
})

export function setServerURL(url) {
  localStorage.setItem('server_url', url)
  api.defaults.baseURL = url + '/api'
}

export default api
