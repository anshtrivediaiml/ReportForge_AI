import { create } from 'zustand'
import { Job, ProgressUpdate, AgentStage, StageStatus, ReportSummary } from '@/types'

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
  // Current job
  currentJobId: string | null
  currentJob: Job | null
  
  // Progress tracking
  stages: Record<AgentStage, StageInfo>
  overallProgress: number
  currentStage: AgentStage
  
  // Logs
  logs: string[]
  
  // Report summary
  reportSummary: ReportSummary | null
  
  // Actions
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
    
    // Handle progress updates
    if (update.type === 'progress' && update.stage) {
      const stage = update.stage as AgentStage
      
      // Update the specific stage with all details
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
      
      // Mark previous stages as completed when a new stage becomes active
      const stageOrder: AgentStage[] = ['parser', 'planner', 'writer', 'builder', 'complete']
      const currentIndex = stageOrder.indexOf(stage)
      if (currentIndex > 0 && newStages[stage].status === 'active') {
        for (let i = 0; i < currentIndex; i++) {
          const prevStage = stageOrder[i]
          if (newStages[prevStage].status !== 'completed') {
            newStages[prevStage] = {
              ...newStages[prevStage],
              status: 'completed',
              progress: 100,
            }
          }
        }
      }
      
      // Calculate overall progress based on stage weights
      // Each agent now goes 0-100%, so we use their actual progress
      const stageWeights = { parser: 0.25, planner: 0.25, writer: 0.35, builder: 0.1, complete: 0.05 }
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
          // Use actual progress percentage (0-100) from the agent
          overallProgress += weight * stageInfo.progress
          currentStage = stageKey
          break
        } else if (stageInfo.status === 'pending') {
          // Pending stages contribute 0
          break
        }
      }
      
      set({
        stages: newStages,
        overallProgress: Math.min(100, Math.round(overallProgress)),
        currentStage,
      })
    } 
    // Handle log messages
    else if (update.type === 'log') {
      // Parse timestamp correctly (handle both ISO string and Date objects)
      let timestamp: string
      try {
        const ts = update.timestamp
        if (typeof ts === 'string') {
          // Parse ISO string and convert to local time
          const date = new Date(ts)
          // Check if date is valid
          if (isNaN(date.getTime())) {
            timestamp = new Date().toLocaleTimeString('en-IN', { 
              timeZone: 'Asia/Kolkata',
              hour12: true, 
              hour: 'numeric', 
              minute: '2-digit', 
              second: '2-digit' 
            })
          } else {
            timestamp = date.toLocaleTimeString('en-IN', { 
              timeZone: 'Asia/Kolkata',
              hour12: true, 
              hour: 'numeric', 
              minute: '2-digit', 
              second: '2-digit' 
            })
          }
        } else {
          timestamp = new Date().toLocaleTimeString('en-IN', { 
            timeZone: 'Asia/Kolkata',
            hour12: true, 
            hour: 'numeric', 
            minute: '2-digit', 
            second: '2-digit' 
          })
        }
      } catch {
        timestamp = new Date().toLocaleTimeString('en-IN', { 
          timeZone: 'Asia/Kolkata',
          hour12: true, 
          hour: 'numeric', 
          minute: '2-digit', 
          second: '2-digit' 
        })
      }
      
      const level = update.level || 'info'
      const agent = update.agent || 'system'
      const message = update.message || ''
      
      // Filter important logs - only show success, error, and key info messages
      const importantKeywords = [
        'completed', 'saved', 'added', 'created', 'generated', 
        'found', 'detected', 'starting', 'error', 'failed',
        'chapter', 'section', 'document', 'references'
      ]
      const isImportant = level === 'success' || level === 'error' || 
                         importantKeywords.some(keyword => message.toLowerCase().includes(keyword))
      
      // Only add important logs to the main log viewer
      if (isImportant) {
        // Format log message with timestamp and level
        const logPrefix = level === 'success' ? '✓' : level === 'error' ? '✗' : level === 'warning' ? '⚠' : 'ℹ'
        const logMessage = `[${timestamp}] [${agent.toUpperCase()}] ${logPrefix} ${message}`
        
        const newLogs = [...state.logs, logMessage]
        const trimmedLogs = newLogs.slice(-100) // Keep last 100 important logs
        
        // Add to relevant stage logs based on agent
        const agentToStage: Record<string, AgentStage> = {
          'parser': 'parser',
          'planner': 'planner',
          'writer': 'writer',
          'builder': 'builder',
          'complete': 'complete',
        }
        
        const stage = agentToStage[agent.toLowerCase()] || 'parser'
        if (stage) {
          newStages[stage] = {
            ...newStages[stage],
            logs: [...newStages[stage].logs, logMessage].slice(-10), // Keep last 10 per stage
          }
        }
        
        set({ logs: trimmedLogs, stages: newStages })
      }
    }
    // Handle error messages
    else if (update.type === 'error') {
      const timestamp = new Date(update.timestamp || Date.now()).toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour12: true,
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit'
      })
      const errorMessage = `[${timestamp}] [ERROR] ✗ ${update.message || 'An error occurred'}`
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

  reset: () => set({
    currentJobId: null,
    currentJob: null,
    stages: initialState,
    overallProgress: 0,
    currentStage: 'parser',
    logs: [],
    reportSummary: null,
  }),
}))

