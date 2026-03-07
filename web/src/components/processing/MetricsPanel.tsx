import { FileText, BookOpen, FileEdit, Clock } from 'lucide-react'
import Card from '@/components/common/Card'

interface MetricsPanelProps {
  filesAnalyzed: number
  chaptersCreated: number
  sectionsWritten: number
  timeElapsed: string
}

export default function MetricsPanel({
  filesAnalyzed,
  chaptersCreated,
  sectionsWritten,
  timeElapsed,
}: MetricsPanelProps) {
  const metrics = [
    {
      icon: FileText,
      label: 'Files Analyzed',
      value: filesAnalyzed,
      color: 'text-primary-400',
    },
    {
      icon: BookOpen,
      label: 'Chapters Created',
      value: chaptersCreated,
      color: 'text-accent-purple',
    },
    {
      icon: FileEdit,
      label: 'Sections Written',
      value: sectionsWritten,
      color: 'text-accent-cyan',
    },
    {
      icon: Clock,
      label: 'Time Elapsed',
      value: timeElapsed,
      color: 'text-accent-amber',
    },
  ]

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Metrics</h3>
      <div className="space-y-4">
        {metrics.map((metric, index) => (
          <div key={index} className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-slate-700/50 ${metric.color}`}>
              <metric.icon className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <div className="text-sm text-text-muted">{metric.label}</div>
              <div className="text-lg font-semibold">{metric.value}</div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

