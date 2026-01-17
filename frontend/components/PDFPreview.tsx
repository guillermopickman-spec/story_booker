"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { downloadPDF, getPDFUrl } from "@/lib/api"
import { FileDown, Maximize2, FileText } from "lucide-react"

interface PDFPreviewProps {
  jobId: string
  availableLanguages?: string[]
}

export function PDFPreview({ jobId, availableLanguages = ["en"] }: PDFPreviewProps) {
  const [selectedLanguage, setSelectedLanguage] = useState<string>(availableLanguages[0])
  const [isDownloading, setIsDownloading] = useState(false)
  const [showFullscreen, setShowFullscreen] = useState(false)
  const [pdfError, setPdfError] = useState<string | null>(null)

  const pdfUrl = getPDFUrl(jobId, selectedLanguage !== availableLanguages[0] ? selectedLanguage : undefined)

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const blob = await downloadPDF(jobId, selectedLanguage !== availableLanguages[0] ? selectedLanguage : undefined)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `storybook_${jobId}${selectedLanguage !== availableLanguages[0] ? `_${selectedLanguage}` : ""}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error("Failed to download PDF:", error)
      alert(`Failed to download PDF: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleFullscreen = () => {
    setShowFullscreen(true)
  }

  if (showFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-black bg-opacity-90 flex flex-col">
        <div className="flex items-center justify-between p-4 bg-gray-900 text-white">
          <h2 className="text-xl font-bold">PDF Preview</h2>
          <div className="flex items-center gap-4">
            {availableLanguages.length > 1 && (
              <Select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="bg-gray-800 text-white border-gray-700"
              >
                {availableLanguages.map((lang) => (
                  <option key={lang} value={lang}>
                    {lang.toUpperCase()}
                  </option>
                ))}
              </Select>
            )}
            <Button
              variant="secondary"
              onClick={() => setShowFullscreen(false)}
              className="bg-gray-700 hover:bg-gray-600"
            >
              Close
            </Button>
          </div>
        </div>
        <iframe
          src={pdfUrl}
          className="flex-1 w-full border-0"
          title="PDF Preview"
        />
      </div>
    )
  }

  return (
    <Card className="w-full max-w-4xl mx-auto animate-fade-in">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-[#6366f1]" />
            <CardTitle>Your Storybook</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {availableLanguages.length > 1 && (
              <Select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="w-32"
              >
                {availableLanguages.map((lang) => (
                  <option key={lang} value={lang}>
                    {lang.toUpperCase()}
                  </option>
                ))}
              </Select>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleFullscreen}
              className="flex items-center gap-2"
            >
              <Maximize2 className="h-4 w-4" />
              Fullscreen
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="w-full h-[600px] border-2 border-gray-200 rounded-lg overflow-hidden relative">
          {pdfError ? (
            <div className="flex items-center justify-center h-full bg-red-50 border-2 border-red-200 rounded-lg p-4">
              <div className="text-center">
                <p className="text-red-900 font-semibold mb-2">Failed to load PDF</p>
                <p className="text-red-700 text-sm mb-4">{pdfError}</p>
                <Button
                  onClick={() => {
                    setPdfError(null)
                    // Force iframe reload
                    const iframe = document.querySelector('iframe[title="PDF Preview"]') as HTMLIFrameElement
                    if (iframe) {
                      iframe.src = iframe.src
                    }
                  }}
                  variant="outline"
                >
                  Retry
                </Button>
              </div>
            </div>
          ) : (
            <iframe
              src={pdfUrl}
              className="w-full h-full border-0"
              title="PDF Preview"
              onError={() => {
                setPdfError("Failed to load PDF. Please try downloading it instead.")
              }}
            />
          )}
        </div>
      </CardContent>
      <CardFooter className="flex justify-center pt-4">
        <Button
          size="lg"
          onClick={handleDownload}
          disabled={isDownloading}
          className="bg-gradient-to-r from-[#10b981] to-[#14b8a6] hover:from-[#059669] hover:to-[#0d9488] shadow-lg"
        >
          {isDownloading ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              Downloading...
            </>
          ) : (
            <>
              <FileDown className="mr-2 h-5 w-5" />
              Download PDF
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}
