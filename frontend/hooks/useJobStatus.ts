import { useState, useEffect, useCallback } from "react"
import { getJobStatus } from "@/lib/api"
import { JobStatusResponse } from "@/lib/types"

export function useJobStatus(jobId: string | null, enabled: boolean = true) {
  const [status, setStatus] = useState<JobStatusResponse | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [isPolling, setIsPolling] = useState(false)

  const pollStatus = useCallback(async () => {
    if (!jobId || !enabled) return

    setIsPolling(true)
    try {
      const jobStatus = await getJobStatus(jobId)
      setStatus(jobStatus)
      setError(null)

      // Stop polling if job is completed or failed
      if (jobStatus.status === "completed" || jobStatus.status === "failed") {
        setIsPolling(false)
        return false
      }
      return true
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to poll job status")
      
      // If job not found (404), stop polling immediately - job doesn't exist
      if (err instanceof Error && err.message.includes("404") && err.message.includes("Job not found")) {
        setError(error)
        setIsPolling(false)
        return false
      }
      
      setError(error)
      setIsPolling(false)
      return false
    } finally {
      setIsPolling(false)
    }
  }, [jobId, enabled])

  useEffect(() => {
    if (!jobId || !enabled) return

    // Initial poll
    pollStatus()

    // Set up polling interval (every 2 seconds)
    const interval = setInterval(async () => {
      const shouldContinue = await pollStatus()
      if (!shouldContinue) {
        clearInterval(interval)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [jobId, enabled, pollStatus])

  return {
    status,
    error,
    isPolling,
    refetch: pollStatus,
  }
}
