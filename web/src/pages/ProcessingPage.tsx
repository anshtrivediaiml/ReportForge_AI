import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { useJobStore } from '@/store/jobStore'
import { getJob } from '@/services/api'
import { WebSocketClient } from '@/services/websocket'
import { ProgressUpdate } from '@/types'
import { AGENTS } from '@/utils/constants'
import { formatDuration } from '@/utils/formatters'
import {
  buildJobWebSocketUrl,
  clearRememberedJobWebSocketUrl,
  getRememberedJobWebSocketUrl,
  rememberJobWebSocketUrl,
} from '@/utils/network'
import AgentCard from '@/components/processing/AgentCard'
import LiveLogViewer from '@/components/processing/LiveLogViewer'
import MetricsPanel from '@/components/processing/MetricsPanel'
import Card from '@/components/common/Card'
import toast from 'react-hot-toast'

type ProcessingLocationState = {
  wsUrl?: string
}

export default function ProcessingPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const { stages, overallProgress, currentStage, logs, updateProgress } = useJobStore()
  const [elapsedTime, setElapsedTime] = useState(0)
  const [startTime] = useState(Date.now())

  const wsUrlFromNavigation = (location.state as ProcessingLocationState | null)?.wsUrl

  const navigateToUpload = (message?: string) => {
    if (jobId) {
      clearRememberedJobWebSocketUrl(jobId)
    }
    if (message) {
      toast.error(message)
    }
    navigate('/upload')
  }

  const navigateToSuccess = () => {
    if (jobId) {
      clearRememberedJobWebSocketUrl(jobId)
      navigate(`/success/${jobId}`)
    }
  }

  // Scroll to top on mount
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  useEffect(() => {
    if (!jobId) {
      navigateToUpload('Invalid job ID')
      return
    }

    const rememberedWsUrl = getRememberedJobWebSocketUrl(jobId)
    const resolvedWsUrl = buildJobWebSocketUrl(jobId, wsUrlFromNavigation || rememberedWsUrl)

    if (wsUrlFromNavigation) {
      rememberJobWebSocketUrl(jobId, wsUrlFromNavigation)
    }

    const checkInitialStatus = async () => {
      try {
        const jobData = await getJob(jobId)

        if (jobData.status === 'failed') {
          navigateToUpload(jobData.error_message || 'Report generation failed')
          return
        }

        if (jobData.status === 'completed') {
          if ((jobData.chapters_created || 0) > 0 && (jobData.sections_written || 0) > 0) {
            navigateToSuccess()
          } else {
            navigateToUpload('Report generation failed. No content was generated.')
          }
        }
      } catch (error) {
        console.error('Failed to check initial job status:', error)
      }
    }

    void checkInitialStatus()

    const client = new WebSocketClient(resolvedWsUrl)

    client.on('progress', (data: ProgressUpdate) => {
      updateProgress(data)
    })

    client.on('log', (data: ProgressUpdate) => {
      updateProgress(data)
    })

    client.on('error', (data: ProgressUpdate) => {
      updateProgress(data)
      toast.error(data.message || 'An error occurred')

      setTimeout(async () => {
        try {
          const jobData = await getJob(jobId)
          if (jobData.status === 'failed') {
            navigateToUpload(jobData.error_message || data.message || 'Report generation failed')
          }
        } catch (error) {
          console.error('Failed to verify error status:', error)
          setTimeout(() => {
            navigateToUpload()
          }, 2000)
        }
      }, 1000)
    })

    client.on('connected', () => {
      toast.dismiss('processing-ws')
    })

    client.on('reconnecting', () => {
      toast.loading('Reconnecting to live updates...', { id: 'processing-ws' })
    })

    client.on('connection-error', () => {
      toast.loading('Live updates are unavailable. Falling back to status polling...', {
        id: 'processing-ws',
      })
    })

    client.connect().catch((error) => {
      console.error('WebSocket connection failed:', error)
      toast.loading('Live updates are unavailable. Falling back to status polling...', {
        id: 'processing-ws',
      })
    })

    const interval = setInterval(() => {
      setElapsedTime((Date.now() - startTime) / 1000)
    }, 1000)

    return () => {
      toast.dismiss('processing-ws')
      client.disconnect()
      clearInterval(interval)
    }
  }, [jobId, navigate, startTime, updateProgress, wsUrlFromNavigation])

  useEffect(() => {
    if (!jobId) {
      return
    }

    const pollInterval = setInterval(async () => {
      try {
        const jobData = await getJob(jobId)

        if (jobData.status === 'failed') {
          clearInterval(pollInterval)
          navigateToUpload(jobData.error_message || 'Report generation failed')
          return
        }

        if (jobData.status === 'completed') {
          clearInterval(pollInterval)
          if ((jobData.chapters_created || 0) > 0 && (jobData.sections_written || 0) > 0) {
            navigateToSuccess()
          } else {
            navigateToUpload('Report generation failed. No content was generated.')
          }
        }
      } catch (error) {
        console.error('Failed to poll job status:', error)
      }
    }, 5000)

    return () => clearInterval(pollInterval)
  }, [jobId, navigate])

  useEffect(() => {
    if (stages.complete.status === 'completed' && stages.complete.progress === 100) {
      setTimeout(async () => {
        if (!jobId) {
          return
        }

        try {
          const jobData = await getJob(jobId)

          if (jobData.status === 'completed' && (jobData.chapters_created || 0) > 0 && (jobData.sections_written || 0) > 0) {
            navigateToSuccess()
          } else {
            navigateToUpload('Report generation failed. No content was generated.')
          }
        } catch (error) {
          console.error('Failed to verify job:', error)
          navigateToUpload()
        }
      }, 2000)
    }

    const hasError = Object.values(stages).some((stage) => stage.status === 'error')
    if (hasError) {
      setTimeout(async () => {
        if (!jobId) {
          return
        }

        try {
          const jobData = await getJob(jobId)

          if (jobData.status === 'failed') {
            navigateToUpload(jobData.error_message || 'Report generation encountered an error')
          } else {
            console.warn('WebSocket error but backend status is:', jobData.status)
          }
        } catch (error) {
          console.error('Failed to verify error status:', error)
          navigateToUpload('Report generation encountered an error')
        }
      }, 2000)
    }
  }, [jobId, navigate, stages, stages.complete])

  const activeAgent = AGENTS.find((agent) => agent.id === currentStage) || AGENTS[0]

  return (
    <div className="container mx-auto px-6 py-12 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 gradient-text">Generating Report</h1>
        <p className="text-text-secondary">Job ID: {jobId}</p>
        <p className="text-text-muted text-sm">Time elapsed: {formatDuration(elapsedTime)}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
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
