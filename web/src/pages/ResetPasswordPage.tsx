import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { Lock, Eye, EyeOff, Loader2, ArrowLeft, CheckCircle } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import { confirmPasswordReset } from '@/services/api'
import toast from 'react-hot-toast'

export default function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  
  // Password validation helpers
  const getPasswordRequirements = () => {
    return {
      minLength: newPassword.length >= 8,
      hasUppercase: /[A-Z]/.test(newPassword),
      hasLowercase: /[a-z]/.test(newPassword),
      hasDigit: /[0-9]/.test(newPassword),
      hasSpecialChar: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(newPassword),
      passwordsMatch: newPassword === confirmPassword && confirmPassword.length > 0
    }
  }

  useEffect(() => {
    if (!token) {
      toast.error('Invalid reset token. Please request a new password reset.')
      navigate('/forgot-password')
    }
  }, [token, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!token) {
      toast.error('Invalid reset token')
      return
    }
    
    // Password validation
    const requirements = getPasswordRequirements()
    
    if (!requirements.minLength) {
      toast.error('Password must be at least 8 characters long')
      return
    }
    
    if (!requirements.hasUppercase) {
      toast.error('Password must contain at least one uppercase letter')
      return
    }
    
    if (!requirements.hasLowercase) {
      toast.error('Password must contain at least one lowercase letter')
      return
    }
    
    if (!requirements.hasDigit) {
      toast.error('Password must contain at least one digit (0-9)')
      return
    }
    
    if (!requirements.hasSpecialChar) {
      toast.error('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
      return
    }

    if (!requirements.passwordsMatch) {
      toast.error('Passwords do not match')
      return
    }
    
    setLoading(true)
    try {
      await confirmPasswordReset({ token, new_password: newPassword })
      setSuccess(true)
      toast.success('Password reset successfully!')
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to reset password')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return null
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-transparent to-accent-purple/20" />
        
        <div className="relative z-10 w-full max-w-md">
          <Card className="p-8 text-center">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-text-primary mb-2">
              Password Reset Successful!
            </h2>
            <p className="text-text-secondary mb-6">
              Your password has been reset. Redirecting to login...
            </p>
            <Link to="/login">
              <Button>Go to Login</Button>
            </Link>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-transparent to-accent-purple/20" />
      
      <div className="relative z-10 w-full max-w-md">
        <Card className="p-8">
          <Link to="/login" className="inline-flex items-center text-text-secondary hover:text-text-primary mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Login
          </Link>
          
          <h2 className="text-3xl font-bold text-text-primary mb-2 gradient-text">
            Reset Password
          </h2>
          <p className="text-text-secondary mb-8">
            Enter your new password below.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-text-secondary mb-2">
                New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  id="newPassword"
                  className="w-full pl-10 pr-10 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-text-primary"
                >
                  {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {/* Password Requirements */}
              {newPassword && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs font-medium text-text-secondary mb-2">Password requirements:</p>
                  <div className="space-y-1">
                    <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().minLength ? 'text-green-400' : 'text-text-muted'}`}>
                      <span>{getPasswordRequirements().minLength ? '[OK]' : '[ ]'}</span>
                      <span>At least 8 characters</span>
                    </div>
                    <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().hasUppercase ? 'text-green-400' : 'text-text-muted'}`}>
                      <span>{getPasswordRequirements().hasUppercase ? '[OK]' : '[ ]'}</span>
                      <span>One uppercase letter (A-Z)</span>
                    </div>
                    <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().hasLowercase ? 'text-green-400' : 'text-text-muted'}`}>
                      <span>{getPasswordRequirements().hasLowercase ? '[OK]' : '[ ]'}</span>
                      <span>One lowercase letter (a-z)</span>
                    </div>
                    <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().hasDigit ? 'text-green-400' : 'text-text-muted'}`}>
                      <span>{getPasswordRequirements().hasDigit ? '[OK]' : '[ ]'}</span>
                      <span>One digit (0-9)</span>
                    </div>
                    <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().hasSpecialChar ? 'text-green-400' : 'text-text-muted'}`}>
                      <span>{getPasswordRequirements().hasSpecialChar ? '[OK]' : '[ ]'}</span>
                      <span>One special character (!@#$%^&*...)</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-text-secondary mb-2">
                Confirm New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  className="w-full pl-10 pr-10 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-text-primary"
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {/* Password Match Indicator */}
              {confirmPassword && (
                <div className="mt-1">
                  {getPasswordRequirements().passwordsMatch ? (
                    <p className="text-xs text-green-400 flex items-center gap-1">
                      <span>[OK]</span>
                      <span>Passwords match</span>
                    </p>
                  ) : (
                    <p className="text-xs text-red-400 flex items-center gap-1">
                      <span>[X]</span>
                      <span>Passwords do not match</span>
                    </p>
                  )}
                </div>
              )}
            </div>

            <Button type="submit" className="w-full py-3" disabled={loading}>
              {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : null}
              Reset Password
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}

