// src/components/ui/alert.jsx
import * as React from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const alertVariants = cva(
  'relative w-full rounded-lg border p-4 [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg+div]:translate-y-[-3px] [&>svg+div]:pl-7',
  {
    variants: {
      variant: {
        default: 'bg-white text-slate-950 border-slate-200',
        destructive:
          'border-red-200/50 text-red-900 dark:border-red-800/50 dark:text-red-50',
        warning:
          'border-yellow-200/50 bg-yellow-50 text-yellow-900 dark:border-yellow-800/50 dark:bg-yellow-950 dark:text-yellow-50',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

function Alert({ className, variant = 'default', ...props }) {
  return (
    <div
      role="alert"
      className={cn(alertVariants({ variant }), className)}
      {...props}
    />
  )
}

function AlertTitle({ className, ...props }) {
  return (
    <h5
      className={cn('mb-1 font-medium leading-none tracking-tight', className)}
      {...props}
    />
  )
}

function AlertDescription({ className, ...props }) {
  return (
    <div
      className={cn('text-sm [&_p]:leading-relaxed', className)}
      {...props}
    />
  )
}

export { Alert, AlertTitle, AlertDescription }