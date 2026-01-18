"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert } from "@/components/ui/alert"
import { CreateCharacterRequest } from "@/lib/types"
import { UserPlus, Upload, Sparkles, X } from "lucide-react"

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  species: z.string().optional(),
  physical_description: z.string().min(10, "Physical description must be at least 10 characters"),
  key_features: z.string().optional(), // Comma-separated
  tags: z.string().optional(), // Comma-separated
  generate_image: z.boolean(),
})

export type CharacterFormData = z.infer<typeof formSchema>

interface CharacterFormProps {
  onSubmit: (data: CreateCharacterRequest) => Promise<void>
  onCancel?: () => void
  initialData?: Partial<CharacterFormData>
  isLoading?: boolean
}

export function CharacterForm({ onSubmit, onCancel, initialData, isLoading = false }: CharacterFormProps) {
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CharacterFormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: initialData?.name || "",
      species: initialData?.species || "",
      physical_description: initialData?.physical_description || "",
      key_features: initialData?.key_features || "",
      tags: initialData?.tags || "",
      generate_image: initialData?.generate_image || false,
    },
  })

  const generateImage = watch("generate_image")

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type.startsWith("image/")) {
        setImageFile(file)
        const reader = new FileReader()
        reader.onloadend = () => {
          setImagePreview(reader.result as string)
        }
        reader.readAsDataURL(file)
        setValue("generate_image", false)
      } else {
        setError("Please select an image file")
      }
    }
  }

  const removeImage = () => {
    setImageFile(null)
    setImagePreview(null)
  }

  const onFormSubmit = async (data: CharacterFormData) => {
    setError(null)
    try {
      // Parse key_features
      const key_features = data.key_features
        ? data.key_features.split(",").map((f) => f.trim()).filter((f) => f.length > 0)
        : []

      // Parse tags
      const tags = data.tags
        ? data.tags.split(",").map((t) => t.trim()).filter((t) => t.length > 0)
        : []

      await onSubmit({
        name: data.name,
        species: data.species || undefined,
        physical_description: data.physical_description,
        key_features,
        tags,
        generate_image: data.generate_image && !imageFile,
        image: imageFile || undefined,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save character")
    }
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center gap-2">
          <UserPlus className="h-6 w-6 text-[#6366f1]" />
          <CardTitle className="text-3xl bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] bg-clip-text text-transparent">
            {initialData ? "Edit Character" : "Create Character"}
          </CardTitle>
        </div>
        <CardDescription className="text-base">
          {initialData ? "Update character details" : "Create a new character for your storybooks"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="error" className="mb-4">
            <p className="font-semibold">Error</p>
            <p>{error}</p>
          </Alert>
        )}

        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className="text-base">
              Character Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              placeholder="e.g., Brave Mouse, Princess Luna"
              className="text-base"
              {...register("name")}
            />
            {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
          </div>

          {/* Species */}
          <div className="space-y-2">
            <Label htmlFor="species" className="text-base">
              Species <span className="text-gray-400">(optional)</span>
            </Label>
            <Input
              id="species"
              placeholder="e.g., mouse, human, bear, rabbit"
              className="text-base"
              {...register("species")}
            />
          </div>

          {/* Physical Description */}
          <div className="space-y-2">
            <Label htmlFor="physical_description" className="text-base">
              Physical Description <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="physical_description"
              placeholder="Describe the character's appearance in detail: size, colors, features, clothing, etc."
              className="min-h-[120px] text-base"
              {...register("physical_description")}
            />
            {errors.physical_description && (
              <p className="text-sm text-red-600">{errors.physical_description.message}</p>
            )}
          </div>

          {/* Key Features */}
          <div className="space-y-2">
            <Label htmlFor="key_features" className="text-base">
              Key Features <span className="text-gray-400">(comma-separated, optional)</span>
            </Label>
            <Input
              id="key_features"
              placeholder="e.g., big ears, red cape, golden crown"
              className="text-base"
              {...register("key_features")}
            />
            <p className="text-xs text-gray-500">Separate multiple features with commas</p>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label htmlFor="tags" className="text-base">
              Tags <span className="text-gray-400">(comma-separated, optional)</span>
            </Label>
            <Input
              id="tags"
              placeholder="e.g., world_builder_1, adventure, hero"
              className="text-base"
              {...register("tags")}
            />
            <p className="text-xs text-gray-500">Separate multiple tags with commas</p>
          </div>

          {/* Image Upload or Generate */}
          <div className="space-y-4">
            <Label className="text-base">Character Image</Label>
            
            {imagePreview ? (
              <div className="relative">
                <img
                  src={imagePreview}
                  alt="Character preview"
                  className="w-full max-w-xs h-auto rounded-lg border-2 border-gray-200"
                />
                <button
                  type="button"
                  onClick={removeImage}
                  className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-4">
                  <Label htmlFor="image-upload" className="cursor-pointer">
                    <div className="flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-[#6366f1] transition-colors">
                      <Upload className="h-5 w-5" />
                      <span>Upload Image</span>
                    </div>
                    <input
                      id="image-upload"
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleImageChange}
                    />
                  </Label>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">or</span>
                  </div>
                  
                  <div
                    className={`flex items-center gap-2 px-4 py-2 border-2 rounded-lg transition-colors cursor-pointer ${
                      generateImage
                        ? "border-[#6366f1] bg-purple-50"
                        : "border-gray-300 hover:border-[#6366f1]"
                    }`}
                    onClick={() => {
                      if (!imageFile) {
                        setValue("generate_image", !generateImage)
                      }
                    }}
                  >
                    <input
                      id="generate-image"
                      type="checkbox"
                      className="hidden"
                      checked={generateImage}
                      onChange={(e) => {
                        if (!imageFile) {
                          setValue("generate_image", e.target.checked)
                        }
                      }}
                      disabled={!!imageFile}
                    />
                    <Sparkles className="h-5 w-5" />
                    <span>Generate with AI</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Buttons */}
          <div className="flex gap-4">
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                className="flex-1"
                disabled={isLoading}
              >
                Cancel
              </Button>
            )}
            <Button
              type="submit"
              size="lg"
              className="flex-1 text-lg h-12 bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] hover:from-[#5855eb] hover:to-[#7c3aed]"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Saving...
                </>
              ) : (
                <>
                  <UserPlus className="mr-2 h-5 w-5" />
                  {initialData ? "Update Character" : "Create Character"}
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
