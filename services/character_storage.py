"""
Character Storage: Manages file system operations for storing character data.
Characters are stored as folders with JSON metadata and reference images.
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from src.models import Character


def ensure_characters_directory() -> Path:
    """
    Ensure the characters directory exists.
    
    Returns:
        Path object for the characters directory
    """
    characters_dir = Path("characters")
    characters_dir.mkdir(parents=True, exist_ok=True)
    return characters_dir


def sanitize_character_id(name: str) -> str:
    """
    Convert a character name to a valid folder name with chr_ prefix.
    
    Args:
        name: Character name
        
    Returns:
        Sanitized character ID (e.g., "chr_character_name")
    """
    # Remove special characters, keep alphanumeric, spaces, hyphens, underscores
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    # Replace spaces with underscores
    safe_name = safe_name.replace(' ', '_')
    # Remove multiple underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    # Add chr_ prefix if not already present
    if not safe_name.startswith('chr_'):
        safe_name = f"chr_{safe_name}"
    # Ensure it's not empty
    if not safe_name or safe_name == 'chr_':
        safe_name = 'chr_unnamed'
    return safe_name.lower()


def get_character_folder_path(character_id: str) -> Path:
    """
    Get the path for a character folder.
    
    Args:
        character_id: Character ID (with or without chr_ prefix)
        
    Returns:
        Path object for the character folder
    """
    characters_dir = ensure_characters_directory()
    # Ensure chr_ prefix
    if not character_id.startswith('chr_'):
        character_id = f"chr_{character_id}"
    return characters_dir / character_id


def character_exists(character_id: str) -> bool:
    """
    Check if a character folder exists.
    
    Args:
        character_id: Character ID
        
    Returns:
        True if character exists, False otherwise
    """
    folder_path = get_character_folder_path(character_id)
    return folder_path.exists() and (folder_path / "character.json").exists()


def load_character(character_id: str) -> Optional[Dict]:
    """
    Load character data from storage.
    
    Args:
        character_id: Character ID
        
    Returns:
        Character data dictionary, or None if not found
    """
    folder_path = get_character_folder_path(character_id)
    json_path = folder_path / "character.json"
    
    if not json_path.exists():
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError) as e:
        raise ValueError(f"Failed to load character {character_id}: {e}")


def save_character(character: Character, image_data: Optional[bytes] = None, tags: Optional[List[str]] = None) -> str:
    """
    Save character data and image to storage.
    
    Args:
        character: Character object to save
        image_data: Optional image bytes to save
        tags: Optional list of tags
        
    Returns:
        Character ID (folder name)
    """
    # Generate character ID from name
    character_id = sanitize_character_id(character.name)
    folder_path = get_character_folder_path(character_id)
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Prepare character metadata
    now = datetime.utcnow().isoformat() + "Z"
    
    # Check if character already exists to preserve created_at
    existing_data = load_character(character_id)
    created_at = existing_data.get("created_at", now) if existing_data else now
    
    character_data = {
        "name": character.name,
        "species": character.species,
        "physical_description": character.physical_description,
        "key_features": character.key_features,
        "color_palette": character.color_palette,
        "tags": tags or [],
        "created_at": created_at,
        "updated_at": now,
        "seed": character.seed,
        "refined_prompt": character.refined_prompt,
    }
    
    # Save JSON
    json_path = folder_path / "character.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(character_data, f, indent=2, ensure_ascii=False)
    
    # Save image if provided
    if image_data:
        image_path = folder_path / "image.png"
        with open(image_path, 'wb') as f:
            f.write(image_data)
    
    return character_id


def delete_character(character_id: str) -> bool:
    """
    Delete a character folder and all its contents.
    
    Args:
        character_id: Character ID
        
    Returns:
        True if deleted, False if not found
    """
    folder_path = get_character_folder_path(character_id)
    if not folder_path.exists():
        return False
    
    import shutil
    shutil.rmtree(folder_path)
    return True


def list_characters() -> List[Dict]:
    """
    List all characters in storage.
    
    Returns:
        List of character metadata dictionaries
    """
    characters_dir = ensure_characters_directory()
    if not characters_dir.exists():
        return []
    
    characters = []
    for folder_path in characters_dir.iterdir():
        if not folder_path.is_dir():
            continue
        if not folder_path.name.startswith('chr_'):
            continue
        
        json_path = folder_path / "character.json"
        if not json_path.exists():
            continue
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Add character_id for reference
            data['character_id'] = folder_path.name
            # Check if image exists
            image_path = folder_path / "image.png"
            data['has_image'] = image_path.exists()
            characters.append(data)
        except (json.JSONDecodeError, IOError):
            # Skip invalid characters
            continue
    
    # Sort by name
    characters.sort(key=lambda x: x.get('name', '').lower())
    return characters


def get_character_image_path(character_id: str) -> Optional[Path]:
    """
    Get the path to a character's image file.
    
    Args:
        character_id: Character ID
        
    Returns:
        Path to image file, or None if not found
    """
    folder_path = get_character_folder_path(character_id)
    image_path = folder_path / "image.png"
    if image_path.exists():
        return image_path
    return None


def character_to_dict(character: Character) -> Dict:
    """
    Convert a Character model to a dictionary for storage.
    
    Args:
        character: Character object
        
    Returns:
        Dictionary representation
    """
    return {
        "name": character.name,
        "species": character.species,
        "physical_description": character.physical_description,
        "key_features": character.key_features or [],
        "color_palette": character.color_palette,
        "seed": character.seed,
        "refined_prompt": character.refined_prompt,
    }


def dict_to_character(data: Dict) -> Character:
    """
    Convert a dictionary to a Character model.
    
    Args:
        data: Character data dictionary
        
    Returns:
        Character object
    """
    return Character(
        name=data.get("name", "Unknown"),
        species=data.get("species"),
        physical_description=data.get("physical_description", ""),
        key_features=data.get("key_features", []),
        color_palette=data.get("color_palette"),
        seed=data.get("seed"),
        refined_prompt=data.get("refined_prompt"),
    )
