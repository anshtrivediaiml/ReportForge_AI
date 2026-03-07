import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { X, Download, Loader2, FileText, AlertCircle } from 'lucide-react'
import Button from '@/components/common/Button'
import { getSharedReportViewUrl, getSharedReportFile } from '@/services/api'
import toast from 'react-hot-toast'
import mammoth from 'mammoth'

export default function SharedReportViewerPage() {
  const { shareToken } = useParams<{ shareToken: string }>()
  const [htmlContent, setHtmlContent] = useState<string>('')
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [filename, setFilename] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (shareToken) {
      loadDocument()
    } else {
      setError('Invalid share token')
      setLoading(false)
    }
  }, [shareToken])

  const loadDocument = async () => {
    if (!shareToken) return

    setLoading(true)
    setError(null)

    try {
      // Get file info first to validate the share token
      const viewData = await getSharedReportViewUrl(shareToken)
      setDownloadUrl(viewData.download_url)
      setFilename(viewData.filename)

      // Fetch the DOCX file as blob
      // This endpoint is public and doesn't require authentication
      const blob = await getSharedReportFile(shareToken)

      if (!blob || blob.size === 0) {
        throw new Error('Document file is empty or could not be loaded')
      }

      // Convert DOCX to HTML using mammoth.js
      const result = await mammoth.convertToHtml({ arrayBuffer: await blob.arrayBuffer() })
      
      if (!result.value || result.value.trim().length === 0) {
        throw new Error('Document appears to be empty or could not be converted')
      }
      
      setHtmlContent(result.value)
      
      // Show warnings if any
      if (result.messages.length > 0) {
        console.warn('Document conversion warnings:', result.messages)
        // Don't show toast for warnings, just log them
      }

      toast.success('Document preview loaded successfully!')
    } catch (error: any) {
      console.error('Failed to load document:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load document preview'
      setError(errorMessage)
      
      // Show more specific error messages
      if (error.response?.status === 404) {
        toast.error('Report not found. The shared link may be invalid or expired.')
      } else if (error.response?.status === 410) {
        toast.error('This shared link has expired or been deactivated.')
      } else if (error.response?.status === 401) {
        toast.error('Access denied. Please check if the link requires a password.')
      } else {
        toast.error('Failed to load document preview. Please try downloading the file instead.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (downloadUrl) {
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = filename || 'report.docx'
      a.target = '_blank'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      toast.success('Download started')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-400 animate-spin mx-auto mb-4" />
          <p className="text-text-secondary">Loading document preview...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2 text-text-primary">Unable to Load Document</h2>
          <p className="text-text-secondary mb-6">{error}</p>
          <div className="flex gap-3 justify-center">
            <Button onClick={loadDocument} variant="outline">Retry</Button>
            <Button onClick={() => window.close()}>Close</Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-700 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-primary-400" />
          <h1 className="text-lg font-semibold text-text-primary">{filename || 'Document Viewer'}</h1>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={handleDownload} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          <Button onClick={() => window.close()} variant="outline" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Document Content */}
      <div className="flex-1 overflow-auto bg-slate-100 dark:bg-slate-800">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div 
            className="bg-white dark:bg-slate-900 rounded-lg shadow-xl p-8 md:p-12 document-preview"
            style={{
              minHeight: '100%',
              color: '#1e293b',
            }}
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        </div>
      </div>

      <style>{`
        .document-preview {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          line-height: 1.6;
          color: #1e293b;
        }
        .document-preview h1,
        .document-preview h2,
        .document-preview h3,
        .document-preview h4,
        .document-preview h5,
        .document-preview h6 {
          margin-top: 1.5em;
          margin-bottom: 0.75em;
          font-weight: 600;
          line-height: 1.25;
          color: #0f172a;
        }
        .document-preview h1 {
          font-size: 2em;
          border-bottom: 2px solid #e2e8f0;
          padding-bottom: 0.5em;
        }
        .document-preview h2 {
          font-size: 1.5em;
          border-bottom: 1px solid #e2e8f0;
          padding-bottom: 0.3em;
        }
        .document-preview h3 {
          font-size: 1.25em;
        }
        .document-preview p {
          margin-bottom: 1em;
        }
        .document-preview ul,
        .document-preview ol {
          margin-bottom: 1em;
          padding-left: 2em;
        }
        .document-preview li {
          margin-bottom: 0.5em;
        }
        .document-preview table {
          width: 100%;
          border-collapse: collapse;
          margin: 1.5em 0;
        }
        .document-preview table th,
        .document-preview table td {
          border: 1px solid #e2e8f0;
          padding: 0.75em;
          text-align: left;
        }
        .document-preview table th {
          background-color: #f8fafc;
          font-weight: 600;
        }
        .document-preview strong {
          font-weight: 600;
        }
        .document-preview em {
          font-style: italic;
        }
        .document-preview code {
          background-color: #f1f5f9;
          padding: 0.2em 0.4em;
          border-radius: 0.25em;
          font-family: 'Courier New', monospace;
          font-size: 0.9em;
        }
        .document-preview blockquote {
          border-left: 4px solid #3b82f6;
          padding-left: 1em;
          margin-left: 0;
          color: #64748b;
          font-style: italic;
        }
        .document-preview img {
          max-width: 100%;
          height: auto;
          border-radius: 0.5em;
          margin: 1em 0;
        }
        .document-preview a {
          color: #3b82f6;
          text-decoration: underline;
        }
        .document-preview a:hover {
          color: #2563eb;
        }
      `}</style>
    </div>
  )
}
