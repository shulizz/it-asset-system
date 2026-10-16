import { ref } from 'vue'
import api from './api'

function savedUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
}

export const currentUser = ref(savedUser())
let generation = 0
let activeRequest = null

export function setCurrentUser(user) {
  generation++
  currentUser.value = user
  localStorage.setItem('user', JSON.stringify(user))
}

export function clearSession() {
  generation++
  currentUser.value = {}
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export function refreshCurrentUser(signal) {
  const token = localStorage.getItem('token')
  if (!token) return Promise.resolve(currentUser.value)
  if (activeRequest) return activeRequest
  const startedGeneration = generation
  const request = api
    .get('/auth/me', { signal })
    .then(({ data }) => {
      if (generation === startedGeneration && localStorage.getItem('token') === token)
        setCurrentUser(data)
      return currentUser.value
    })
    .catch((error) => {
      if (
        error.response?.status === 401 &&
        generation === startedGeneration &&
        localStorage.getItem('token') === token
      )
        clearSession()
      throw error
    })
    .finally(() => {
      if (activeRequest === request) activeRequest = null
    })
  activeRequest = request
  return request
}
