"use client"

import { useState } from "react"
import { CharacterMetadata } from "@/lib/types"
import { getCharacterImageUrl } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Search, Edit, Trash2, UserPlus, Image as ImageIcon } from "lucide-react"

interface CharacterGalleryProps {
  characters: CharacterMetadata[]
  onEdit?: (character: CharacterMetadata) => void
  onDelete?: (characterId: string) => void
  onSelect?: (characterId: string) => void
  selectedIds?: string[]
  showActions?: boolean
  showSelection?: boolean
}

export function CharacterGallery({
  characters,
  onEdit,
  onDelete,
  onSelect,
  selectedIds = [],
  showActions = true,
  showSelection = false,
}: CharacterGalleryProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [tagFilter, setTagFilter] = useState<string>("")

  // Get all unique tags
  const allTags = Array.from(
    new Set(characters.flatMap((char) => char.tags || []))
  ).sort()

  // Filter characters
  const filteredCharacters = characters.filter((char) => {
    const matchesSearch =
      searchQuery === "" ||
      char.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      char.species?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      char.physical_description.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesTag = tagFilter === "" || (char.tags || []).includes(tagFilter)

    return matchesSearch && matchesTag
  })

  if (characters.length === 0) {
    return (
      <div className="text-center py-12">
        <UserPlus className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <p className="text-lg text-gray-600 mb-2">No characters yet</p>
        <p className="text-sm text-gray-500">Create your first character to get started</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 space-y-2">
          <Label htmlFor="search" className="text-base">
            Search Characters
          </Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              id="search"
              placeholder="Search by name, species, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 text-base"
            />
          </div>
        </div>
        {allTags.length > 0 && (
          <div className="sm:w-64 space-y-2">
            <Label htmlFor="tag-filter" className="text-base">
              Filter by Tag
            </Label>
            <select
              id="tag-filter"
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
              className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg text-base focus:outline-none focus:border-[#6366f1]"
            >
              <option value="">All Tags</option>
              {allTags.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Character Grid */}
      {filteredCharacters.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-lg text-gray-600">No characters match your search</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredCharacters.map((character) => {
            const isSelected = selectedIds.includes(character.character_id || "")
            const imageUrl = character.character_id
              ? getCharacterImageUrl(character.character_id)
              : null

            return (
              <Card
                key={character.character_id}
                className={`overflow-hidden transition-all hover:shadow-lg ${
                  isSelected ? "ring-2 ring-[#6366f1]" : ""
                }`}
              >
                <div className="relative aspect-square bg-gray-100">
                  {character.has_image && imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={character.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        // Fallback if image fails to load
                        e.currentTarget.style.display = "none"
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <ImageIcon className="h-12 w-12 text-gray-400" />
                    </div>
                  )}
                  {showSelection && (
                    <div className="absolute top-2 right-2">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {
                          if (onSelect && character.character_id) {
                            onSelect(character.character_id)
                          }
                        }}
                        className="w-5 h-5 rounded border-gray-300 text-[#6366f1] focus:ring-[#6366f1]"
                      />
                    </div>
                  )}
                </div>
                <CardContent className="p-4">
                  <h3 className="font-semibold text-lg mb-1">{character.name}</h3>
                  {character.species && (
                    <p className="text-sm text-gray-600 mb-2">{character.species}</p>
                  )}
                  {character.tags && character.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {character.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                      {character.tags.length > 3 && (
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                          +{character.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                  {showActions && (
                    <div className="flex gap-2 mt-3">
                      {onEdit && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onEdit(character)}
                          className="flex-1"
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          Edit
                        </Button>
                      )}
                      {onDelete && character.character_id && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onDelete(character.character_id!)}
                          className="flex-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          Delete
                        </Button>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
