import { create } from 'zustand'
import { Job, ProgressUpdate, AgentStage, StageStatus, ReportSummary } from '@/types'
import { formatTime } from '@/utils/formatters'

interface StageInfo {
  status: StageStatus
  progress: number
  message: string
  logs: string[]
  files_analyzed?: number
  chapters_created?: number
  sections_written?: number
  total_sections?: number
}

interface JobState {
  currentJobId: string | null
  currentJob: Job | null
  stages: Record<AgentStage, StageInfo>
  overallProgress: number
  currentStage: AgentStage
  logs: string[]
  reportSummary: ReportSummary | null
  setCurrentJob: (job: Job) => void
  updateProgress: (update: ProgressUpdate) => void
  addLog: (log: string) => void
  setReportSummary: (summary: ReportSummary) => void
  reset: () => void
}

const initialStageInfo: StageInfo = {
  status: 'pending',
  progress: 0,
  message: 'Waiting to start...',
  logs: [],
}

const initialState = {
  parser: { ...initialStageInfo },
  planner: { ...initialStageInfo },
  writer: { ...initialStageInfo },
  builder: { ...initialStageInfo },
  complete: { ...initialStageInfo },
}

function getStageOrder(): AgentStage[] {
  return ['parser', 'planner', 'writer', 'builder', 'complete']
}

function getLogPrefix(level: string): string {
  if (level === 'success') return '[OK]'
  if (level === 'error') return '[ERR]'
  if (level === 'warning') return '[WARN]'
  return '[INFO]'
}

export const useJobStore = create<JobState>((set, get) => ({
  currentJobId: null,
  currentJob: null,
  stages: initialState,
  overallProgress: 0,
  currentStage: 'parser',
  logs: [],
  reportSummary: null,

  setCurrentJob: (job) => set({ currentJob: job, currentJobId: job.id }),

  updateProgress: (update) => {
    const state = get()
    const newStages = { ...state.stages }

    if (update.type === 'progress' && update.stage) {
      const stage = update.stage as AgentStage

      newStages[stage] = {
        status: update.progress === 100 ? 'completed' : 'active',
        progress: update.progress || 0,
        message: update.message || '',
        logs: newStages[stage].logs,
        files_analyzed: update.files_analyzed,
        chapters_created: update.chapters_created,
        sections_written: update.sections_written,
        total_sections: update.total_sections,
      }

      const stageOrder = getStageOrder()
      const currentIndex = stageOrder.indexOf(stage)
      if (currentIndex > 0 && newStages[stage].status === 'active') {
        for (let i = 0; i < currentIndex; i += 1) {
          const previousStage = stageOrder[i]
          if (newStages[previousStage].status !== 'completed') {
            newStages[previousStage] = {
              ...newStages[previousStage],
              status: 'completed',
              progress: 100,
            }
          }
        }
      }

      const stageWeights = {
        parser: 0.25,
        planner: 0.25,
        writer: 0.35,
        builder: 0.1,
        complete: 0.05,
      }

      let overallProgress = 0
      let currentStage: AgentStage = 'parser'

      for (const [key, weight] of Object.entries(stageWeights)) {
        const stageKey = key as AgentStage
        const stageInfo = newStages[stageKey]

        if (stageInfo.status === 'completed') {
          overallProgress += weight * 100
          if (stageKey !== 'complete') {
            currentStage = stageKey
          }
        } else if (stageInfo.status === 'active') {
          overallProgress += weight * stageInfo.progress
          currentStage = stageKey
          break
        } else if (stageInfo.status === 'pending') {
          break
        }
      }

      set({
        stages: newStages,
        overallProgress: Math.min(100, Math.round(overallProgress)),
        currentStage,
      })
      return
    }

    if (update.type === 'log') {
      const timestamp = formatTime(update.timestamp || Date.now())
      const level = update.level || 'info'
      const agent = update.agent || 'system'
      const message = update.message || ''

      const importantKeywords = [
        'completed',
        'saved',
        'added',
        'created',
        'generated',
        'found',
        'detected',
        'starting',
        'error',
        'failed',
        'chapter',
        'section',
        'document',
        'references',
      ]
      const isImportant =
        level === 'success' ||
        level === 'error' ||
        importantKeywords.some((keyword) => message.toLowerCase().includes(keyword))

      if (isImportant) {
        const logMessage = `[${timestamp}] [${agent.toUpperCase()}] ${getLogPrefix(level)} ${message}`
        const newLogs = [...state.logs, logMessage]
        const trimmedLogs = newLogs.slice(-100)

        const agentToStage: Record<string, AgentStage> = {
          parser: 'parser',
          planner: 'planner',
          writer: 'writer',
          builder: 'builder',
          complete: 'complete',
        }

        const stage = agentToStage[agent.toLowerCase()] || 'parser'
        newStages[stage] = {
          ...newStages[stage],
          logs: [...newStages[stage].logs, logMessage].slice(-10),
        }

        set({ logs: trimmedLogs, stages: newStages })
      }
      return
    }

    if (update.type === 'error') {
      const timestamp = formatTime(update.timestamp || Date.now())
      const errorMessage = `[${timestamp}] [ERROR] [ERR] ${update.message || 'An error occurred'}`
      const newLogs = [...state.logs, errorMessage].slice(-200)

      if (update.stage) {
        const stage = update.stage as AgentStage
        newStages[stage] = {
          ...newStages[stage],
          status: 'error',
          message: update.message || 'Error occurred',
          logs: [...newStages[stage].logs, errorMessage].slice(-50),
        }
      }

      set({ logs: newLogs, stages: newStages })
    }
  },

  addLog: (log) => set((state) => ({ logs: [...state.logs, log].slice(-200) })),

  setReportSummary: (summary) => set({ reportSummary: summary }),

  reset: () =>
    set({
      currentJobId: null,
      currentJob: null,
      stages: initialState,
      overallProgress: 0,
      currentStage: 'parser',
      logs: [],
      reportSummary: null,
    }),
}))
