import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileQuestion, RefreshCw, Search, Edit2, Trash2, MoreVertical, Download, Loader2, ChevronLeft, ChevronRight, CheckSquare, Square, Share2 } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import Modal from '@/components/common/Modal'
import ConfirmDialog from '@/components/common/ConfirmDialog'
import { SkeletonList } from '@/components/common/Skeleton'
import ShareReportDialog from '@/components/sharing/ShareReportDialog'
import { listJobs, updateJobTitle, deleteJob, downloadReport, bulkDeleteJobs } from '@/services/api'
import { formatDate } from '@/utils/formatters'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'

export default function HistoryPage() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState<any[]>([])
  const [totalJobs, setTotalJobs] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)
  const [selectedJobs, setSelectedJobs] = useState<Set<string>>(new Set())
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [editingJob, setEditingJob] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [deletingJob, setDeletingJob] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [showMenu, setShowMenu] = useState<string | null>(null)
  const [sharingJob, setSharingJob] = useState<{ id: string; title?: string } | null>(null)
  const menuRefs = useRef<{ [key: string]: HTMLDivElement | null }>({})

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showMenu) {
        const menuElement = menuRefs.current[showMenu]
        if (menuElement && !menuElement.contains(event.target as Node)) {
          setShowMenu(null)
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showMenu])

  const fetchJobs = async (page: number = currentPage) => {
    // Ensure auth is hydrated before making request
    const authState = useAuthStore.getState()
    if (!authState._hasHydrated) {
      console.warn('Auth not hydrated yet, waiting...')
      // Wait a bit for hydration
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    setLoading(true)
    try {
      const response = await listJobs(page, pageSize)
      // Backend returns { jobs: [], total: int, page: int, page_size: int }
      const jobsList = response.jobs || []
      const total = response.total || 0
      setJobs(jobsList)
      setTotalJobs(total)
    } catch (error: any) {
      console.error('Error fetching jobs:', error)
      if (error.response?.status === 401) {
        // Unauthorized - token might be expired or invalid
        toast.error('Session expired. Please login again.')
        // The axios interceptor should handle redirect, but ensure it happens
        setTimeout(() => {
          window.location.href = '/login?redirect=' + encodeURIComponent('/history')
        }, 1000)
      } else {
        toast.error(error.response?.data?.detail || 'Failed to load job history')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Wait for auth store to hydrate before making API calls
    const authState = useAuthStore.getState()
    if (authState._hasHydrated) {
      fetchJobs(currentPage)
    } else {
      // Wait for hydration to complete
      const checkHydration = setInterval(() => {
        const state = useAuthStore.getState()
        if (state._hasHydrated) {
          clearInterval(checkHydration)
          fetchJobs(currentPage)
        }
      }, 50)
      
      // Fallback: proceed after 500ms even if hydration flag isn't set
      const timeout = setTimeout(() => {
        clearInterval(checkHydration)
        fetchJobs(currentPage)
      }, 500)
      
      return () => {
        clearInterval(checkHydration)
        clearTimeout(timeout)
      }
    }
  }, [currentPage])

  const filteredJobs = jobs.filter((job) => {
    if (!searchTerm) return true
    const search = searchTerm.toLowerCase()
    return (
      job.title?.toLowerCase().includes(search) ||
      job.output_filename?.toLowerCase().includes(search) ||
      job.guidelines_filename?.toLowerCase().includes(search) ||
      job.project_filename?.toLowerCase().includes(search) ||
      job.id?.toLowerCase().includes(search)
    )
  })

  const totalPages = Math.ceil(totalJobs / pageSize)

  const handleSelectJob = (jobId: string) => {
    setSelectedJobs((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(jobId)) {
        newSet.delete(jobId)
      } else {
        newSet.add(jobId)
      }
      return newSet
    })
  }

  const handleSelectAll = () => {
    if (selectedJobs.size === filteredJobs.length) {
      setSelectedJobs(new Set())
    } else {
      setSelectedJobs(new Set(filteredJobs.map((job) => job.id)))
    }
  }

  const handleBulkDelete = async () => {
    if (selectedJobs.size === 0) return
    
    setBulkDeleting(true)
    try {
      const result = await bulkDeleteJobs(Array.from(selectedJobs))
      toast.success(result.message || `Deleted ${result.deleted_count} report(s)`)
      setSelectedJobs(new Set())
      fetchJobs(currentPage)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete reports')
    } finally {
      setBulkDeleting(false)
    }
  }

  const handleEditClick = (job: any) => {
    setEditingJob(job.id)
    setEditTitle(job.title || job.output_filename || 'Untitled Report')
    setShowMenu(null)
  }

  const handleSaveTitle = async () => {
    if (!editingJob) return
    
    setActionLoading(editingJob)
    try {
      await updateJobTitle(editingJob, editTitle)
      toast.success('Report title updated successfully')
      setEditingJob(null)
      fetchJobs() // Refresh list
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update title')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDeleteClick = (jobId: string) => {
    setDeletingJob(jobId)
    setShowMenu(null)
  }

  const handleConfirmDelete = async () => {
    if (!deletingJob) return
    
    setActionLoading(deletingJob)
    try {
      await deleteJob(deletingJob)
      toast.success('Report deleted successfully')
      setDeletingJob(null)
      fetchJobs() // Refresh list
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete report')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDownload = async (jobId: string, filename: string) => {
    setActionLoading(jobId)
    try {
      const blob = await downloadReport(jobId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename || 'report.docx'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Report downloaded successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to download report')
    } finally {
      setActionLoading(null)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-400'
      case 'processing':
        return 'text-primary-400'
      case 'queued':
        return 'text-yellow-400'
      case 'failed':
        return 'text-red-400'
      default:
        return 'text-text-muted'
    }
  }

  if (loading && jobs.length === 0) {
    return (
      <div className="container mx-auto px-6 py-12 max-w-6xl">
        <SkeletonList items={5} />
      </div>
    )
  }

  return (
    <>
      <div className="container mx-auto px-6 py-12 max-w-6xl">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold gradient-text">Generation History</h1>
            {filteredJobs.length > 0 && (
              <button
                onClick={handleSelectAll}
                className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                title={selectedJobs.size === filteredJobs.length ? 'Deselect all' : 'Select all'}
              >
                {selectedJobs.size === filteredJobs.length ? (
                  <CheckSquare className="w-5 h-5" />
                ) : (
                  <Square className="w-5 h-5" />
                )}
              </button>
            )}
          </div>
          <Button variant="outline" onClick={() => fetchJobs(currentPage)} disabled={loading}>
            <RefreshCw className={`mr-2 w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Search and Bulk Actions */}
        <div className="mb-6 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              placeholder="Search by title, filename, or job ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-text-primary focus:outline-none focus:border-primary-500"
            />
          </div>
          
          {selectedJobs.size > 0 && (
            <div className="flex items-center justify-between p-4 bg-primary-900/20 border border-primary-500/30 rounded-lg">
              <span className="text-text-primary font-medium">
                {selectedJobs.size} report{selectedJobs.size !== 1 ? 's' : ''} selected
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setSelectedJobs(new Set())}
                  disabled={bulkDeleting}
                >
                  Clear Selection
                </Button>
                <Button
                  variant="outline"
                  onClick={handleBulkDelete}
                  disabled={bulkDeleting}
                  className="text-red-400 border-red-400 hover:bg-red-400/10"
                >
                  {bulkDeleting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Selected
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Job Cards */}
        {filteredJobs.length === 0 ? (
          <Card className="text-center py-12">
            <FileQuestion className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No reports found</h3>
            <p className="text-text-muted mb-4">Start generating your first report</p>
            <Button onClick={() => navigate('/upload')}>Create Report</Button>
          </Card>
        ) : (
          <div className="grid gap-4">
            {filteredJobs.map((job) => (
              <div
                key={job.id}
                className="relative"
                style={{ zIndex: showMenu === job.id ? 50 : 1 }}
              >
                <Card className="hover:border-primary-500 transition-colors relative overflow-visible">
                <div className="flex items-start justify-between gap-4">
                  {/* Bulk Selection Checkbox */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleSelectJob(job.id)
                    }}
                    className="mt-1 p-1 hover:bg-slate-700 rounded transition-colors"
                  >
                    {selectedJobs.has(job.id) ? (
                      <CheckSquare className="w-5 h-5 text-primary-400" />
                    ) : (
                      <Square className="w-5 h-5 text-text-muted" />
                    )}
                  </button>
                  
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => {
                      if (job.status === 'completed') {
                        navigate(`/success/${job.id}`)
                      } else if (job.status === 'processing' || job.status === 'queued') {
                        navigate(`/processing/${job.id}`)
                      }
                    }}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-text-primary">
                        {job.title || job.output_filename || 'Untitled Report'}
                      </h3>
                      <span className={`text-xs font-medium px-2 py-1 rounded ${getStatusColor(job.status)} bg-slate-700/50`}>
                        {job.status}
                      </span>
                    </div>
                    <div className="text-sm text-text-muted space-y-1">
                      {job.original_filename && (
                        <div>File: {job.original_filename}</div>
                      )}
                      <div>Created: {formatDate(job.created_at)}</div>
                      {job.status === 'completed' && job.completed_at && (
                        <div>Completed: {formatDate(job.completed_at)}</div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-2xl font-bold text-primary-400 mb-1">
                        {job.progress || 0}%
                      </div>
                      <div className="text-xs text-text-muted">Progress</div>
                    </div>
                    
                    {/* Actions Menu */}
                    <div
                      className="relative z-50"
                      ref={(el) => {
                        menuRefs.current[job.id] = el
                      }}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setShowMenu(showMenu === job.id ? null : job.id)
                        }}
                        className="p-2 rounded-lg hover:bg-slate-700 transition-colors"
                        disabled={actionLoading === job.id}
                      >
                        {actionLoading === job.id ? (
                          <Loader2 className="w-5 h-5 text-primary-400 animate-spin" />
                        ) : (
                          <MoreVertical className="w-5 h-5 text-text-muted" />
                        )}
                      </button>
                      
                      {showMenu === job.id && (
                        <div className="absolute right-0 mt-2 w-48 glass-card rounded-lg shadow-2xl border border-slate-700 overflow-hidden bg-slate-900 z-[100]">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleEditClick(job)
                            }}
                            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-slate-800 transition-colors"
                          >
                            <Edit2 className="w-4 h-4" />
                            Edit Title
                          </button>
                          {job.status === 'completed' && (
                            <>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleDownload(job.id, job.output_filename || 'report.docx')
                                  setShowMenu(null)
                                }}
                                className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-slate-800 transition-colors"
                              >
                                <Download className="w-4 h-4" />
                                Download
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  e.preventDefault()
                                  const jobToShare = { id: job.id, title: job.title || job.output_filename }
                                  console.log('Opening share dialog for job:', jobToShare)
                                  setSharingJob(jobToShare)
                                  setShowMenu(null)
                                }}
                                className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-slate-800 transition-colors"
                              >
                                <Share2 className="w-4 h-4" />
                                Share
                              </button>
                            </>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteClick(job.id)
                            }}
                            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-slate-800 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                    </div>
                  </div>
                </Card>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-700">
            <div className="text-text-secondary text-sm">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalJobs)} of {totalJobs} reports
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1 || loading}
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </Button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum: number
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-1 rounded-lg transition-colors ${
                        currentPage === pageNum
                          ? 'bg-primary-600 text-white'
                          : 'text-text-secondary hover:bg-slate-800 hover:text-text-primary'
                      }`}
                      disabled={loading}
                    >
                      {pageNum}
                    </button>
                  )
                })}
              </div>
              <Button
                variant="outline"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages || loading}
              >
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Edit Title Modal */}
      <Modal
        isOpen={editingJob !== null}
        onClose={() => {
          setEditingJob(null)
          setEditTitle('')
        }}
        title="Edit Report Title"
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Report Title
            </label>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-text-primary focus:outline-none focus:border-primary-500"
              placeholder="Enter report title"
              maxLength={200}
              autoFocus
            />
          </div>
          <div className="flex gap-3 justify-end">
            <Button
              variant="outline"
              onClick={() => {
                setEditingJob(null)
                setEditTitle('')
              }}
              disabled={actionLoading === editingJob}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveTitle}
              disabled={!editTitle.trim() || actionLoading === editingJob}
            >
              {actionLoading === editingJob ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save'
              )}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Share Report Dialog */}
      <ShareReportDialog
        jobId={sharingJob?.id || ''}
        jobTitle={sharingJob?.title}
        isOpen={sharingJob !== null}
        onClose={() => setSharingJob(null)}
        onShareCreated={() => {
          // Don't close the dialog - let user see and copy the link
          // The dialog will show its own success toast
        }}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deletingJob !== null}
        onClose={() => setDeletingJob(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Report"
        message="Are you sure you want to delete this report? This action cannot be undone and will also delete all associated files."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        loading={actionLoading === deletingJob}
      />
    </>
  )
}
