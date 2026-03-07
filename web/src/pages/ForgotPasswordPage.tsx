import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Loader2, ArrowLeft } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import { requestPasswordReset } from '@/services/api'
import toast from 'react-hot-toast'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [resetUrl, setResetUrl] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await requestPasswordReset(email)
      setSent(true)
      if (response.reset_url) {
        setResetUrl(response.reset_url)
        toast.success('Password reset link generated! Check the console for the link (development mode).')
      } else {
        toast.success('If an account exists with this email, a password reset link has been sent.')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send password reset email')
    } finally {
      setLoading(false)
    }
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
            Forgot Password?
          </h2>
          <p className="text-text-secondary mb-8">
            Enter your email address and we'll send you a link to reset your password.
          </p>

          {!sent ? (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-text-secondary mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="email"
                    id="email"
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>
              <Button type="submit" className="w-full py-3" disabled={loading}>
                {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : null}
                Send Reset Link
              </Button>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="bg-primary-900/20 border border-primary-500/30 rounded-lg p-4">
                <p className="text-text-primary">
                  If an account exists with this email, a password reset link has been sent.
                </p>
                {resetUrl && (
                  <div className="mt-4 p-3 bg-slate-800 rounded text-sm">
                    <p className="text-text-muted mb-2">Development Mode - Reset Link:</p>
                    <a
                      href={resetUrl}
                      className="text-primary-400 hover:underline break-all"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {resetUrl}
                    </a>
                  </div>
                )}
              </div>
              <Link to="/login">
                <Button variant="outline" className="w-full">
                  Back to Login
                </Button>
              </Link>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

