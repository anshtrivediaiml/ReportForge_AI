import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  FileText, 
  HardDrive, 
  TrendingUp, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Loader2,
  Plus,
  ArrowRight,
  BarChart3,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import { getUserStats, listJobs, getMyMetrics, type UserStats, type UserMetrics } from '@/services/api'
import { formatBytes, formatDate } from '@/utils/formatters'
import toast from 'react-hot-toast'

export default function DashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<UserStats | null>(null)
  const [recentJobs, setRecentJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showAnalytics, setShowAnalytics] = useState(false)
  const [analytics, setAnalytics] = useState<UserMetrics | null>(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [analyticsDays, setAnalyticsDays] = useState(30)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [showAnalyticsContent, setShowAnalyticsContent] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      // Fetch user stats and recent jobs in parallel
      const [statsData, jobsData] = await Promise.all([
        getUserStats(),
        listJobs(1, 5) // Get 5 most recent jobs
      ])
      
      setStats(statsData)
      setRecentJobs(jobsData.jobs || [])
    } catch (error: any) {
      console.error('Error fetching dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const fetchAnalytics = async (days: number = analyticsDays) => {
    setIsTransitioning(true)
    setShowAnalyticsContent(false) // Fade out old content
    
    // Wait for fade-out animation (300ms)
    await new Promise(resolve => setTimeout(resolve, 300))
    
    setAnalyticsLoading(true)
    
    try {
      const metrics = await getMyMetrics(days)
      setAnalytics(metrics)
      
      // Small delay before showing new data for smooth fade-in
      await new Promise(resolve => setTimeout(resolve, 100))
      setShowAnalyticsContent(true) // Fade in new content
    } catch (error: any) {
      console.error('Failed to fetch analytics:', error)
      toast.error('Failed to load analytics')
      setShowAnalyticsContent(true) // Show content even on error
    } finally {
      setAnalyticsLoading(false)
      setIsTransitioning(false)
    }
  }

  const handleToggleAnalytics = () => {
    if (!showAnalytics && !analytics) {
      fetchAnalytics()
    }
    setShowAnalytics(!showAnalytics)
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    return `${Math.round(seconds / 3600)}h`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-400'
      case 'processing':
        return 'text-primary-400'
      case 'failed':
        return 'text-red-400'
      case 'queued':
        return 'text-yellow-400'
      default:
        return 'text-text-muted'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return CheckCircle
      case 'processing':
        return Loader2
      case 'failed':
        return XCircle
      case 'queued':
        return Clock
      default:
        return FileText
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-6 py-12">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="container mx-auto px-6 py-12">
        <Card className="text-center py-12">
          <p className="text-text-muted">Failed to load dashboard data</p>
          <Button onClick={fetchDashboardData} className="mt-4">
            Retry
          </Button>
        </Card>
      </div>
    )
  }

  const maxProcessingTime = analytics?.max_processing_time_seconds ?? null
  const minProcessingTime = analytics?.min_processing_time_seconds ?? null

  return (
    <div className="container mx-auto px-6 py-12 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold gradient-text mb-2">Dashboard</h1>
          <p className="text-text-secondary">Welcome back! Here's your overview</p>
        </div>
        <Button onClick={() => navigate('/upload')}>
          <Plus className="w-4 h-4 mr-2" />
          New Report
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Storage Usage */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-primary-500/10">
              <HardDrive className="w-6 h-6 text-primary-400" />
            </div>
            <span className="text-xs text-text-muted">Storage</span>
          </div>
          <div className="mb-2">
            <div className="text-2xl font-bold">{formatBytes(stats.storage_used)}</div>
            <div className="text-sm text-text-muted">
              of {formatBytes(stats.storage_limit)}
            </div>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-primary-500 to-accent-purple h-2 rounded-full transition-all"
              style={{ width: `${Math.min(stats.storage_used_percent, 100)}%` }}
            />
          </div>
          <div className="text-xs text-text-muted mt-1">
            {stats.storage_used_percent.toFixed(1)}% used
          </div>
        </Card>

        {/* Total Reports */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-accent-purple/10">
              <FileText className="w-6 h-6 text-accent-purple" />
            </div>
            <span className="text-xs text-text-muted">Total</span>
          </div>
          <div className="text-2xl font-bold mb-1">{stats.total_reports}</div>
          <div className="text-sm text-text-muted">Reports generated</div>
        </Card>

        {/* Completed Reports */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-green-500/10">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
            <span className="text-xs text-text-muted">Completed</span>
          </div>
          <div className="text-2xl font-bold mb-1">{stats.reports_completed}</div>
          <div className="text-sm text-text-muted">Successfully generated</div>
        </Card>

        {/* Processing Reports */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-primary-500/10">
              <Loader2 className="w-6 h-6 text-primary-400" />
            </div>
            <span className="text-xs text-text-muted">Active</span>
          </div>
          <div className="text-2xl font-bold mb-1">
            {stats.reports_processing + stats.reports_queued}
          </div>
          <div className="text-sm text-text-muted">In progress</div>
        </Card>
      </div>

      {/* Recent Reports & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Reports */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-text-primary">Recent Reports</h2>
              <Button
                variant="ghost"
                onClick={() => navigate('/history')}
                className="text-sm"
              >
                View All
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>

            {recentJobs.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No reports yet</h3>
                <p className="text-text-muted mb-4">Start generating your first report</p>
                <Button onClick={() => navigate('/upload')}>
                  Create Report
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {recentJobs.map((job) => {
                  const StatusIcon = getStatusIcon(job.status)
                  return (
                    <div
                      key={job.id}
                      className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-primary-500 transition-colors cursor-pointer"
                      onClick={() => {
                        if (job.status === 'completed') {
                          navigate(`/success/${job.id}`)
                        } else if (job.status === 'processing' || job.status === 'queued') {
                          navigate(`/processing/${job.id}`)
                        }
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <StatusIcon
                              className={`w-5 h-5 ${getStatusColor(job.status)} ${
                                job.status === 'processing' ? 'animate-spin' : ''
                              }`}
                            />
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
                        <div className="text-right ml-4">
                          <div className="text-2xl font-bold text-primary-400">
                            {job.progress || 0}%
                          </div>
                          <div className="text-xs text-text-muted">Progress</div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Quick Actions & Stats */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card className="p-6">
            <h2 className="text-xl font-bold text-text-primary mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Button
                className="w-full justify-start"
                onClick={() => navigate('/upload')}
              >
                <Plus className="w-4 h-4 mr-2" />
                Generate New Report
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/history')}
              >
                <FileText className="w-4 h-4 mr-2" />
                View All Reports
              </Button>
            </div>
          </Card>

          {/* Report Status Breakdown */}
          <Card className="p-6">
            <h2 className="text-xl font-bold text-text-primary mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Status Breakdown
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-text-secondary">Completed</span>
                </div>
                <span className="font-semibold">{stats.reports_completed}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 text-primary-400" />
                  <span className="text-sm text-text-secondary">Processing</span>
                </div>
                <span className="font-semibold">{stats.reports_processing}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm text-text-secondary">Queued</span>
                </div>
                <span className="font-semibold">{stats.reports_queued}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <XCircle className="w-4 h-4 text-red-400" />
                  <span className="text-sm text-text-secondary">Failed</span>
                </div>
                <span className="font-semibold">{stats.reports_failed}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Analytics Section */}
      <div className="mt-8">
        <Card className="p-6">
          <button
            onClick={handleToggleAnalytics}
            className="w-full flex items-center justify-between mb-4 hover:opacity-80 transition-opacity"
          >
            <h2 className="text-2xl font-bold text-text-primary flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-primary-400" />
              Analytics
            </h2>
            {showAnalytics ? (
              <ChevronUp className="w-5 h-5 text-text-secondary transition-transform duration-200" />
            ) : (
              <ChevronDown className="w-5 h-5 text-text-secondary transition-transform duration-200" />
            )}
          </button>

          {showAnalytics && (
            <div className="space-y-6 transition-all duration-300 ease-in-out animate-fade-in">
              {/* Time Period Selector */}
              <div className="flex gap-2">
                {[7, 30, 90].map((d) => (
                  <button
                    key={d}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      if (analyticsDays !== d && !analyticsLoading && !isTransitioning) {
                        setAnalyticsDays(d)
                        fetchAnalytics(d)
                      }
                    }}
                    disabled={analyticsLoading || isTransitioning}
                    className={`
                      px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ease-in-out
                      ${analyticsDays === d
                        ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/50 scale-105'
                        : 'bg-slate-800 text-text-secondary hover:bg-slate-700 hover:text-text-primary border border-slate-700 hover:scale-105'
                      }
                      ${analyticsLoading || isTransitioning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    {d}d
                  </button>
                ))}
              </div>

              {analyticsLoading ? (
                <div className="flex items-center justify-center py-12 transition-opacity duration-500 ease-in-out">
                  <div className="text-center">
                    <Loader2 className="w-8 h-8 text-primary-400 animate-spin mx-auto mb-2" />
                    <p className="text-sm text-text-secondary">Loading analytics...</p>
                  </div>
                </div>
              ) : analytics ? (
                <div 
                  key={`analytics-${analyticsDays}`}
                  className={`space-y-6 transition-all duration-500 ease-in-out ${
                    showAnalyticsContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'
                  }`}
                >
                  {/* Advanced Analytics Metrics - Different from dashboard stats */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Growth Rate */}
                    <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-primary-500/50 transition-all duration-200">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-text-secondary">Growth Rate</p>
                        <TrendingUp className={`w-4 h-4 ${(analytics.growth_rate_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`} />
                      </div>
                      <p className={`text-2xl font-bold ${(analytics.growth_rate_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(analytics.growth_rate_percent || 0) >= 0 ? '+' : ''}{analytics.growth_rate_percent?.toFixed(1) || 0}%
                      </p>
                      <p className="text-xs text-text-muted mt-1">
                        vs previous period
                      </p>
                    </div>

                    {/* Average Pages Per Report */}
                    <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-primary-500/50 transition-all duration-200">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-text-secondary">Avg Pages/Report</p>
                        <FileText className="w-4 h-4 text-blue-400" />
                      </div>
                      <p className="text-2xl font-bold text-blue-400">
                        {analytics.avg_pages_per_report?.toFixed(1) || 0}
                      </p>
                      <p className="text-xs text-text-muted mt-1">
                        {analytics.total_pages_generated || 0} total pages
                      </p>
                    </div>

                    {/* Average Sections Per Report */}
                    <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-primary-500/50 transition-all duration-200">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-text-secondary">Avg Sections/Report</p>
                        <BarChart3 className="w-4 h-4 text-purple-400" />
                      </div>
                      <p className="text-2xl font-bold text-purple-400">
                        {analytics.avg_sections_per_report?.toFixed(1) || 0}
                      </p>
                      <p className="text-xs text-text-muted mt-1">
                        {analytics.total_sections_written || 0} total sections
                      </p>
                    </div>

                    {/* Average Storage Per Report */}
                    <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-primary-500/50 transition-all duration-200">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-text-secondary">Avg Size/Report</p>
                        <HardDrive className="w-4 h-4 text-orange-400" />
                      </div>
                      <p className="text-2xl font-bold text-orange-400">
                        {formatBytes(analytics.avg_storage_per_report_bytes || 0)}
                      </p>
                      <p className="text-xs text-text-muted mt-1">
                        Per completed report
                      </p>
                    </div>
                  </div>

                  {/* Content Quality & Performance Insights */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Content Quality Metrics */}
                    <div className="p-6 bg-slate-800/50 rounded-lg border border-slate-700">
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <FileText className="w-5 h-5 text-primary-400" />
                        Content Quality Metrics
                      </h3>
                      <div className="space-y-4">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-text-secondary">Total Pages Generated</span>
                            <span className="font-semibold text-primary-400">
                              {analytics.total_pages_generated || 0}
                            </span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(((analytics.total_pages_generated || 0) / 100) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-text-secondary">Total Sections Written</span>
                            <span className="font-semibold text-green-400">
                              {analytics.total_sections_written || 0}
                            </span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(((analytics.total_sections_written || 0) / 200) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-text-secondary">Total Chapters Created</span>
                            <span className="font-semibold text-purple-400">
                              {analytics.total_chapters_created || 0}
                            </span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-2">
                            <div
                              className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(((analytics.total_chapters_created || 0) / 50) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                        <div className="pt-2 border-t border-slate-700">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-text-secondary">Avg Pages per Report</span>
                            <span className="font-semibold text-text-primary">
                              {analytics.avg_pages_per_report?.toFixed(1) || 0} pages
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Processing Performance */}
                    <div className="p-6 bg-slate-800/50 rounded-lg border border-slate-700">
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Clock className="w-5 h-5 text-primary-400" />
                        Processing Performance
                      </h3>
                      <div className="space-y-4">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-text-secondary">Average</span>
                            <span className="font-semibold text-text-primary">
                              {formatTime(analytics.avg_processing_time_seconds)}
                            </span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: '60%' }}
                            />
                          </div>
                        </div>
                        {maxProcessingTime !== null && maxProcessingTime > 0 && (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-text-secondary">Longest</span>
                              <span className="font-semibold text-text-primary">
                                {formatTime(maxProcessingTime)}
                              </span>
                            </div>
                            <div className="w-full bg-slate-700 rounded-full h-2">
                              <div
                                className="bg-orange-500 h-2 rounded-full transition-all duration-500"
                                style={{ width: '100%' }}
                              />
                            </div>
                          </div>
                        )}
                        {minProcessingTime !== null && minProcessingTime > 0 && (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-text-secondary">Fastest</span>
                              <span className="font-semibold text-text-primary">
                                {formatTime(minProcessingTime)}
                              </span>
                            </div>
                            <div className="w-full bg-slate-700 rounded-full h-2">
                              <div
                                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                                style={{ width: '30%' }}
                              />
                            </div>
                          </div>
                        )}
                        <div className="pt-2 border-t border-slate-700">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-text-secondary">Reports per Day</span>
                            <span className="font-semibold text-text-primary">
                              {analytics.reports_per_day?.toFixed(2) || 0} reports
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Reports by Status with Percentages */}
                    <div className="p-6 bg-slate-800/50 rounded-lg border border-slate-700">
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-primary-400" />
                        Status Distribution
                      </h3>
                      <div className="space-y-3">
                        {Object.entries(analytics.reports_by_status).map(([status, count]) => {
                          const total = Object.values(analytics.reports_by_status).reduce((a, b) => a + b, 0)
                          const percentage = total > 0 ? (count / total) * 100 : 0
                          const colors: Record<string, { bg: string; text: string }> = {
                            completed: { bg: 'bg-green-500', text: 'text-green-400' },
                            processing: { bg: 'bg-blue-500', text: 'text-blue-400' },
                            queued: { bg: 'bg-yellow-500', text: 'text-yellow-400' },
                            failed: { bg: 'bg-red-500', text: 'text-red-400' },
                          }
                          const color = colors[status] || { bg: 'bg-slate-500', text: 'text-slate-400' }
                          return (
                            <div key={status} className="transition-all duration-200">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-text-secondary capitalize flex items-center gap-2">
                                  <div className={`w-2 h-2 rounded-full ${color.bg}`} />
                                  {status}
                                </span>
                                <div className="flex items-center gap-2">
                                  <span className={`font-semibold ${color.text}`}>{count}</span>
                                  <span className="text-xs text-text-muted">({percentage.toFixed(1)}%)</span>
                                </div>
                              </div>
                              <div className="w-full bg-slate-700 rounded-full h-2.5">
                                <div
                                  className={`h-2.5 rounded-full transition-all duration-500 ${color.bg}`}
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Efficiency & Trends Summary */}
                  <div className="p-6 bg-gradient-to-r from-primary-500/10 to-accent-purple/10 rounded-lg border border-primary-500/30">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-primary-400" />
                      Efficiency & Trends
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-400">
                          {analytics.success_rate_percent?.toFixed(1) || 0}%
                        </p>
                        <p className="text-xs text-text-muted mt-1">Success Rate</p>
                      </div>
                      <div className="text-center">
                        <p className={`text-2xl font-bold ${(analytics.growth_rate_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {(analytics.growth_rate_percent || 0) >= 0 ? '+' : ''}{analytics.growth_rate_percent?.toFixed(1) || 0}%
                        </p>
                        <p className="text-xs text-text-muted mt-1">Growth Rate</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-400">
                          {analytics.reports_per_day?.toFixed(2) || 0}
                        </p>
                        <p className="text-xs text-text-muted mt-1">Reports/Day</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-purple-400">
                          {formatBytes(analytics.avg_storage_per_report_bytes || 0)}
                        </p>
                        <p className="text-xs text-text-muted mt-1">Avg Report Size</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

