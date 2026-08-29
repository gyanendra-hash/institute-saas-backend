import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: `${API_BASE_URL}/api` })

const ACCESS_KEY = 'coaching_saas_access'
const REFRESH_KEY = 'coaching_saas_refresh'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null
  try {
    const { data } = await axios.post(`${API_BASE_URL}/api/auth/login/refresh/`, { refresh })
    localStorage.setItem(ACCESS_KEY, data.access)
    return data.access as string
  } catch {
    clearTokens()
    return null
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
    if (error.response?.status === 401 && original && !original._retried && getRefreshToken()) {
      original._retried = true
      refreshInFlight ??= refreshAccessToken().finally(() => {
        refreshInFlight = null
      })
      const newAccess = await refreshInFlight
      if (newAccess) {
        original.headers.set('Authorization', `Bearer ${newAccess}`)
        return api(original)
      }
    }
    return Promise.reject(error)
  },
)

/** DRF's PageNumberPagination envelope shape, shared by every list endpoint. */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export function apiErrorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data
    if (typeof data === 'string') return data
    if (data && typeof data === 'object') {
      if ('detail' in data && typeof data.detail === 'string') return data.detail
      const firstKey = Object.keys(data)[0]
      if (firstKey) {
        const value = (data as Record<string, unknown>)[firstKey]
        const text = Array.isArray(value) ? value.join(' ') : String(value)
        return `${firstKey}: ${text}`
      }
    }
  }
  return fallback
}
