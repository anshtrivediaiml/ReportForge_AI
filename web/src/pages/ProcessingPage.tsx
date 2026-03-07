import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useJobStore } from '@/store/jobStore'
import { WebSocketClient } from '@/services/websocket'
import { ProgressUpdate } from '@/types'
import { AGENTS } from '@/utils/constants'
import { formatDuration } from '@/utils/formatters'
import AgentCard from '@/components/processing/AgentCard'
import LiveLogViewer from '@/components/processing/LiveLogViewer'
import MetricsPanel from '@/components/processing/MetricsPanel'
import Card from '@/components/common/Card'
import toast from 'react-hot-toast'

export default function ProcessingPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const { stages, overallProgress, currentStage, logs, updateProgress, setReportSummary } = useJobStore()
  const [elapsedTime, setElapsedTime] = useState(0)
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null)
  const [startTime] = useState(Date.now())

  // Scroll to top on mount
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  useEffect(() => {
    if (!jobId) {
      toast.error('Invalid job ID')
      navigate('/upload')
      return
    }

    // CRITICAL: Check job status immediately on page load to ensure consistency
    const checkInitialStatus = async () => {
      try {
        const { getJob } = await import('@/services/api')
        const job = await getJob(jobId)
        const jobData = job.data || job
        
        // If job is already failed, navigate immediately
        if (jobData.status === 'failed' || jobData.status === 'error') {
          toast.error(jobData.error_message || 'Report generation failed')
          navigate('/upload')
          return
        }
        
        // If job is already completed, navigate to success
        if (jobData.status === 'completed') {
          if ((jobData.chapters_created || 0) > 0 && 
              (jobData.sections_written || 0) > 0) {
            navigate(`/success/${jobId}`)
          } else {
            toast.error('Report generation failed. No content was generated.')
            navigate('/upload')
          }
          return
        }
      } catch (error) {
        console.error('Failed to check initial job status:', error)
        // Continue with WebSocket connection even if initial check fails
      }
    }
    
    checkInitialStatus()

    // Connect to WebSocket
    const wsUrl = `ws://localhost:8000/ws/${jobId}`
    const client = new WebSocketClient(wsUrl)

    client.on('progress', (data: ProgressUpdate) => {
      console.log('📊 Progress update:', data)
      updateProgress(data)
    })

    client.on('log', (data: ProgressUpdate) => {
      console.log('📝 Log update:', data)
      updateProgress(data)
    })

    client.on('error', (data: ProgressUpdate) => {
      console.error('❌ Error update:', data)
      updateProgress(data)
      toast.error(data.message || 'An error occurred')
      
      // CRITICAL: Immediately check backend status to ensure consistency
      setTimeout(async () => {
        try {
          const { getJob } = await import('@/services/api')
          const job = await getJob(jobId!)
          const jobData = job.data || job
          
          // If backend confirms failure, navigate immediately
          if (jobData.status === 'failed' || jobData.status === 'error') {
            toast.error(jobData.error_message || data.message || 'Report generation failed')
            navigate('/upload')
          }
        } catch (error) {
          console.error('Failed to verify error status:', error)
          // Still navigate on WebSocket error even if we can't verify
          setTimeout(() => {
            navigate('/upload')
          }, 2000)
        }
      }, 1000) // Check after 1 second
    })

    client.on('connected', () => {
      console.log('✅ WebSocket connected')
      // Don't show toast on connection - less intrusive
    })

    client.on('message', (data: ProgressUpdate) => {
      // Handle any message type that wasn't caught above
      if (data.type && ['progress', 'log', 'error'].includes(data.type)) {
        updateProgress(data)
      }
    })

    client.connect().catch((error) => {
      console.error('WebSocket connection failed:', error)
      toast.error('Failed to connect to live updates')
    })

    setWsClient(client)

    // Update elapsed time
    const interval = setInterval(() => {
      setElapsedTime((Date.now() - startTime) / 1000)
    }, 1000)

    return () => {
      client.disconnect()
      clearInterval(interval)
    }
  }, [jobId, navigate, updateProgress, startTime])

  // Poll job status as fallback to ensure frontend-backend synchronization
  useEffect(() => {
    if (!jobId) return

    const pollInterval = setInterval(async () => {
      try {
        const { getJob } = await import('@/services/api')
        const job = await getJob(jobId)
        const jobData = job.data || job
        
        // CRITICAL: Check job status from backend to stay synchronized
        if (jobData.status === 'failed' || jobData.status === 'error') {
          clearInterval(pollInterval)
          toast.error(jobData.error_message || 'Report generation failed')
          navigate('/upload')
          return
        }
        
        // Check for completion
        if (jobData.status === 'completed') {
          clearInterval(pollInterval)
          // Verify job has actual content
          if ((jobData.chapters_created || 0) > 0 && 
              (jobData.sections_written || 0) > 0) {
            navigate(`/success/${jobId}`)
          } else {
            toast.error('Report generation failed. No content was generated.')
            navigate('/upload')
          }
          return
        }
      } catch (error) {
        console.error('Failed to poll job status:', error)
        // Don't clear interval on error - might be temporary network issue
      }
    }, 5000) // Poll every 5 seconds

    return () => clearInterval(pollInterval)
  }, [jobId, navigate])

  // Check if generation is complete or failed (from WebSocket)
  useEffect(() => {
    // Check for completion
    if (stages.complete.status === 'completed' && stages.complete.progress === 100) {
      // Verify job actually has content before navigating
      setTimeout(async () => {
        try {
          const { getJob } = await import('@/services/api')
          const job = await getJob(jobId!)
          const jobData = job.data || job
          
          // Only navigate if job has actual content
          if (jobData.status === 'completed' && 
              (jobData.chapters_created || 0) > 0 && 
              (jobData.sections_written || 0) > 0) {
            navigate(`/success/${jobId}`)
          } else {
            toast.error('Report generation failed. No content was generated.')
            navigate('/upload')
          }
        } catch (error) {
          console.error('Failed to verify job:', error)
          navigate('/upload')
        }
      }, 2000)
    }
    
    // Check for error status in any stage
    const hasError = Object.values(stages).some(stage => stage.status === 'error')
    if (hasError) {
      setTimeout(async () => {
        // Double-check with backend to ensure consistency
        try {
          const { getJob } = await import('@/services/api')
          const job = await getJob(jobId!)
          const jobData = job.data || job
          
          if (jobData.status === 'failed' || jobData.status === 'error') {
            toast.error(jobData.error_message || 'Report generation encountered an error')
            navigate('/upload')
          } else {
            // WebSocket error but backend says otherwise - log for debugging
            console.warn('WebSocket error but backend status is:', jobData.status)
          }
        } catch (error) {
          console.error('Failed to verify error status:', error)
          toast.error('Report generation encountered an error')
          navigate('/upload')
        }
      }, 2000)
    }
  }, [stages.complete, stages, jobId, navigate])

  const activeAgent = AGENTS.find(a => a.id === currentStage) || AGENTS[0]

  return (
    <div className="container mx-auto px-6 py-12 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 gradient-text">Generating Report</h1>
        <p className="text-text-secondary">Job ID: {jobId}</p>
        <p className="text-text-muted text-sm">Time elapsed: {formatDuration(elapsedTime)}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Agent Timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Agent Highlight Card */}
          {stages[currentStage]?.status === 'active' && (
            <Card className="border-2 border-primary-500 bg-primary-500/10 shadow-lg shadow-primary-500/20">
              <div className="flex items-center gap-4">
                <div className="text-4xl animate-pulse">{activeAgent.icon}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-xl font-bold">{activeAgent.name}</h3>
                    <span className="text-xs px-2 py-1 bg-primary-500/20 text-primary-400 rounded">ACTIVE</span>
                  </div>
                  <p className="text-text-secondary text-sm mb-2">
                    {stages[currentStage]?.message || 'Processing...'}
                  </p>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-300"
                      style={{ width: `${stages[currentStage]?.progress || 0}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-text-muted mt-1">
                    <span>Progress: {stages[currentStage]?.progress || 0}%</span>
                    <span>Time: {formatDuration(elapsedTime)}</span>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Overall Progress */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Overall Progress</h3>
              <span className="text-3xl font-bold">{overallProgress}%</span>
            </div>
            <div className="h-3 bg-slate-700 rounded-full overflow-hidden mb-2">
              <div
                className="h-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-500"
                style={{ width: `${overallProgress}%` }}
              />
            </div>
            <div className="flex justify-between text-sm text-text-muted">
              <span>{activeAgent.name}</span>
              <span>{stages[currentStage]?.message || 'Processing...'}</span>
            </div>
          </Card>

          {/* Agent Timeline */}
          <div className="space-y-4">
            {AGENTS.map((agent, index) => {
              const stageInfo = stages[agent.id as keyof typeof stages]
              const isActive = currentStage === agent.id
              const isComplete = stageInfo.status === 'completed'
              const isPending = stageInfo.status === 'pending'

              return (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  status={stageInfo.status}
                  progress={stageInfo.progress}
                  message={stageInfo.message}
                  isActive={isActive}
                  isComplete={isComplete}
                  isPending={isPending}
                  index={index}
                  logs={stageInfo.logs}
                />
              )
            })}
          </div>
        </div>

        {/* Right Column: Metrics & Logs */}
        <div className="space-y-6">
          <MetricsPanel
            filesAnalyzed={stages.parser.files_analyzed || 0}
            chaptersCreated={stages.planner.chapters_created || 0}
            sectionsWritten={stages.writer.sections_written || 0}
            timeElapsed={formatDuration(elapsedTime)}
          />

          <LiveLogViewer logs={logs} />
        </div>
      </div>
    </div>
  )
}

