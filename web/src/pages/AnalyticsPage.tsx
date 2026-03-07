import { useState, useEffect } from 'react'
import { BarChart3, Clock, HardDrive, FileText, TrendingUp, Users, Activity } from 'lucide-react'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import { getMyMetrics, getSystemMetrics, type UserMetrics, type SystemMetrics } from '@/services/api'
import { formatBytes, formatDate } from '@/utils/formatters'
import toast from 'react-hot-toast'
import Skeleton from '@/components/common/Skeleton'

export default function AnalyticsPage() {
  const [userMetrics, setUserMetrics] = useState<UserMetrics | null>(null)
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)
  const [viewMode, setViewMode] = useState<'user' | 'system'>('user')

  useEffect(() => {
    fetchMetrics()
  }, [days, viewMode])

  const fetchMetrics = async () => {
    setLoading(true)
    try {
      if (viewMode === 'user') {
        const metrics = await getMyMetrics(days)
        setUserMetrics(metrics)
      } else {
        const metrics = await getSystemMetrics(days)
        setSystemMetrics(metrics)
      }
    } catch (error: any) {
      console.error('Failed to fetch metrics:', error)
      toast.error(error.response?.data?.detail || 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    return `${Math.round(seconds / 3600)}h`
  }

  const StatusCard = ({ title, value, icon: Icon, color }: { title: string; value: number | string; icon: any; color: string }) => (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-text-secondary mb-1">{title}</p>
          <p className={`text-3xl font-bold ${color}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color === 'text-primary-400' ? 'bg-primary-400/10' : color === 'text-green-400' ? 'bg-green-400/10' : color === 'text-blue-400' ? 'bg-blue-400/10' : color === 'text-purple-400' ? 'bg-purple-400/10' : color === 'text-indigo-400' ? 'bg-indigo-400/10' : 'bg-emerald-400/10'}`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </Card>
  )

  if (loading && !userMetrics && !systemMetrics) {
    return (
      <div className="container mx-auto px-6 py-12 max-w-7xl">
        <Skeleton variant="text" className="h-8 w-64 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rectangular" className="h-32" />
          ))}
        </div>
        <Skeleton variant="rectangular" className="h-96" />
      </div>
    )
  }

  const metrics = viewMode === 'user' ? userMetrics : systemMetrics

  return (
    <div className="container mx-auto px-6 py-12 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold gradient-text mb-2">Analytics Dashboard</h1>
          <p className="text-text-secondary">Track your usage and performance metrics</p>
        </div>
        <div className="flex items-center gap-4 mt-4 md:mt-0">
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'user' ? 'primary' : 'outline'}
              onClick={() => setViewMode('user')}
              className="text-sm"
            >
              My Metrics
            </Button>
            <Button
              variant={viewMode === 'system' ? 'primary' : 'outline'}
              onClick={() => setViewMode('system')}
              className="text-sm"
            >
              System Metrics
            </Button>
          </div>
          <div className="flex gap-2">
            {[7, 30, 90].map((d) => (
              <Button
                key={d}
                variant={days === d ? 'primary' : 'outline'}
                onClick={() => setDays(d)}
                className="text-sm"
              >
                {d}d
              </Button>
            ))}
          </div>
        </div>
      </div>

      {metrics && (
        <>
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatusCard
              title="Total Reports"
              value={metrics.total_reports}
              icon={FileText}
              color="text-primary-400"
            />
            <StatusCard
              title="Completed"
              value={metrics.reports_by_status.completed}
              icon={TrendingUp}
              color="text-green-400"
            />
            <StatusCard
              title="Avg Processing Time"
              value={formatTime(metrics.avg_processing_time_seconds)}
              icon={Clock}
              color="text-blue-400"
            />
            <StatusCard
              title="Storage Used"
              value={formatBytes(metrics.storage_used_bytes)}
              icon={HardDrive}
              color="text-purple-400"
            />
            {viewMode === 'system' && systemMetrics && (
              <>
                <StatusCard
                  title="Total Users"
                  value={systemMetrics.total_users}
                  icon={Users}
                  color="text-indigo-400"
                />
                <StatusCard
                  title="Active Users"
                  value={systemMetrics.active_users}
                  icon={Activity}
                  color="text-emerald-400"
                />
              </>
            )}
          </div>

          {/* Reports by Status */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <BarChart3 className="w-6 h-6 text-primary-400" />
                Reports by Status
              </h2>
              <div className="space-y-4">
                {Object.entries(metrics.reports_by_status).map(([status, count]) => {
                  const total = Object.values(metrics.reports_by_status).reduce((a, b) => a + b, 0)
                  const percentage = total > 0 ? (count / total) * 100 : 0
                  const colors: Record<string, string> = {
                    completed: 'bg-green-500',
                    processing: 'bg-blue-500',
                    queued: 'bg-yellow-500',
                    failed: 'bg-red-500',
                  }
                  return (
                    <div key={status}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-text-secondary capitalize">{status}</span>
                        <span className="font-semibold">{count}</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${colors[status] || 'bg-slate-500'}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </Card>

            {/* Daily Reports Chart (System only) */}
            {viewMode === 'system' && systemMetrics && (
              <Card className="p-6">
                <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-primary-400" />
                  Daily Reports (Last 7 Days)
                </h2>
                <div className="space-y-3">
                  {systemMetrics.daily_reports.map((day, index) => {
                    const maxCount = Math.max(...systemMetrics.daily_reports.map(d => d.count), 1)
                    const height = (day.count / maxCount) * 100
                    return (
                      <div key={index} className="flex items-end gap-2">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm text-text-secondary">
                              {new Date(day.date).toLocaleDateString('en-IN', { 
                                timeZone: 'Asia/Kolkata',
                                month: 'short', 
                                day: 'numeric' 
                              })}
                            </span>
                            <span className="text-sm font-semibold">{day.count}</span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-8 relative overflow-hidden">
                            <div
                              className="bg-gradient-to-t from-primary-500 to-primary-400 h-full rounded-full transition-all"
                              style={{ width: `${height}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </Card>
            )}

            {/* Storage Usage (User only) */}
            {viewMode === 'user' && userMetrics && (
              <Card className="p-6">
                <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <HardDrive className="w-6 h-6 text-primary-400" />
                  Storage Usage
                </h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-text-secondary">Used</span>
                    <span className="font-semibold">{formatBytes(userMetrics.storage_used_bytes)}</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-4">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-purple-400 h-4 rounded-full transition-all"
                      style={{ width: '45%' }}
                    />
                  </div>
                  <p className="text-sm text-text-muted">
                    Analyzing last {userMetrics.period_days} days of activity
                  </p>
                </div>
              </Card>
            )}
          </div>

          {/* Summary */}
          <Card className="p-6">
            <h2 className="text-2xl font-bold mb-4">Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-text-secondary">
              <div>
                <p className="mb-2">
                  <span className="font-semibold text-text-primary">Period:</span> Last {metrics.period_days} days
                </p>
                <p className="mb-2">
                  <span className="font-semibold text-text-primary">Total Reports:</span> {metrics.total_reports}
                </p>
                <p>
                  <span className="font-semibold text-text-primary">Success Rate:</span>{' '}
                  {metrics.total_reports > 0
                    ? Math.round((metrics.reports_by_status.completed / metrics.total_reports) * 100)
                    : 0}
                  %
                </p>
              </div>
              <div>
                <p className="mb-2">
                  <span className="font-semibold text-text-primary">Average Processing Time:</span>{' '}
                  {formatTime(metrics.avg_processing_time_seconds)}
                </p>
                <p className="mb-2">
                  <span className="font-semibold text-text-primary">Storage Used:</span>{' '}
                  {formatBytes(metrics.storage_used_bytes)}
                </p>
                {viewMode === 'system' && systemMetrics && (
                  <p>
                    <span className="font-semibold text-text-primary">Active Users:</span>{' '}
                    {systemMetrics.active_users} / {systemMetrics.total_users}
                  </p>
                )}
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}

