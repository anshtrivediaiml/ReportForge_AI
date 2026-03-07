import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import { useAuthStore } from '@/store/authStore'
import { getCurrentUser } from '@/services/api'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login: setAuth } = useAuthStore()
  
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        // Get tokens from URL params (OAuth callback)
        const accessToken = searchParams.get('access_token')
        const refreshToken = searchParams.get('refresh_token')

        if (accessToken && refreshToken) {
          // Fetch user info
          try {
            // Temporarily set token to fetch user
            const originalAuth = api.defaults.headers.common['Authorization']
            api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
            
            const user = await getCurrentUser()
            
            // Restore original auth header (will be set by interceptor)
            if (originalAuth) {
              api.defaults.headers.common['Authorization'] = originalAuth
            } else {
              delete api.defaults.headers.common['Authorization']
            }
            
            // Store auth state
            setAuth(accessToken, refreshToken, user)
            
            setStatus('success')
            toast.success('Login successful!')
            
            // Redirect to upload page after a brief delay
            setTimeout(() => {
              navigate('/upload')
            }, 1500)
          } catch (userError: any) {
            console.error('Failed to fetch user:', userError)
            setError('Failed to fetch user information')
            setStatus('error')
          }
        } else {
          // No tokens in URL - might be direct access or error
          const errorParam = searchParams.get('error')
          if (errorParam) {
            setError(errorParam)
            setStatus('error')
          } else {
            // No tokens and no error - redirect to login
            toast.error('Invalid callback. Redirecting to login...')
            setTimeout(() => {
              navigate('/login')
            }, 2000)
          }
        }
      } catch (err: any) {
        console.error('OAuth callback error:', err)
        setError(err.message || 'Authentication failed')
        setStatus('error')
      }
    }

    handleOAuthCallback()
  }, [searchParams, navigate, setAuth])

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-transparent to-accent-purple/20" />
      
      <div className="relative z-10 text-center">
        <Card className="max-w-md mx-auto p-8">
          {status === 'loading' && (
            <>
              <Loader2 className="w-16 h-16 text-primary-400 mx-auto mb-4 animate-spin" />
              <h2 className="text-2xl font-bold text-text-primary mb-2">
                Completing authentication...
              </h2>
              <p className="text-text-secondary">
                Please wait while we sign you in
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-text-primary mb-2">
                Authentication Successful!
              </h2>
              <p className="text-text-secondary mb-4">
                Redirecting you to the dashboard...
              </p>
            </>
          )}

          {status === 'error' && (
            <>
              <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-text-primary mb-2">
                Authentication Failed
              </h2>
              <p className="text-text-secondary mb-4">
                {error || 'An error occurred during authentication'}
              </p>
              <Button
                onClick={() => navigate('/login')}
                className="mt-4"
              >
                Go to Login
              </Button>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}

