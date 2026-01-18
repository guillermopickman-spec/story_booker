"use client"

import { useState } from "react"
import { GenerationForm, GenerationFormData } from "@/components/GenerationForm"
import { ProgressTracker } from "@/components/ProgressTracker"
import { PDFPreview } from "@/components/PDFPreview"
import { Alert } from "@/components/ui/alert"
import { createJob } from "@/lib/api"
import { JobStatus } from "@/lib/types"
import { BookOpen, Sparkles, UserPlus } from "lucide-react"
import Link from "next/link"

type ViewState = "form" | "progress" | "preview"

export default function Home() {
  const [viewState, setViewState] = useState<ViewState>("form")
  const [jobId, setJobId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([])

  const handleFormSubmit = async (data: GenerationFormData) => {
    setIsLoading(true)
    setError(null)
    setJobId(null)

    try {
      const response = await createJob({
        theme: data.theme || undefined,
        num_pages: data.num_pages,
        style: data.style,
        languages: data.languages,
        pod_ready: data.pod_ready,
        character_ids: data.character_ids,
      })

      setJobId(response.job_id)
      setAvailableLanguages(data.languages)
      setViewState("progress")
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create job. Please try again."
      setError(errorMessage)
      setViewState("form")
    } finally {
      setIsLoading(false)
    }
  }

  const handleProgressComplete = (status: JobStatus) => {
    if (status === "completed") {
      setViewState("preview")
    } else if (status === "failed") {
      // Reset state when job fails or is not found
      setJobId(null)
      setError(null)
      setAvailableLanguages([])
      setViewState("form")
    }
  }

  const handleNewStorybook = () => {
    setViewState("form")
    setJobId(null)
    setError(null)
    setAvailableLanguages([])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      {/* Header */}
      <header className="border-b-2 border-purple-200 bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] rounded-xl shadow-lg">
                <BookOpen className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] bg-clip-text text-transparent">
                  Story Booker
                </h1>
                <p className="text-xs text-gray-600">AI-Powered Storybook Generator</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/characters">
                <button
                  className="px-4 py-2 text-sm font-semibold text-[#6366f1] hover:text-[#5855eb] transition-colors flex items-center gap-2"
                >
                  <UserPlus className="h-4 w-4" />
                  Characters
                </button>
              </Link>
              {viewState !== "form" && (
                <button
                  onClick={handleNewStorybook}
                  className="px-4 py-2 text-sm font-semibold text-[#6366f1] hover:text-[#5855eb] transition-colors flex items-center gap-2"
                >
                  <Sparkles className="h-4 w-4" />
                  New Storybook
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-5xl">
        <div className="space-y-8">
          {/* Error Alert */}
          {error && (
            <Alert variant="error" className="animate-fade-in">
              <p className="font-semibold">Error</p>
              <p>{error}</p>
            </Alert>
          )}

          {/* Form View */}
          {viewState === "form" && (
            <div className="flex flex-col items-center">
              <GenerationForm onSubmit={handleFormSubmit} isLoading={isLoading} />
            </div>
          )}

          {/* Progress View */}
          {viewState === "progress" && jobId && (
            <div className="flex flex-col items-center">
              <ProgressTracker jobId={jobId} onComplete={handleProgressComplete} />
            </div>
          )}

          {/* Preview View */}
          {viewState === "preview" && jobId && (
            <div className="flex flex-col items-center gap-4">
              <PDFPreview jobId={jobId} availableLanguages={availableLanguages} />
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t-2 border-purple-200 bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-gray-600">
          <p>Built with ❤️ using Next.js, FastAPI, and AI</p>
        </div>
      </footer>
    </div>
  )
}
