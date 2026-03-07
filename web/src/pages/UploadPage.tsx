import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, FolderArchive, Upload, X, CheckCircle, HardDrive, AlertTriangle, Loader2 } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import { uploadFile, startGeneration, getUserStats, type StartGenerationResponse } from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import { formatBytes } from '@/utils/formatters'
import { MAX_FILE_SIZE } from '@/utils/constants'
import toast from 'react-hot-toast'

export default function UploadPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [guidelinesFile, setGuidelinesFile] = useState<File | null>(null)
  const [projectFile, setProjectFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [storageStats, setStorageStats] = useState<{ used: number; limit: number; percent: number } | null>(null)
  const [loadingStats, setLoadingStats] = useState(true)

  useEffect(() => {
    fetchStorageStats()
  }, [])

  const fetchStorageStats = async () => {
    try {
      const stats = await getUserStats()
      setStorageStats({
        used: stats.storage_used,
        limit: stats.storage_limit,
        percent: stats.storage_used_percent,
      })
    } catch (error) {
      console.error('Failed to fetch storage stats:', error)
    } finally {
      setLoadingStats(false)
    }
  }

  const handleFileSelect = (type: 'guidelines' | 'project') => (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      toast.error(`File size exceeds maximum of ${formatBytes(MAX_FILE_SIZE)}`)
      return
    }

    // Check total size with existing files
    const totalSize = (guidelinesFile?.size || 0) + (projectFile?.size || 0) + file.size
    if (storageStats && totalSize + storageStats.used > storageStats.limit) {
      const available = storageStats.limit - storageStats.used
      toast.error(`Total file size exceeds available storage. Available: ${formatBytes(available)}`)
      return
    }

    // Validate file type
    if (type === 'guidelines' && !file.name.endsWith('.pdf')) {
      toast.error('Guidelines file must be a PDF')
      return
    }

    if (type === 'project' && !file.name.endsWith('.zip')) {
      toast.error('Project file must be a ZIP archive')
      return
    }

    if (type === 'guidelines') {
      setGuidelinesFile(file)
    } else {
      setProjectFile(file)
    }
  }

  const handleGenerate = async () => {
    if (!guidelinesFile || !projectFile) {
      toast.error('Please upload both files')
      return
    }

    // Final storage check
    const totalSize = guidelinesFile.size + projectFile.size
    if (storageStats && totalSize + storageStats.used > storageStats.limit) {
      const available = storageStats.limit - storageStats.used
      toast.error(`Total file size (${formatBytes(totalSize)}) exceeds available storage. Available: ${formatBytes(available)}`)
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      // Upload files
      toast.loading('Uploading files...', { id: 'upload' })
      
      const [guidelinesResponse, projectResponse] = await Promise.all([
        uploadFile(guidelinesFile),
        uploadFile(projectFile),
      ])

      toast.success('Files uploaded successfully!', { id: 'upload' })
      setUploadProgress(50)

      // Start generation
      toast.loading('Starting report generation...', { id: 'generate' })
      
      let generationResponse
      try {
        generationResponse = await startGeneration({
          guidelines_file_id: guidelinesResponse.file_id,
          project_file_id: projectResponse.file_id,
        })
      } catch (genError: any) {
        // Check if we got a job_id despite the error (might be a response parsing issue)
        const errorData = genError.response?.data
        if (errorData?.data?.job_id || errorData?.job_id) {
          // We got a job_id, so generation actually started - navigate to processing
          const jobId = errorData.data?.job_id || errorData.job_id
          toast.success('Generation started!', { id: 'generate' })
          setUploadProgress(100)
          await fetchStorageStats()
          navigate(`/processing/${jobId}`)
          return
        }
        // Real error - re-throw to be caught by outer catch
        throw genError
      }

      // Check if we got a valid response with job_id
      if (!generationResponse?.job_id) {
        // Try to extract job_id from response data if structure is different
        const responseData = (generationResponse as any)?.data || generationResponse
        if (responseData?.job_id) {
          generationResponse = { job_id: responseData.job_id } as StartGenerationResponse
        } else {
          throw new Error('Invalid response: job_id not found')
        }
      }

      toast.success('Generation started!', { id: 'generate' })
      setUploadProgress(100)

      // Refresh storage stats
      await fetchStorageStats()

      // Navigate to processing page
      navigate(`/processing/${generationResponse.job_id}`)
    } catch (error: any) {
      // Only show error if we don't have a job_id to navigate to
      const errorData = error.response?.data
      const jobId = errorData?.data?.job_id || errorData?.job_id
      
      if (!jobId) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to start generation'
        toast.error(errorMessage, { id: 'generate' })
        console.error('Generation error:', error)
      } else {
        // We have a job_id, so generation started successfully despite the error
        toast.success('Generation started!', { id: 'generate' })
        setUploadProgress(100)
        await fetchStorageStats()
        navigate(`/processing/${jobId}`)
      }
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const canGenerate = guidelinesFile && projectFile && !uploading
  const totalSelectedSize = (guidelinesFile?.size || 0) + (projectFile?.size || 0)
  const willExceedLimit = storageStats && totalSelectedSize + storageStats.used > storageStats.limit
  const isNearLimit = storageStats && storageStats.percent > 80

  return (
    <div className="container mx-auto px-6 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-2 gradient-text text-center">Generate Report</h1>
      <p className="text-text-secondary text-center mb-8">
        Upload your guidelines PDF and project ZIP to get started
      </p>

      {/* Storage Indicator */}
      {!loadingStats && storageStats && (
        <Card className="mb-6 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <HardDrive className="w-5 h-5 text-primary-400" />
              <span className="text-sm font-medium text-text-secondary">Storage Usage</span>
            </div>
            <span className="text-sm text-text-muted">
              {formatBytes(storageStats.used)} / {formatBytes(storageStats.limit)}
            </span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2 mb-2">
            <div
              className={`h-2 rounded-full transition-all ${
                storageStats.percent > 90
                  ? 'bg-red-500'
                  : storageStats.percent > 80
                  ? 'bg-yellow-500'
                  : 'bg-gradient-to-r from-primary-500 to-accent-purple'
              }`}
              style={{ width: `${Math.min(storageStats.percent, 100)}%` }}
            />
          </div>
          {isNearLimit && (
            <div className="flex items-center gap-2 text-xs text-yellow-400 mt-2">
              <AlertTriangle className="w-4 h-4" />
              <span>Storage is {storageStats.percent.toFixed(1)}% full</span>
            </div>
          )}
        </Card>
      )}

      {/* Storage Warning */}
      {willExceedLimit && (
        <Card className="mb-6 p-4 border-yellow-500/50 bg-yellow-500/10">
          <div className="flex items-center gap-2 text-yellow-400">
            <AlertTriangle className="w-5 h-5" />
            <span className="text-sm font-medium">
              Warning: Total file size ({formatBytes(totalSelectedSize)}) will exceed your storage limit
            </span>
          </div>
        </Card>
      )}

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Guidelines Upload */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-6 h-6 text-primary-400" />
            <h3 className="text-lg font-semibold">Guidelines PDF</h3>
          </div>
          
          {guidelinesFile ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm truncate">{guidelinesFile.name}</span>
                </div>
                <button
                  onClick={() => setGuidelinesFile(null)}
                  className="text-text-muted hover:text-text-primary transition-colors flex-shrink-0 ml-2"
                  disabled={uploading}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-text-muted">{formatBytes(guidelinesFile.size)}</p>
            </div>
          ) : (
            <label className="block">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileSelect('guidelines')}
                className="hidden"
                disabled={uploading}
              />
              <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <p className="text-text-secondary">Click to upload PDF</p>
                <p className="text-xs text-text-muted mt-2">Max {formatBytes(MAX_FILE_SIZE)}</p>
              </div>
            </label>
          )}
        </Card>

        {/* Project Upload */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <FolderArchive className="w-6 h-6 text-primary-400" />
            <h3 className="text-lg font-semibold">Project ZIP</h3>
          </div>
          
          {projectFile ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm truncate">{projectFile.name}</span>
                </div>
                <button
                  onClick={() => setProjectFile(null)}
                  className="text-text-muted hover:text-text-primary transition-colors flex-shrink-0 ml-2"
                  disabled={uploading}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-text-muted">{formatBytes(projectFile.size)}</p>
            </div>
          ) : (
            <label className="block">
              <input
                type="file"
                accept=".zip"
                onChange={handleFileSelect('project')}
                className="hidden"
                disabled={uploading}
              />
              <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <p className="text-text-secondary">Click to upload ZIP</p>
                <p className="text-xs text-text-muted mt-2">Max {formatBytes(MAX_FILE_SIZE)}</p>
              </div>
            </label>
          )}
        </Card>
      </div>

      {/* Total Size Info */}
      {totalSelectedSize > 0 && (
        <div className="mb-6 text-center">
          <p className="text-sm text-text-muted">
            Total size: <span className="font-medium text-text-primary">{formatBytes(totalSelectedSize)}</span>
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/')} disabled={uploading}>
          Cancel
        </Button>
        <Button
          variant="primary"
          disabled={!canGenerate || willExceedLimit || uploading}
          onClick={handleGenerate}
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Uploading...
            </>
          ) : (
            'Generate Report'
          )}
        </Button>
      </div>

      {/* Upload Progress */}
      {uploading && (
        <div className="mt-6">
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="text-center text-sm text-text-muted mt-2">{uploadProgress}% complete</p>
        </div>
      )}
    </div>
  )
}
