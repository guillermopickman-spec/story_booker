"use client"

import { useState, useEffect } from "react"
import { CharacterForm } from "@/components/CharacterForm"
import { CharacterGallery } from "@/components/CharacterGallery"
import { Button } from "@/components/ui/button"
import { Alert } from "@/components/ui/alert"
import {
  getCharacters,
  createCharacter,
  updateCharacter,
  deleteCharacter,
  CreateCharacterRequest,
} from "@/lib/api"
import { CharacterMetadata } from "@/lib/types"
import { UserPlus, BookOpen, ArrowLeft } from "lucide-react"
import Link from "next/link"

type ViewState = "list" | "create" | "edit"

export default function CharactersPage() {
  const [viewState, setViewState] = useState<ViewState>("list")
  const [characters, setCharacters] = useState<CharacterMetadata[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingCharacter, setEditingCharacter] = useState<CharacterMetadata | null>(null)

  const loadCharacters = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getCharacters()
      setCharacters(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load characters")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadCharacters()
  }, [])

  const handleCreate = () => {
    setEditingCharacter(null)
    setViewState("create")
  }

  const handleEdit = (character: CharacterMetadata) => {
    setEditingCharacter(character)
    setViewState("edit")
  }

  const handleDelete = async (characterId: string) => {
    if (!confirm("Are you sure you want to delete this character?")) {
      return
    }

    try {
      setIsLoading(true)
      setError(null)
      await deleteCharacter(characterId)
      await loadCharacters()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete character")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (data: CreateCharacterRequest) => {
    try {
      setIsLoading(true)
      setError(null)

      if (editingCharacter?.character_id) {
        // Update existing character
        await updateCharacter(editingCharacter.character_id, data)
      } else {
        // Create new character
        await createCharacter(data)
      }

      await loadCharacters()
      setViewState("list")
      setEditingCharacter(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save character")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = () => {
    setViewState("list")
    setEditingCharacter(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      {/* Header */}
      <header className="border-b-2 border-purple-200 bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] rounded-xl shadow-lg">
                <UserPlus className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] bg-clip-text text-transparent">
                  Character Creator
                </h1>
                <p className="text-xs text-gray-600">Create and manage your characters</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Storybook
                </Button>
              </Link>
              {viewState === "list" && (
                <Button
                  onClick={handleCreate}
                  className="bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] hover:from-[#5855eb] hover:to-[#7c3aed]"
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  New Character
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="space-y-8">
          {/* Error Alert */}
          {error && (
            <Alert variant="error" className="animate-fade-in">
              <p className="font-semibold">Error</p>
              <p>{error}</p>
            </Alert>
          )}

          {/* List View */}
          {viewState === "list" && (
            <div>
              <CharacterGallery
                characters={characters}
                onEdit={handleEdit}
                onDelete={handleDelete}
                showActions={true}
              />
            </div>
          )}

          {/* Create/Edit View */}
          {(viewState === "create" || viewState === "edit") && (
            <div className="flex flex-col items-center">
              <CharacterForm
                onSubmit={handleSubmit}
                onCancel={handleCancel}
                initialData={
                  editingCharacter
                    ? {
                        name: editingCharacter.name,
                        species: editingCharacter.species || "",
                        physical_description: editingCharacter.physical_description,
                        key_features: (editingCharacter.key_features || []).join(", "),
                        tags: (editingCharacter.tags || []).join(", "),
                        generate_image: false,
                      }
                    : undefined
                }
                isLoading={isLoading}
              />
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
