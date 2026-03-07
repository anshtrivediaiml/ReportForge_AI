import { useState, useEffect } from 'react'
import { Link2, Copy, Trash2, Eye, Calendar, Lock, Globe, Check } from 'lucide-react'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import { listSharedReports, deleteShareLink, type ShareReportResponse } from '@/services/api'
import { formatDate } from '@/utils/formatters'
import toast from 'react-hot-toast'
import Skeleton from '@/components/common/Skeleton'
import ConfirmDialog from '@/components/common/ConfirmDialog'

export default function SharedReportsPage() {
  const [shares, setShares] = useState<ShareReportResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [selectedShareId, setSelectedShareId] = useState<string | null>(null)
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null)

  useEffect(() => {
    fetchShares()
  }, [])

  const fetchShares = async () => {
    setLoading(true)
    try {
      const response = await listSharedReports()
      setShares(response.shares)
    } catch (error: any) {
      console.error('Failed to fetch shared reports:', error)
      toast.error(error.response?.data?.detail || 'Failed to load shared reports')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedShareId) return

    setDeletingId(selectedShareId)
    try {
      await deleteShareLink(selectedShareId)
      toast.success('Share link deleted successfully')
      fetchShares()
    } catch (error: any) {
      console.error('Failed to delete share link:', error)
      toast.error(error.response?.data?.detail || 'Failed to delete share link')
    } finally {
      setDeletingId(null)
      setShowDeleteDialog(false)
      setSelectedShareId(null)
    }
  }

  const handleCopy = (url: string) => {
    navigator.clipboard.writeText(url)
    setCopiedUrl(url)
    toast.success('Link copied to clipboard!')
    setTimeout(() => setCopiedUrl(null), 2000)
  }

  const isExpired = (expiresAt: string | null) => {
    if (!expiresAt) return false
    return new Date(expiresAt) < new Date()
  }

  if (loading) {
    return (
      <div className="container mx-auto px-6 py-12 max-w-6xl">
        <Skeleton variant="text" className="h-8 w-64 mb-6" />
        <SkeletonList items={5} />
      </div>
    )
  }

  return (
    <>
      <div className="container mx-auto px-6 py-12 max-w-6xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold gradient-text mb-2">Shared Reports</h1>
            <p className="text-text-secondary">Manage your shared report links</p>
          </div>
        </div>

        {shares.length === 0 ? (
          <Card className="p-12 text-center">
            <Link2 className="w-16 h-16 text-text-muted mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">No shared reports</h2>
            <p className="text-text-secondary mb-6">
              Share reports from the History page to create shareable links
            </p>
            <Button onClick={() => window.location.href = '/history'}>
              Go to History
            </Button>
          </Card>
        ) : (
          <div className="space-y-4">
            {shares.map((share) => (
              <Card key={share.share_id} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`p-2 rounded-lg ${share.is_active && !isExpired(share.expires_at) ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                        {share.requires_password ? (
                          <Lock className={`w-5 h-5 ${share.is_active && !isExpired(share.expires_at) ? 'text-green-400' : 'text-red-400'}`} />
                        ) : (
                          <Globe className={`w-5 h-5 ${share.is_active && !isExpired(share.expires_at) ? 'text-green-400' : 'text-red-400'}`} />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            share.is_active && !isExpired(share.expires_at)
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}>
                            {share.is_active && !isExpired(share.expires_at) ? 'Active' : 'Inactive'}
                          </span>
                          {share.requires_password && (
                            <span className="px-2 py-1 rounded text-xs font-semibold bg-blue-500/20 text-blue-400 flex items-center gap-1">
                              <Lock className="w-3 h-3" />
                              Password Protected
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-text-muted">
                          Created {formatDate(share.created_at)}
                        </p>
                      </div>
                    </div>

                    <div className="mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <input
                          type="text"
                          value={share.share_url}
                          readOnly
                          className="flex-1 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-text-primary text-sm"
                        />
                        <Button
                          onClick={() => handleCopy(share.share_url)}
                          variant="outline"
                          className="px-4"
                        >
                          {copiedUrl === share.share_url ? (
                            <Check className="w-4 h-4" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <div className="flex items-center gap-6 text-sm text-text-secondary">
                      <div className="flex items-center gap-2">
                        <Eye className="w-4 h-4" />
                        <span>{share.access_count} views</span>
                      </div>
                      {share.expires_at && (
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          <span>
                            Expires {formatDate(share.expires_at)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="ml-4">
                    <Button
                      onClick={() => {
                        setSelectedShareId(share.share_id)
                        setShowDeleteDialog(true)
                      }}
                      variant="outline"
                      className="text-red-400 hover:text-red-300 hover:border-red-400"
                      disabled={deletingId === share.share_id}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setSelectedShareId(null)
        }}
        onConfirm={handleDelete}
        title="Delete Share Link"
        message="Are you sure you want to delete this share link? It will no longer be accessible."
        confirmText="Delete"
        variant="danger"
      />
    </>
  )
}

// Helper component for skeleton list
function SkeletonList({ items }: { items: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: items }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" className="h-32" />
      ))}
    </div>
  )
}

