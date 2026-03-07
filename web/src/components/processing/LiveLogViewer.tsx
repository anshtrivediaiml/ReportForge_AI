import { useEffect, useRef } from 'react'
import { Terminal } from 'lucide-react'
import Card from '@/components/common/Card'
import { cn } from '@/utils/helpers'

interface LiveLogViewerProps {
  logs: string[]
  autoScroll?: boolean
  maxHeight?: string
}

export default function LiveLogViewer({
  logs,
  autoScroll = true,
  maxHeight = '500px',
}: LiveLogViewerProps) {
  const logEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (autoScroll) {
      logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4" />
          <h3 className="font-semibold">Live Logs</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-success">
          <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
          Live
        </div>
      </div>

      <div
        className="overflow-y-auto font-mono text-xs space-y-1"
        style={{ maxHeight }}
      >
        {logs.length === 0 ? (
          <div className="text-text-muted text-center py-8">Waiting for logs...</div>
        ) : (
          logs.map((log, index) => {
            const isError = log.toLowerCase().includes('error')
            const isWarning = log.toLowerCase().includes('warning')
            const isSuccess = log.toLowerCase().includes('success') || log.includes('✓')

            return (
              <div
                key={index}
                className={cn(
                  'px-3 py-2 rounded border-b border-slate-800 hover:bg-slate-800/50',
                  isError && 'bg-red-900/20 text-red-400',
                  isWarning && 'bg-amber-900/20 text-amber-400',
                  isSuccess && 'bg-green-900/20 text-green-400'
                )}
              >
                {log}
              </div>
            )
          })
        )}
        <div ref={logEndRef} />
      </div>
    </Card>
  )
}

