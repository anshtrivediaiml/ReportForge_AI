import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

export default function VerifyEmailPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus('error')
        setMessage('No verification token provided')
        return
      }

      try {
        // Call the backend verification endpoint
        const response = await api.post(`/api/v1/auth/verify-email/${token}`)
        setStatus('success')
        setMessage(response.data.message || 'Email verified successfully!')
        toast.success('Email verified successfully!')
        
        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          navigate('/dashboard')
        }, 2000)
      } catch (error: any) {
        setStatus('error')
        const errorMessage = error.response?.data?.detail || 'Failed to verify email. The link may be invalid or expired.'
        setMessage(errorMessage)
        toast.error(errorMessage)
      }
    }

    verifyEmail()
  }, [token, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-transparent to-accent-purple/20" />
      
      <div className="relative z-10 w-full max-w-md">
        <Card className="p-8 text-center">
          {status === 'loading' && (
            <>
              <Loader2 className="w-16 h-16 text-primary-400 mx-auto mb-4 animate-spin" />
              <h2 className="text-2xl font-bold text-text-primary mb-2">
                Verifying Your Email
              </h2>
              <p className="text-text-secondary">
                Please wait while we verify your email address...
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-text-primary mb-2">
                Email Verified!
              </h2>
              <p className="text-text-secondary mb-6">
                {message}
              </p>
              <p className="text-sm text-text-muted mb-6">
                Redirecting you to the dashboard...
              </p>
              <Button onClick={() => navigate('/dashboard')}>
                Go to Dashboard
              </Button>
            </>
          )}

          {status === 'error' && (
            <>
              <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-text-primary mb-2">
                Verification Failed
              </h2>
              <p className="text-text-secondary mb-6">
                {message}
              </p>
              <div className="space-y-3">
                <Button onClick={() => navigate('/login')}>
                  Go to Login
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => navigate('/register')}
                >
                  Create New Account
                </Button>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}

