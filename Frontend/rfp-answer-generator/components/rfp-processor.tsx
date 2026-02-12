'use client'

import { useState, useEffect } from 'react'
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

interface RFPProcessorProps {
  isLoading: boolean
  error?: string | null
  onRetry?: () => void
  progress?: number // 0-100
  currentStep?: string
}

export default function RFPProcessor({ isLoading, error, onRetry, progress = 0, currentStep = '' }: RFPProcessorProps) {
  return (
    <div className="flex min-h-96 items-center justify-center">
      <Card className="w-full max-w-md p-8 text-center">
        {error ? (
          <>
            <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
            <h2 className="mt-6 text-2xl font-bold text-foreground">Processing Failed</h2>
            <p className="mt-4 text-sm text-destructive">{error}</p>
            {onRetry && (
              <Button onClick={onRetry} className="mt-6">
                Try Again
              </Button>
            )}
          </>
        ) : (
          <>
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-primary" />
            <h2 className="mt-6 text-2xl font-bold text-foreground">Processing RFP</h2>
            <p className="mt-4 text-muted-foreground">
              Analyzing documents and generating intelligent answers based on your knowledge base...
            </p>

            {/* Progress bar */}
            <div className="mt-8 space-y-2">
              <Progress value={progress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{progress}%</span>
                <span>Processing...</span>
              </div>
            </div>

            {/* Current step */}
            {currentStep && (
              <p className="mt-4 text-sm text-primary font-medium">
                {currentStep}
              </p>
            )}
          </>
        )}
      </Card>
    </div>
  )
}
