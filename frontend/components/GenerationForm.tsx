"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Slider } from "@/components/ui/slider"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ART_STYLES, LANGUAGES } from "@/lib/constants"
import { ArtStyle, Language } from "@/lib/types"
import { Sparkles } from "lucide-react"

const formSchema = z.object({
  theme: z.string().optional(),
  num_pages: z.number().min(1).max(10),
  style: z.string().optional(),
  languages: z.array(z.enum(["en", "es"])).min(1, "Select at least one language"),
  pod_ready: z.boolean(),
})

export type GenerationFormData = z.infer<typeof formSchema>

interface GenerationFormProps {
  onSubmit: (data: GenerationFormData) => void
  isLoading?: boolean
}

export function GenerationForm({ onSubmit, isLoading = false }: GenerationFormProps) {
  const [numPages, setNumPages] = useState(5)
  const [selectedLanguages, setSelectedLanguages] = useState<Language[]>(["en"])

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<GenerationFormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      theme: "",
      num_pages: 5,
      style: "3D_RENDERED",
      languages: ["en"],
      pod_ready: false,
    },
  })

  const podReady = watch("pod_ready")

  const toggleLanguage = (language: Language) => {
    const current = selectedLanguages
    const newLanguages = current.includes(language)
      ? current.filter((l) => l !== language)
      : [...current, language]
    setSelectedLanguages(newLanguages)
    setValue("languages", newLanguages, { shouldValidate: true })
  }

  const onFormSubmit = (data: GenerationFormData) => {
    onSubmit(data)
  }

  return (
    <Card className="w-full max-w-2xl mx-auto animate-fade-in">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-[#6366f1]" />
          <CardTitle className="text-3xl bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] bg-clip-text text-transparent">
            Create Your Storybook
          </CardTitle>
        </div>
        <CardDescription className="text-base">
          Tell us your story idea, and we'll bring it to life with AI-generated illustrations
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
          {/* Theme Input */}
          <div className="space-y-2">
            <Label htmlFor="theme" className="text-base">
              Story Theme <span className="text-gray-400">(optional)</span>
            </Label>
            <Textarea
              id="theme"
              placeholder="e.g., A brave little mouse goes on an adventure to find the golden cheese..."
              className="min-h-[100px] text-base"
              {...register("theme")}
            />
            {errors.theme && (
              <p className="text-sm text-red-600">{errors.theme.message}</p>
            )}
          </div>

          {/* Pages Slider */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="pages" className="text-base">
                Number of Pages
              </Label>
              <span className="text-2xl font-bold text-[#6366f1]">{numPages}</span>
            </div>
            <Slider
              id="pages"
              min={1}
              max={10}
              value={numPages}
              onValueChange={(value) => {
                setNumPages(value)
                setValue("num_pages", value)
              }}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>1</span>
              <span>10</span>
            </div>
          </div>

          {/* Art Style Selector */}
          <div className="space-y-2">
            <Label htmlFor="style" className="text-base">
              Art Style
            </Label>
            <Select
              id="style"
              {...register("style")}
              onChange={(e) => setValue("style", e.target.value)}
              defaultValue="3D_RENDERED"
            >
              {ART_STYLES.map((style) => (
                <option key={style.value} value={style.value}>
                  {style.label} - {style.description}
                </option>
              ))}
            </Select>
          </div>

          {/* Language Selector */}
          <div className="space-y-3">
            <Label className="text-base">Languages</Label>
            <div className="flex flex-wrap gap-4">
              {LANGUAGES.map((lang) => (
                <div key={lang.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`lang-${lang.value}`}
                    checked={selectedLanguages.includes(lang.value)}
                    onChange={() => toggleLanguage(lang.value)}
                  />
                  <Label
                    htmlFor={`lang-${lang.value}`}
                    className="text-base font-normal cursor-pointer"
                  >
                    {lang.label}
                  </Label>
                </div>
              ))}
            </div>
            {errors.languages && (
              <p className="text-sm text-red-600">{errors.languages.message}</p>
            )}
          </div>

          {/* POD Ready Toggle */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 border-2 border-gray-200">
            <div className="space-y-1">
              <Label htmlFor="pod-ready" className="text-base cursor-pointer">
                Print-on-Demand Ready
              </Label>
              <p className="text-sm text-gray-600">
                Enable CMYK colors and bleed margins for Amazon KDP
              </p>
            </div>
            <Switch
              id="pod-ready"
              checked={podReady}
              onCheckedChange={(checked) => setValue("pod_ready", checked)}
            />
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            size="lg"
            className="w-full text-lg h-14 bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] hover:from-[#5855eb] hover:to-[#7c3aed] shadow-lg"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" />
                Generate Storybook
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
