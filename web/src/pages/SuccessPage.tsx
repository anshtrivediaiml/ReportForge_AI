import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CheckCircle, Download, FileText, Clock, ArrowRight } from 'lucide-react'
import { motion } from 'framer-motion'
import confetti from 'canvas-confetti'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import { downloadReport, getJob, type JobResponse } from '@/services/api'
import { formatBytes, formatDate } from '@/utils/formatters'
import toast from 'react-hot-toast'

export default function SuccessPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const [job, setJob] = useState<JobResponse | null>(null)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    // Fetch job details first before showing success
    if (jobId) {
      getJob(jobId)
        .then((jobData) => {
          // CRITICAL: Validate job actually completed successfully
          if (jobData.status === 'failed') {
            toast.error('Report generation failed. Please try again.')
            navigate('/upload')
            return
          }
          
          // Check if job has actual content (not empty report)
          const hasContent = (jobData.chapters_created || 0) > 0 && 
                            (jobData.sections_written || 0) > 0 &&
                            (jobData.files_analyzed || 0) > 0
          
          if (!hasContent && jobData.status === 'completed') {
            // Job marked as completed but has no content - likely failed silently
            toast.error('Report generation appears to have failed. No content was generated.')
            navigate('/upload')
            return
          }
          
          // Only show success if job is actually completed with content
          if (jobData.status === 'completed' && hasContent) {
            // Trigger confetti only for successful completion
            confetti({
              particleCount: 100,
              spread: 70,
              origin: { y: 0.6 },
            })
          }
          
          setJob(jobData)
        })
        .catch((error) => {
          console.error('Failed to fetch job:', error)
          toast.error('Failed to load job details')
          navigate('/upload')
        })
    }
  }, [jobId, navigate])

  const handleDownload = async () => {
    if (!jobId) return

    setDownloading(true)
    try {
      const blob = await downloadReport(jobId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = job?.output_filename || 'Report.docx'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Report downloaded successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to download report')
    } finally {
      setDownloading(false)
    }
  }

  if (!job) {
    return (
      <div className="container mx-auto px-6 py-12 text-center">
        <div className="text-text-muted">Loading...</div>
      </div>
    )
  }

  const generationTime = job.completed_at && job.started_at
    ? Math.floor((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000)
    : 0

  return (
    <div className="container mx-auto px-6 py-12 max-w-4xl">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200 }}
        className="text-center mb-8"
      >
        <CheckCircle className="w-24 h-24 text-success mx-auto mb-6" />
        <h1 className="text-4xl font-bold mb-2 gradient-text">Report Generated! 🎉</h1>
        <p className="text-xl text-text-secondary">
          Your documentation is ready to download
        </p>
      </motion.div>

      {/* Report Preview Card */}
      <Card className="mb-8">
        <div className="flex items-start gap-4 mb-6">
          <FileText className="w-12 h-12 text-primary-500 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-lg mb-1">
              {job.output_filename || 'Technical_Report.docx'}
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm text-text-muted">
              <div>
                <span className="text-text-secondary">Size:</span>{' '}
                {job.output_file_size 
                  ? formatBytes(job.output_file_size)
                  : job.output_path 
                    ? 'Calculating...' 
                    : 'N/A'}
              </div>
              <div>
                <span className="text-text-secondary">Chapters:</span> {job.chapters_created || 0}
              </div>
              <div>
                <span className="text-text-secondary">Sections:</span> {job.sections_written || 0}
              </div>
              <div>
                <span className="text-text-secondary">Generated:</span>{' '}
                {formatDate(job.completed_at || job.created_at)}
              </div>
            </div>
          </div>
        </div>

        <Button
          variant="primary"
          size="lg"
          onClick={handleDownload}
          disabled={downloading}
          className="w-full"
        >
          <Download className="mr-2" />
          {downloading ? 'Downloading...' : 'Download Report'}
        </Button>
      </Card>

      {/* Generation Summary */}
      <Card className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Generation Summary</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <Clock className="w-8 h-8 text-accent-amber mx-auto mb-2" />
            <div className="text-2xl font-bold">{Math.floor(generationTime / 60)}m {generationTime % 60}s</div>
            <div className="text-sm text-text-muted">Total Time</div>
          </div>
          <div className="text-center">
            <FileText className="w-8 h-8 text-primary-400 mx-auto mb-2" />
            <div className="text-2xl font-bold">{job.files_analyzed || 0}</div>
            <div className="text-sm text-text-muted">Files Analyzed</div>
          </div>
          <div className="text-center">
            <FileText className="w-8 h-8 text-accent-cyan mx-auto mb-2" />
            <div className="text-2xl font-bold">
              {job.sections_written || 0} / {job.total_sections || 0}
            </div>
            <div className="text-sm text-text-muted">Sections Written</div>
          </div>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex justify-center gap-4">
        <Button variant="outline" onClick={() => navigate('/history')}>
          View History
        </Button>
        <Button variant="primary" onClick={() => navigate('/upload')}>
          Generate Another Report
          <ArrowRight className="ml-2" />
        </Button>
      </div>
    </div>
  )
}

