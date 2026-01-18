"use client"

import { useState, useEffect } from "react"
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
import { ArtStyle, Language, CharacterMetadata } from "@/lib/types"
import { getCharacters, getCharacterImageUrl } from "@/lib/api"
import { Sparkles, UserPlus } from "lucide-react"
import Link from "next/link"

const formSchema = z.object({
  theme: z.string().optional(),
  num_pages: z.number().min(1).max(10),
  style: z.string().optional(),
  languages: z.array(z.enum(["en", "es"])).min(1, "Select at least one language"),
  pod_ready: z.boolean(),
  character_ids: z.array(z.string()).optional(),
})

export type GenerationFormData = z.infer<typeof formSchema>

interface GenerationFormProps {
  onSubmit: (data: GenerationFormData) => void
  isLoading?: boolean
}

export function GenerationForm({ onSubmit, isLoading = false }: GenerationFormProps) {
  const [numPages, setNumPages] = useState(5)
  const [selectedLanguages, setSelectedLanguages] = useState<Language[]>(["en"])
  const [characters, setCharacters] = useState<CharacterMetadata[]>([])
  const [selectedCharacterIds, setSelectedCharacterIds] = useState<string[]>([])
  const [loadingCharacters, setLoadingCharacters] = useState(false)
  const [charactersError, setCharactersError] = useState<string | null>(null)

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

  useEffect(() => {
    const loadCharacters = async () => {
      try {
        setLoadingCharacters(true)
        setCharactersError(null)
        const data = await getCharacters()
        setCharacters(data)
      } catch (err) {
        console.error("Failed to load characters:", err)
        const errorMessage = err instanceof Error ? err.message : "Failed to load characters"
        setCharactersError(errorMessage)
      } finally {
        setLoadingCharacters(false)
      }
    }
    loadCharacters()
  }, [])

  const toggleLanguage = (language: Language) => {
    const current = selectedLanguages
    const newLanguages = current.includes(language)
      ? current.filter((l) => l !== language)
      : [...current, language]
    setSelectedLanguages(newLanguages)
    setValue("languages", newLanguages, { shouldValidate: true })
  }

  const toggleCharacter = (characterId: string) => {
    const current = selectedCharacterIds
    const newIds = current.includes(characterId)
      ? current.filter((id) => id !== characterId)
      : [...current, characterId]
    setSelectedCharacterIds(newIds)
  }

  const onFormSubmit = (data: GenerationFormData) => {
    onSubmit({
      ...data,
      character_ids: selectedCharacterIds.length > 0 ? selectedCharacterIds : undefined,
    })
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

          {/* Character Selection */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-base">Select Characters (Optional)</Label>
              <Link href="/characters">
                <Button variant="outline" size="sm" type="button">
                  <UserPlus className="h-4 w-4 mr-1" />
                  Manage Characters
                </Button>
              </Link>
            </div>
            {loadingCharacters ? (
              <p className="text-sm text-gray-500">Loading characters...</p>
            ) : charactersError ? (
              <div className="p-4 rounded-xl bg-red-50 border-2 border-red-200 text-center">
                <p className="text-sm text-red-700 font-semibold mb-2">Error loading characters</p>
                <p className="text-xs text-red-600 mb-3">{charactersError}</p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  type="button"
                  onClick={() => {
                    setCharactersError(null)
                    const loadCharacters = async () => {
                      try {
                        setLoadingCharacters(true)
                        const data = await getCharacters()
                        setCharacters(data)
                      } catch (err) {
                        const errorMessage = err instanceof Error ? err.message : "Failed to load characters"
                        setCharactersError(errorMessage)
                      } finally {
                        setLoadingCharacters(false)
                      }
                    }
                    loadCharacters()
                  }}
                >
                  Retry
                </Button>
              </div>
            ) : characters.length === 0 ? (
              <div className="p-4 rounded-xl bg-gray-50 border-2 border-gray-200 text-center">
                <p className="text-sm text-gray-600 mb-2">No characters created yet</p>
                <Link href="/characters">
                  <Button variant="outline" size="sm" type="button">
                    <UserPlus className="h-4 w-4 mr-1" />
                    Create Your First Character
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-48 overflow-y-auto p-2 border-2 border-gray-200 rounded-lg">
                {characters.map((character) => {
                  const isSelected = selectedCharacterIds.includes(character.character_id || "")
                  const imageUrl = character.character_id
                    ? getCharacterImageUrl(character.character_id)
                    : null

                  return (
                    <div
                      key={character.character_id}
                      className={`relative cursor-pointer rounded-lg border-2 transition-all ${
                        isSelected
                          ? "border-[#6366f1] bg-purple-50"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                      onClick={() => {
                        if (character.character_id) {
                          toggleCharacter(character.character_id)
                        }
                      }}
                    >
                      <div className="aspect-square bg-gray-100 rounded-t-lg overflow-hidden">
                        {character.has_image && imageUrl ? (
                          <img
                            src={imageUrl}
                            alt={character.name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.currentTarget.style.display = "none"
                            }}
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <UserPlus className="h-8 w-8 text-gray-400" />
                          </div>
                        )}
                      </div>
                      <div className="p-2">
                        <p className="text-xs font-semibold truncate">{character.name}</p>
                        {character.species && (
                          <p className="text-xs text-gray-500 truncate">{character.species}</p>
                        )}
                      </div>
                      {isSelected && (
                        <div className="absolute top-1 right-1 w-4 h-4 bg-[#6366f1] rounded-full flex items-center justify-center">
                          <span className="text-white text-xs">✓</span>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
            {selectedCharacterIds.length > 0 && (
              <p className="text-xs text-gray-500">
                {selectedCharacterIds.length} character(s) selected
              </p>
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
