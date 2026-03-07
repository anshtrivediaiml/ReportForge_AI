import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies/sessions
})

// Request interceptor - Add JWT token to requests
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const state = useAuthStore.getState()
    
    // Wait for hydration if not complete yet (should be very fast)
    if (!state._hasHydrated) {
      // Wait up to 200ms for hydration to complete
      let attempts = 0
      while (!state._hasHydrated && attempts < 20) {
        await new Promise(resolve => setTimeout(resolve, 10))
        const currentState = useAuthStore.getState()
        if (currentState._hasHydrated) {
          break
        }
        attempts++
      }
    }
    
    const { accessToken } = useAuthStore.getState()
    
    // Add Authorization header if token exists
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle token refresh and errors
api.interceptors.response.use(
  (response) => {
    // Success - just return the response
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    
    // Handle 401 Unauthorized - Token expired or invalid
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const { refreshToken, logout } = useAuthStore.getState()
      
      // If no refresh token, logout immediately
      if (!refreshToken) {
        logout()
        toast.error('Session expired. Please login again.')
        window.location.href = '/login'
        return Promise.reject(error)
      }
      
      try {
        // Attempt to refresh the token
        const response = await axios.post(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken },
          { withCredentials: true }
        )
        
        // Handle both wrapped and direct responses
        const data = response.data.data || response.data
        const { access_token } = data
        
        // Update token in store
        useAuthStore.getState().setTokens(access_token)
        
        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }
        
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed - logout user
        logout()
        toast.error('Session expired. Please login again.')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    // Handle other errors
    if (error.response?.status === 403) {
      toast.error('Access denied. You don\'t have permission to perform this action.')
    } else if (error.response?.status === 404) {
      // Don't show toast for 404s - let components handle it
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.')
    }
    
    return Promise.reject(error)
  }
)

export default api

