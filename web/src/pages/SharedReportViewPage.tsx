import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Lock, Download, FileText, Calendar, User, AlertCircle, Loader2, Eye } from 'lucide-react'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import { getSharedReportInfo, accessSharedReport, getSharedReportViewUrl } from '@/services/api'
import { formatDate } from '@/utils/formatters'
import toast from 'react-hot-toast'
import Skeleton from '@/components/common/Skeleton'

export default function SharedReportViewPage() {
  const { shareToken } = useParams<{ shareToken: string }>()
  const navigate = useNavigate()
  const [reportInfo, setReportInfo] = useState<any>(null)
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(true)
  const [accessing, setAccessing] = useState(false)
  const [accessGranted, setAccessGranted] = useState(false)

  useEffect(() => {
    if (shareToken) {
      console.log('Share token from URL:', shareToken)
      fetchReportInfo()
    } else {
      setLoading(false)
      toast.error('Invalid share link')
    }
  }, [shareToken])

  const fetchReportInfo = async () => {
    if (!shareToken) {
      console.error('No share token provided')
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      console.log('Fetching shared report info for token:', shareToken)
      console.log('Token length:', shareToken.length)
      console.log('API endpoint will be:', `/api/v1/sharing/${encodeURIComponent(shareToken)}`)
      
      // FastAPI automatically URL-decodes path parameters, so we encode it for the HTTP request
      const info = await getSharedReportInfo(shareToken)
      console.log('Shared report info received:', info)
      setReportInfo(info)
      if (!info.requires_password) {
        // Auto-grant access if no password required
        await grantAccess()
      }
    } catch (error: any) {
      console.error('Failed to fetch shared report info:', error)
      console.error('Error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        url: error.config?.url,
        shareToken: shareToken,
      })
      if (error.response?.status === 410) {
        toast.error('This shared link has expired or been deactivated')
      } else if (error.response?.status === 404) {
        const detail = error.response?.data?.detail || 'Shared link not found'
        console.error('404 Error detail:', detail)
        console.error('This might mean:')
        console.error('1. The share token is incorrect')
        console.error('2. The share link was deleted')
        console.error('3. The job was deleted')
        toast.error(detail)
      } else if (error.response?.status === 500) {
        toast.error('Server error - please try again later')
        console.error('Server error:', error.response?.data)
      } else {
        toast.error(error.response?.data?.detail || 'Failed to load shared report')
      }
      setReportInfo(null)
    } finally {
      setLoading(false)
    }
  }

  const grantAccess = async (providedPassword?: string) => {
    if (!shareToken) return

    setAccessing(true)
    try {
      await accessSharedReport(shareToken, providedPassword || password)
      setAccessGranted(true)
      toast.success('Access granted!')
    } catch (error: any) {
      console.error('Failed to access shared report:', error)
      if (error.response?.status === 401) {
        toast.error('Incorrect password')
      } else {
        toast.error(error.response?.data?.detail || 'Failed to access report')
      }
    } finally {
      setAccessing(false)
    }
  }

  const handleViewReport = async () => {
    if (!shareToken || !accessGranted) {
      toast.error('Please grant access first')
      return
    }

    try {
      // Get the Google Docs Viewer URL from backend
      const viewData = await getSharedReportViewUrl(shareToken)
      
      // Use Google Docs Viewer URL (most accurate preview)
      const viewerUrl = viewData.google_docs_viewer_url || viewData.office_viewer_url || viewData.view_url
      
      if (!viewerUrl) {
        toast.error('Preview URL not available')
        return
      }

      // Open Google Docs Viewer in new tab
      const viewerWindow = window.open(viewerUrl, '_blank', 'noopener,noreferrer')
      
      if (!viewerWindow) {
        toast.error('Please allow popups to view the document')
        return
      }
      
      toast.success('Opening document in Google Docs Viewer...')
    } catch (error: any) {
      console.error('Failed to open viewer:', error)
      toast.error(error.response?.data?.detail || 'Failed to open document viewer')
    }
  }

  const handleDownload = async () => {
    if (!shareToken) return

    try {
      const viewData = await getSharedReportViewUrl(shareToken)
      const downloadUrl = viewData.download_url
      
      // Trigger download
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = viewData.filename || 'report.docx'
      a.target = '_blank'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      toast.success('Report downloaded successfully!')
    } catch (error: any) {
      console.error('Failed to download report:', error)
      toast.error(error.response?.data?.detail || 'Failed to download report')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <Skeleton variant="rectangular" className="h-96" />
        </div>
      </div>
    )
  }

  if (!reportInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-12">
        <Card className="w-full max-w-md text-center p-8">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Report Not Found</h2>
          <p className="text-text-secondary mb-6">
            This shared link may be invalid or expired.
          </p>
          <Button onClick={() => navigate('/')}>Go to Home</Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 bg-bg-primary">
      <Card className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-primary-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-primary-400" />
          </div>
          <h1 className="text-3xl font-bold gradient-text mb-2">
            {reportInfo.job_title || 'Shared Report'}
          </h1>
          {reportInfo.description && (
            <p className="text-text-secondary mb-4">{reportInfo.description}</p>
          )}
        </div>

        <div className="space-y-4 mb-6">
          <div className="flex items-center gap-3 text-text-secondary">
            <User className="w-5 h-5" />
            <span>Shared by: {reportInfo.shared_by}</span>
          </div>
          <div className="flex items-center gap-3 text-text-secondary">
            <Calendar className="w-5 h-5" />
            <span>Created: {formatDate(reportInfo.created_at)}</span>
          </div>
          {reportInfo.expires_at && (
            <div className="flex items-center gap-3 text-text-secondary">
              <Calendar className="w-5 h-5" />
              <span>Expires: {formatDate(reportInfo.expires_at)}</span>
            </div>
          )}
        </div>

        {reportInfo.requires_password && !accessGranted ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2 flex items-center gap-2">
                <Lock className="w-4 h-4" />
                Password Required
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && password) {
                    grantAccess()
                  }
                }}
                placeholder="Enter password to access"
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-text-primary placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                autoFocus
              />
            </div>
            <Button
              onClick={() => grantAccess()}
              disabled={!password || accessing}
              className="w-full"
            >
              {accessing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Access Report'
              )}
            </Button>
          </div>
        ) : accessGranted ? (
          <div className="space-y-4">
            <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
              <p className="text-green-400 text-sm text-center">
                Access granted! You can now view or download the report.
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                onClick={handleViewReport}
                variant="outline"
                className="flex-1"
              >
                <Eye className="w-4 h-4 mr-2" />
                View Report
              </Button>
              <Button onClick={handleDownload} className="flex-1">
                <Download className="w-4 h-4 mr-2" />
                Download
              </Button>
            </div>
          </div>
        ) : null}
      </Card>
    </div>
  )
}
