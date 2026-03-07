import { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/utils/helpers'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export default function Card({ children, className, ...props }: CardProps) {
  return (
    <div
      className={cn('glass-card p-6', className)}
      {...props}
    >
      {children}
    </div>
  )
}

