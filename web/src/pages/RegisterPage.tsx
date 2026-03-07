import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, Lock, UserPlus, ArrowRight, User } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import { register } from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { login: setAuth } = useAuthStore()
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  })
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  
  // Password validation helpers
  const getPasswordRequirements = () => {
    const password = formData.password
    return {
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasDigit: /[0-9]/.test(password),
      hasSpecialChar: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
      passwordsMatch: formData.password === formData.confirmPassword && formData.confirmPassword.length > 0
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const validateForm = (): string | null => {
    if (!formData.email || !formData.password || !formData.confirmPassword) {
      return 'Please fill in all required fields'
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      return 'Please enter a valid email address'
    }

    // Password validation
    const requirements = getPasswordRequirements()
    
    if (!requirements.minLength) {
      return 'Password must be at least 8 characters long'
    }
    
    if (!requirements.hasUppercase) {
      return 'Password must contain at least one uppercase letter'
    }
    
    if (!requirements.hasLowercase) {
      return 'Password must contain at least one lowercase letter'
    }
    
    if (!requirements.hasDigit) {
      return 'Password must contain at least one digit (0-9)'
    }
    
    if (!requirements.hasSpecialChar) {
      return 'Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)'
    }

    if (!requirements.passwordsMatch) {
      return 'Passwords do not match'
    }

    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const validationError = validateForm()
    if (validationError) {
      toast.error(validationError)
      return
    }

    setLoading(true)
    
    try {
      const response = await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.fullName || undefined,
      })
      
      // Store auth state
      setAuth(
        response.access_token,
        response.refresh_token,
        response.user
      )
      
      toast.success('Account created successfully!')
      
      // Redirect to upload page
      navigate('/upload')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.'
      toast.error(errorMessage)
      console.error('Registration error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-transparent to-accent-purple/20" />
      
      <div className="relative z-10 w-full max-w-md">
        <Card className="space-y-6">
          {/* Header */}
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-accent-purple flex items-center justify-center">
                <UserPlus className="w-8 h-8 text-white" />
              </div>
            </div>
            <h1 className="text-3xl font-bold gradient-text mb-2">
              Create Account
            </h1>
            <p className="text-text-secondary">
              Sign up to start generating reports
            </p>
          </div>

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name Field (Optional) */}
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-text-secondary mb-2">
                Full Name <span className="text-text-muted">(Optional)</span>
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  value={formData.fullName}
                  onChange={handleChange}
                  placeholder="John Doe"
                  className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-text-primary placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-text-secondary mb-2">
                Email Address <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="you@example.com"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-text-primary placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-text-secondary mb-2">
                Password <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="At least 8 characters"
                  required
                  minLength={8}
                  className="w-full pl-10 pr-12 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-text-primary placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-500 hover:text-text-primary transition-colors text-sm"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {/* Password Requirements */}
              {formData.password && (
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

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-text-secondary mb-2">
                Confirm Password <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Re-enter your password"
                  required
                  className="w-full pl-10 pr-12 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-text-primary placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-500 hover:text-text-primary transition-colors text-sm"
                >
                  {showConfirmPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {/* Password Match Indicator */}
              {formData.confirmPassword && (
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

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? (
                'Creating account...'
              ) : (
                <>
                  Create Account
                  <ArrowRight className="ml-2 w-5 h-5" />
                </>
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-700"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-slate-800/70 text-text-muted">Or continue with</span>
            </div>
          </div>

          {/* Google OAuth Button */}
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={() => {
              window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/auth/google/login`
            }}
            disabled={loading}
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Sign up with Google
          </Button>

          {/* Links */}
          <div className="text-center space-y-2">
            <p className="text-sm text-text-muted">
              Already have an account?{' '}
              <Link
                to="/login"
                className="text-primary-400 hover:text-primary-300 font-medium transition-colors"
              >
                Sign in
              </Link>
            </p>
            <p className="text-xs text-text-muted">
              <Link
                to="/"
                className="hover:text-text-secondary transition-colors"
              >
                ← Back to home
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}

