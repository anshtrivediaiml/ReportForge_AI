export type AgentStage = 'parser' | 'planner' | 'writer' | 'builder' | 'complete'
export type StageStatus = 'pending' | 'active' | 'completed' | 'error'

export interface ProgressUpdate {
  type: 'progress' | 'log' | 'error' | 'connected' | 'heartbeat'
  job_id: string
  stage?: AgentStage
  progress?: number
  message?: string
  timestamp: string
  files_analyzed?: number
  chapters_created?: number
  sections_written?: number
  total_sections?: number
  pages_generated?: number
  estimated_time_remaining?: string
  details?: Record<string, any>
  agent?: string
  level?: 'info' | 'warning' | 'error' | 'success'
}

export interface Job {
  id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  current_stage?: AgentStage
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  files_analyzed: number
  chapters_created: number
  sections_written: number
  total_sections: number
  pages_generated: number
  output_path?: string
  output_filename?: string
  error_message?: string
}

export interface UploadedFile {
  file: File
  fileId?: string
  progress: number
  status: 'idle' | 'uploading' | 'completed' | 'error'
}

export interface ReportSummary {
  filename: string
  size: number
  sections: number
  chapters: number
  generationTime: string
  filesAnalyzed: number
}

