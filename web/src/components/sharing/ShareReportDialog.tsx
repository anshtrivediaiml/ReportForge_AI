import { useState, useEffect } from 'react'
import { X, Copy, Check, Lock, Calendar } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import { createShareLink, type ShareReportRequest } from '@/services/api'
import toast from 'react-hot-toast'

interface ShareReportDialogProps {
  jobId: string
  jobTitle?: string
  isOpen: boolean
  onClose: () => void
  onShareCreated?: () => void
}

export default function ShareReportDialog({
  jobId,
  jobTitle,
  isOpen,
  onClose,
  onShareCreated,
}: ShareReportDialogProps) {
  const [expiresInDays, setExpiresInDays] = useState<number | null>(7)
  const [requiresPassword, setRequiresPassword] = useState(false)
  const [password, setPassword] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Auto-create share link when dialog opens
  useEffect(() => {
    if (isOpen && !shareUrl && !loading && jobId) {
      let cancelled = false
      const handleAutoCreate = async () => {
        setLoading(true)
        try {
          const shareData: ShareReportRequest = {
            job_id: jobId,
            expires_in_days: 7, // Default 7 days
            requires_password: false,
            password: null,
            description: null,
            access_level: 'view',
          }

          const response = await createShareLink(shareData)
          if (!cancelled) {
            setShareUrl(response.share_url)
            toast.success('Share link created!')
            // Don't call onShareCreated here - it might close the dialog
            // onShareCreated?.()
          }
        } catch (error: any) {
          if (!cancelled) {
            console.error('Failed to create share link:', error)
            toast.error(error.response?.data?.detail || 'Failed to create share link')
          }
        } finally {
          if (!cancelled) {
            setLoading(false)
          }
        }
      }
      handleAutoCreate()
      
      return () => {
        cancelled = true
      }
    }
  }, [isOpen, jobId])

  // Reset state when dialog closes
  useEffect(() => {
    if (!isOpen) {
      setShareUrl(null)
      setExpiresInDays(7)
      setRequiresPassword(false)
      setPassword('')
      setDescription('')
      setCopied(false)
      setLoading(false)
    }
  }, [isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (requiresPassword && !password) {
      toast.error('Please enter a password')
      return
    }

    if (requiresPassword && password.length < 4) {
      toast.error('Password must be at least 4 characters')
      return
    }

    setLoading(true)
    try {
      const shareData: ShareReportRequest = {
        job_id: jobId,
        expires_in_days: expiresInDays,
        requires_password: requiresPassword,
        password: requiresPassword ? password : null,
        description: description || null,
        access_level: 'view',
      }

      const response = await createShareLink(shareData)
      setShareUrl(response.share_url)
      toast.success('Share link created successfully!')
      onShareCreated?.()
    } catch (error: any) {
      console.error('Failed to create share link:', error)
      toast.error(error.response?.data?.detail || 'Failed to create share link')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      toast.success('Link copied to clipboard!')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleClose = () => {
    setShareUrl(null)
    setExpiresInDays(7)
    setRequiresPassword(false)
    setPassword('')
    setDescription('')
    setCopied(false)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9999] flex items-center justify-center p-4"
      onClick={(e) => {
        // Close dialog when clicking outside (on the backdrop)
        if (e.target === e.currentTarget) {
          handleClose()
        }
      }}
    >
      <Card 
        className="w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => {
          // Prevent clicks inside the card from closing the dialog
          e.stopPropagation()
        }}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold gradient-text">Share Report</h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {jobTitle && (
          <p className="text-text-secondary mb-6">Sharing: {jobTitle}</p>
        )}

        {loading && !shareUrl ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-text-secondary">Creating share link...</p>
            </div>
          </div>
        ) : shareUrl ? (
          <div className="space-y-4">
            <div className="p-4 bg-slate-800 rounded-lg">
              <p className="text-sm text-text-secondary mb-2">Share Link:</p>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={shareUrl}
                  readOnly
                  className="flex-1 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-text-primary text-sm"
                />
                <Button onClick={handleCopy} variant="outline" className="px-4">
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </Button>
              </div>
            </div>
            <p className="text-xs text-text-muted text-center">
              Share this link with others. They can view and download the report.
            </p>
            <Button onClick={handleClose} className="w-full">
              Done
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Expiration */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Link Expires In
              </label>
              <select
                value={expiresInDays || ''}
                onChange={(e) => setExpiresInDays(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Never expires</option>
                <option value="1">1 day</option>
                <option value="7">7 days</option>
                <option value="30">30 days</option>
                <option value="90">90 days</option>
                <option value="365">1 year</option>
              </select>
            </div>

            {/* Password Protection */}
            <div>
              <label className="flex items-center gap-2 mb-2">
                <input
                  type="checkbox"
                  checked={requiresPassword}
                  onChange={(e) => setRequiresPassword(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-text-secondary flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Require password to access
                </span>
              </label>
              {requiresPassword && (
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password (min 4 characters)"
                  minLength={4}
                  className="w-full mt-2 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-text-primary placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Description (optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add a note about this shared report..."
                maxLength={500}
                rows={3}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-text-primary placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              />
              <p className="text-xs text-text-muted mt-1">{description.length}/500</p>
            </div>

            <div className="flex gap-2 pt-4">
              <Button type="button" onClick={handleClose} variant="outline" className="flex-1">
                Cancel
              </Button>
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? 'Creating...' : 'Create Share Link'}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  )
}

