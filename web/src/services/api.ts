// Use the authenticated axios instance from lib/axios
// This ensures all API calls include JWT tokens and handle auth errors
import api from '@/lib/axios'
import { ApiEnvelope, unwrapApiData } from '@/utils/api'

export interface UploadFileResponse {
  file_id: string
  filename: string
  size: number
  chunk_count: number
  uploaded_chunks: number
}

export interface StartGenerationRequest {
  guidelines_file_id: string
  project_file_id: string
}

export interface StartGenerationResponse {
  job_id: string
  ws_url: string
  status: string
}

export interface JobResponse {
  id: string
  title?: string | null
  user_id?: number | null
  guidelines_filename: string
  project_filename: string
  original_filename?: string | null
  status: 'queued' | 'processing' | 'completed' | 'failed'
  current_stage?: 'parser' | 'planner' | 'writer' | 'builder' | 'complete' | null
  progress: number
  created_at: string
  started_at?: string | null
  completed_at?: string | null
  files_analyzed: number
  chapters_created: number
  sections_written: number
  total_sections: number
  pages_generated: number
  output_path?: string | null
  output_filename?: string | null
  error_message?: string | null
  output_file_size?: number | null
}

export interface JobListResponse {
  jobs: JobResponse[]
  total: number
  page: number
  page_size: number
}

export const uploadFile = async (file: File): Promise<UploadFileResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post<ApiEnvelope<UploadFileResponse>>(
    '/api/v1/upload/file',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  
  return unwrapApiData(response.data)
}

export const startGeneration = async (
  request: StartGenerationRequest
): Promise<StartGenerationResponse> => {
  const response = await api.post<ApiEnvelope<StartGenerationResponse>>(
    '/api/v1/upload/generate',
    request
  )
  
  return unwrapApiData(response.data)
}

export const getJob = async (jobId: string): Promise<JobResponse> => {
  const response = await api.get<ApiEnvelope<JobResponse> | JobResponse>(`/api/v1/jobs/${jobId}`)
  return unwrapApiData(response.data)
}

export const listJobs = async (page = 1, pageSize = 20): Promise<JobListResponse> => {
  const response = await api.get<JobListResponse>('/api/v1/jobs', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const downloadReport = async (jobId: string): Promise<Blob> => {
  const response = await api.get(`/api/v1/download/${jobId}`, {
    responseType: 'blob',
  })
  return response.data
}

export const getSharedReportFile = async (shareToken: string): Promise<Blob> => {
  const response = await api.get(`/api/v1/sharing/${encodeURIComponent(shareToken)}/file`, {
    responseType: 'blob',
  })
  return response.data
}

// Update job title
export interface UpdateJobTitleRequest {
  title: string
}

export const updateJobTitle = async (jobId: string, title: string): Promise<any> => {
  const response = await api.patch<ApiEnvelope<{ id: string; title: string }>>(
    `/api/v1/jobs/${jobId}`,
    { title }
  )
  return unwrapApiData(response.data)
}

// Delete job
export const deleteJob = async (jobId: string): Promise<{ success: boolean; message: string }> => {
  const response = await api.delete<{ success: boolean; message: string; job_id: string }>(
    `/api/v1/jobs/${jobId}`
  )
  return response.data
}

// ============================================================================
// Authentication API Functions
// ============================================================================

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: number
    email: string
    username: string | null
    full_name: string | null
    profile_picture: string | null
    auth_provider: string
    is_verified: boolean
    storage_used: number
    reports_generated: number
    created_at: string
  }
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  access_token: string
  token_type: string
}

// Register new user
export const register = async (data: RegisterRequest): Promise<AuthResponse> => {
  const response = await api.post<ApiEnvelope<AuthResponse> | AuthResponse>(
    '/api/v1/auth/register',
    data
  )
  return unwrapApiData(response.data)
}

// Login user
export const login = async (data: LoginRequest): Promise<AuthResponse> => {
  const formData = new FormData()
  formData.append('username', data.email) // OAuth2 uses 'username' field
  formData.append('password', data.password)
  
  const response = await api.post<AuthResponse | ApiEnvelope<AuthResponse>>(
    '/api/v1/auth/login',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  
  const authResponse = unwrapApiData(response.data)
  
  if (!authResponse.access_token || !authResponse.user) {
    throw new Error('Invalid login response: missing access_token or user')
  }
  
  return authResponse
}

// Get current user info
export const getCurrentUser = async (): Promise<AuthResponse['user']> => {
  const response = await api.get<AuthResponse['user'] | ApiEnvelope<AuthResponse['user']>>(
    '/api/v1/auth/me'
  )
  return unwrapApiData(response.data)
}

// Refresh access token
export const refreshToken = async (refreshToken: string): Promise<RefreshTokenResponse> => {
  const response = await api.post<RefreshTokenResponse | ApiEnvelope<RefreshTokenResponse>>(
    '/api/v1/auth/refresh',
    { refresh_token: refreshToken }
  )
  return unwrapApiData(response.data)
}

// Logout user
export const logout = async (): Promise<void> => {
  await api.post('/api/v1/auth/logout')
}

// Get user statistics
export interface UserStats {
  user_id: number
  email: string
  storage_used: number
  storage_limit: number
  storage_used_percent: number
  reports_generated: number
  reports_completed: number
  reports_failed: number
  reports_processing: number
  reports_queued: number
  total_reports: number
  created_at: string
  last_login: string | null
}

export const getUserStats = async (): Promise<UserStats> => {
  const response = await api.get<UserStats | ApiEnvelope<UserStats>>(
    '/api/v1/reports/stats'
  )
  return unwrapApiData(response.data)
}

// ============================================================================
// Profile Management API Functions
// ============================================================================

export interface ProfileUpdate {
  full_name?: string
  username?: string
}

export interface PasswordChange {
  current_password: string
  new_password: string
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirm {
  token: string
  new_password: string
}

export const updateProfile = async (profileData: ProfileUpdate): Promise<AuthResponse['user']> => {
  const response = await api.patch<AuthResponse['user'] | ApiEnvelope<AuthResponse['user']>>(
    '/api/v1/auth/profile',
    profileData
  )
  return unwrapApiData(response.data)
}

export const changePassword = async (passwordData: PasswordChange): Promise<{ message: string }> => {
  const response = await api.post<{ success: boolean; message: string }>(
    '/api/v1/auth/change-password',
    passwordData
  )
  return response.data
}

export const requestPasswordReset = async (email: string): Promise<{ message: string; reset_url?: string }> => {
  const response = await api.post<{ message: string; reset_url?: string }>(
    '/api/v1/auth/password-reset/request',
    { email }
  )
  return response.data
}

export const confirmPasswordReset = async (resetData: PasswordResetConfirm): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>(
    '/api/v1/auth/password-reset/confirm',
    resetData
  )
  return response.data
}

// Delete account
export const deleteAccount = async (): Promise<{ message: string; success: boolean }> => {
  const response = await api.delete<{ message: string; success: boolean }>(
    '/api/v1/auth/account'
  )
  return response.data
}

// ============================================================================
// Bulk Actions API Functions
// ============================================================================

export interface BulkDeleteResponse {
  success: boolean
  message: string
  deleted_count: number
  failed_ids: string[]
}

// ============================================================================
// Analytics API Functions
// ============================================================================

export interface UserMetrics {
  total_reports: number
  reports_by_status: {
    queued: number
    processing: number
    completed: number
    failed: number
  }
  avg_processing_time_seconds: number
  min_processing_time_seconds?: number | null
  max_processing_time_seconds?: number | null
  storage_used_bytes: number
  period_days: number
  // Advanced analytics
  growth_rate_percent?: number
  success_rate_percent?: number
  reports_per_day?: number
  avg_pages_per_report?: number
  avg_sections_per_report?: number
  total_pages_generated?: number
  total_sections_written?: number
  total_chapters_created?: number
  avg_storage_per_report_bytes?: number
}

export interface SystemMetrics extends UserMetrics {
  total_users: number
  active_users: number
  daily_reports: Array<{
    date: string
    count: number
  }>
}

export const getMyMetrics = async (days: number = 30): Promise<UserMetrics> => {
  const response = await api.get<ApiEnvelope<UserMetrics>>(
    `/api/v1/analytics/my-metrics?days=${days}`
  )
  return unwrapApiData(response.data)
}

export const getSystemMetrics = async (days: number = 30): Promise<SystemMetrics> => {
  const response = await api.get<ApiEnvelope<SystemMetrics>>(
    `/api/v1/analytics/system?days=${days}`
  )
  return unwrapApiData(response.data)
}

// ============================================================================
// Sharing API Functions
// ============================================================================

export interface ShareReportRequest {
  job_id: string
  expires_in_days?: number | null
  requires_password: boolean
  password?: string | null
  description?: string | null
  access_level?: string
}

export interface ShareReportResponse {
  share_id: string
  share_token: string
  share_url: string
  expires_at: string | null
  created_at: string
  access_count: number
  is_active: boolean
  requires_password: boolean
}

export interface SharedReportInfo {
  share_id: string
  job_id: string
  job_title: string | null
  shared_by: string
  created_at: string
  expires_at: string | null
  access_count: number
  description: string | null
  requires_password: boolean
}

export interface SharedReportListResponse {
  shares: ShareReportResponse[]
  total: number
}

export const createShareLink = async (shareData: ShareReportRequest): Promise<ShareReportResponse> => {
  const response = await api.post<ShareReportResponse>(
    '/api/v1/sharing/create',
    shareData
  )
  return response.data
}

export const listSharedReports = async (): Promise<SharedReportListResponse> => {
  const response = await api.get<SharedReportListResponse>(
    '/api/v1/sharing/list'
  )
  return response.data
}

export const getSharedReportInfo = async (shareToken: string): Promise<SharedReportInfo> => {
  // FastAPI automatically URL-decodes path parameters, so pass token as-is
  // But ensure it's properly encoded in the URL if it contains special characters
  const response = await api.get<SharedReportInfo>(
    `/api/v1/sharing/${encodeURIComponent(shareToken)}`
  )
  return response.data
}

export const accessSharedReport = async (shareToken: string, password?: string): Promise<{ job_id: string; access_granted: boolean }> => {
  // FastAPI automatically URL-decodes path parameters, so encode for URL but FastAPI will decode
  const response = await api.post<{ job_id: string; access_granted: boolean }>(
    `/api/v1/sharing/${encodeURIComponent(shareToken)}/access`,
    { password: password || null }
  )
  return response.data
}

export const getSharedReportViewUrl = async (shareToken: string): Promise<{ 
  view_url: string
  google_docs_viewer_url?: string
  office_viewer_url?: string
  download_url: string
  filename: string
}> => {
  const response = await api.get<{ 
    view_url: string
    google_docs_viewer_url?: string
    office_viewer_url?: string
    download_url: string
    filename: string
  }>(
    `/api/v1/sharing/${encodeURIComponent(shareToken)}/view`
  )
  return response.data
}

export const deleteShareLink = async (shareId: string): Promise<{ message: string }> => {
  const response = await api.delete<{ message: string }>(
    `/api/v1/sharing/${shareId}`
  )
  return response.data
}

// ============================================================================
// Bulk Actions API Functions
// ============================================================================

export const bulkDeleteJobs = async (jobIds: string[]): Promise<BulkDeleteResponse> => {
  const response = await api.post<BulkDeleteResponse>(
    '/api/v1/jobs/bulk-delete',
    jobIds
  )
  return response.data
}


