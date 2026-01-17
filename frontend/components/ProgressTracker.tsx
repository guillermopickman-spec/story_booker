"use client"

import { useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { StatusBadge } from "./StatusBadge"
import { useJobStatus } from "@/hooks/useJobStatus"
import { JobStatus } from "@/lib/types"
import { FileText, CheckCircle2 } from "lucide-react"

interface ProgressTrackerProps {
  jobId: string | null
  onComplete?: (status: JobStatus) => void
}

export function ProgressTracker({ jobId, onComplete }: ProgressTrackerProps) {
  const { status, error } = useJobStatus(jobId, !!jobId)

  useEffect(() => {
    if (status && (status.status === "completed" || status.status === "failed")) {
      onComplete?.(status.status)
    }
  }, [status, onComplete])

  // If job not found (404), notify parent to reset
  useEffect(() => {
    if (error && error.message.includes("404") && error.message.includes("Job not found")) {
      onComplete?.("failed")
    }
  }, [error, jobId, onComplete])

  // Show error if job not found (404) even without status
  if (!jobId) {
    return null
  }

  // If error is "Job not found", show error card and let useEffect handle cleanup
  if (error && error.message.includes("404") && error.message.includes("Job not found")) {
    return (
      <Card className="w-full max-w-2xl mx-auto animate-fade-in">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-[#6366f1]" />
              <CardTitle>Generation Progress</CardTitle>
            </div>
            <StatusBadge status="failed" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="mt-4 p-4 bg-red-50 border-2 border-red-200 rounded-xl">
            <p className="text-sm font-semibold text-red-900 mb-1">Job Not Found</p>
            <p className="text-sm text-red-700">
              The job could not be found. Please try generating a new storybook.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Wait for status to load
  if (!status) {
    return (
      <Card className="w-full max-w-2xl mx-auto animate-fade-in">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-[#6366f1]" />
              <CardTitle>Generation Progress</CardTitle>
            </div>
            <StatusBadge status="pending" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center py-4 text-gray-600">
            Loading job status...
          </div>
        </CardContent>
      </Card>
    )
  }

  const progress = status.progress ?? 0
  const currentStep = status.current_step || "Initializing..."

  return (
    <Card className="w-full max-w-2xl mx-auto animate-fade-in">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-[#6366f1]" />
            <CardTitle>Generation Progress</CardTitle>
          </div>
          <StatusBadge status={status.status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Progress</span>
            <span className="font-semibold text-[#6366f1]">{progress}%</span>
          </div>
          <Progress value={progress} className="h-3" />
        </div>

        {/* Current Step */}
        <div className="space-y-2">
          <p className="text-sm font-semibold text-gray-700">Current Step:</p>
          <p className="text-base text-gray-900 bg-gray-50 p-3 rounded-lg border border-gray-200">
            {currentStep}
          </p>
        </div>

        {/* Error Message */}
        {status.status === "failed" && status.error_message && (
          <div className="mt-4 p-4 bg-red-50 border-2 border-red-200 rounded-xl">
            <p className="text-sm font-semibold text-red-900 mb-1">Error:</p>
            <p className="text-sm text-red-700 whitespace-pre-wrap">
              {status.error_message}
            </p>
          </div>
        )}

        {/* API Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border-2 border-red-200 rounded-xl">
            <p className="text-sm font-semibold text-red-900 mb-1">Connection Error:</p>
            <p className="text-sm text-red-700">{error.message}</p>
          </div>
        )}

        {/* Completion Message */}
        {status.status === "completed" && (
          <div className="mt-4 p-4 bg-green-50 border-2 border-green-200 rounded-xl flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
            <p className="text-sm text-green-900">
              Your storybook has been generated successfully! You can now preview and download it below.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
