import { ReactNode, useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Loader2 } from 'lucide-react'

interface ProtectedRouteProps {
  children: ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const authState = useAuthStore()
  const [isHydrated, setIsHydrated] = useState(authState._hasHydrated)
  const location = useLocation()

  // Wait for Zustand to hydrate from localStorage
  useEffect(() => {
    if (authState._hasHydrated) {
      setIsHydrated(true)
    } else {
      // If not hydrated yet, check periodically (should be very fast)
      const timer = setTimeout(() => {
        setIsHydrated(true) // Set to true anyway after a short delay to prevent infinite loading
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [authState._hasHydrated])

  // Show loading while hydrating
  if (!isHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-primary">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin mx-auto mb-4" />
          <p className="text-text-secondary">Loading...</p>
        </div>
      </div>
    )
  }

  const isAuthenticated = !!(authState.accessToken && authState.user)

  if (!isAuthenticated) {
    // Redirect to login with return URL
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />
  }

  return <>{children}</>
}

