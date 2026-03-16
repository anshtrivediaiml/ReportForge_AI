import { motion } from 'framer-motion'
import { CheckCircle } from 'lucide-react'
import { cn } from '@/utils/helpers'
import { StageStatus } from '@/types'
import Card from '@/components/common/Card'

interface AgentCardProps {
  agent: { id: string; name: string; description: string; icon: string }
  status: StageStatus
  progress: number
  message: string
  isActive: boolean
  isComplete: boolean
  isPending: boolean
  index: number
  logs: string[]
}

export default function AgentCard({
  agent,
  status,
  progress,
  message,
  isActive,
  isComplete,
  isPending,
  index,
  logs,
}: AgentCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card
        className={cn(
          'relative transition-all duration-300',
          isActive && 'border-primary-500 shadow-lg shadow-primary-500/50 scale-105',
          isComplete && 'border-success bg-success/10',
          isPending && 'border-slate-700 bg-slate-800/50 opacity-60'
        )}
      >
        {/* Connection line */}
        {index < 3 && (
          <div className="absolute left-1/2 -bottom-4 w-0.5 h-4 bg-gradient-to-b from-slate-600 to-transparent transform -translate-x-1/2" />
        )}

        <div className="flex items-start gap-4">
          {/* Icon */}
          <div
            className={cn(
              'relative p-3 rounded-lg',
              isActive && 'animate-pulse-glow bg-primary-500/20',
              isComplete && 'bg-success/20',
              isPending && 'bg-slate-700'
            )}
          >
            <div className="text-3xl">{agent.icon}</div>

            {/* Status indicator */}
            {isActive && (
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="absolute -top-1 -right-1 w-3 h-3 bg-primary-500 rounded-full"
              />
            )}

            {isComplete && (
              <CheckCircle className="absolute -top-1 -right-1 w-5 h-5 text-success" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-lg font-semibold">{agent.name}</h4>
              <span
                className={cn(
                  'text-xs px-2 py-1 rounded',
                  isActive && 'bg-primary-500/20 text-primary-400',
                  isComplete && 'bg-success/20 text-success',
                  isPending && 'bg-slate-700 text-slate-400'
                )}
              >
                {status}
              </span>
            </div>

            <p className="text-sm text-text-secondary mb-3">{message || agent.description}</p>

            {/* Progress bar */}
            {isActive && (
              <div className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                  <span>Progress</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-primary-600 to-primary-400"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            )}

            {/* Recent logs */}
            {isActive && logs.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-700">
                <div className="space-y-1">
                  {logs.slice(-3).map((log, i) => (
                    <div key={i} className="text-xs font-mono text-slate-400 flex items-start gap-2">
                      <span className="text-primary-400">→</span>
                      <span>{log}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

