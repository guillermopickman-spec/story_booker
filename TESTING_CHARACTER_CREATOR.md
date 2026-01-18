# Character Creator Feature - Manual Testing Guide

## Prerequisites

1. **Backend is running**: `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`
2. **Frontend is running**: `cd frontend && npm run dev` (should be on http://localhost:3000)
3. **API keys configured**: Ensure your `.env` has the necessary API keys for image generation

## Testing Checklist

### 1. Backend API Testing (Using curl or Postman)

#### Test 1.1: List Characters (Empty)
```bash
curl http://localhost:8000/characters
```
**Expected**: `{"characters": []}`

#### Test 1.2: Create Character (with AI image generation)
```bash
curl -X POST http://localhost:8000/characters \
  -F "name=Brave Mouse" \
  -F "species=mouse" \
  -F "physical_description=A small brown mouse with big round ears, bright black eyes, wearing a red cape with golden trim" \
  -F "key_features=big ears,red cape,golden trim" \
  -F "tags=adventure,hero,world_builder_1" \
  -F "generate_image=true"
```
**Expected**: Returns character metadata with `character_id`, `created_at`, `tags`, etc.

**Note**: This will take 30-60 seconds as it generates an image using AI.

#### Test 1.3: Create Character (with image upload)
First, save a test image, then:
```bash
curl -X POST http://localhost:8000/characters \
  -F "name=Princess Luna" \
  -F "species=human" \
  -F "physical_description=A young princess with long golden hair, blue eyes, wearing a silver tiara and purple dress" \
  -F "key_features=golden hair,silver tiara,purple dress" \
  -F "tags=fantasy,princess" \
  -F "image=@/path/to/your/image.png"
```
**Expected**: Returns character metadata. Image should be saved.

#### Test 1.4: List All Characters
```bash
curl http://localhost:8000/characters
```
**Expected**: Array with 2 characters (Brave Mouse and Princess Luna)

#### Test 1.5: Get Single Character
```bash
# Use the character_id from previous response (e.g., chr_brave_mouse)
curl http://localhost:8000/characters/chr_brave_mouse
```
**Expected**: Single character object with all metadata

#### Test 1.6: Get Character Image
```bash
curl http://localhost:8000/characters/chr_brave_mouse/image -o test_image.png
```
**Expected**: Downloads the character image file

#### Test 1.7: Update Character
```bash
curl -X PUT http://localhost:8000/characters/chr_brave_mouse \
  -F "physical_description=A small brown mouse with big round ears, bright black eyes, wearing a red cape with golden trim and a small sword" \
  -F "key_features=big ears,red cape,golden trim,small sword" \
  -F "tags=adventure,hero,world_builder_1,warrior"
```
**Expected**: Returns updated character with new `updated_at` timestamp

#### Test 1.8: Create Storybook with Characters
```bash
curl -X POST "http://localhost:8000/generate?theme=a%20brave%20mouse%20adventure&num_pages=3&character_ids=chr_brave_mouse&languages=en"
```
**Expected**: Returns `{"job_id": "..."}`. The storybook should use the stored character.

#### Test 1.9: Delete Character
```bash
curl -X DELETE http://localhost:8000/characters/chr_princess_luna
```
**Expected**: `{"message": "Character deleted successfully", "character_id": "chr_princess_luna"}`

#### Test 1.10: Verify Deletion
```bash
curl http://localhost:8000/characters/chr_princess_luna
```
**Expected**: 404 error

---

### 2. Frontend UI Testing

#### Test 2.1: Access Character Creator Page
1. Navigate to http://localhost:3000
2. Click the **"Characters"** button in the header
3. **Expected**: Should navigate to `/characters` page showing empty state or existing characters

#### Test 2.2: Create Character via UI (AI Generation)
1. Click **"New Character"** button
2. Fill in the form:
   - **Name**: "Brave Mouse"
   - **Species**: "mouse"
   - **Physical Description**: "A small brown mouse with big round ears, bright black eyes, wearing a red cape"
   - **Key Features**: "big ears, red cape, golden trim"
   - **Tags**: "adventure, hero"
3. Check **"Generate with AI"** checkbox
4. Click **"Create Character"**
5. **Expected**: 
   - Loading state appears
   - After 30-60 seconds, character is created
   - Redirects to character list
   - Character appears in gallery with generated image

#### Test 2.3: Create Character via UI (Image Upload)
1. Click **"New Character"** button
2. Fill in the form:
   - **Name**: "Princess Luna"
   - **Species**: "human"
   - **Physical Description**: "A young princess with long golden hair"
   - **Key Features**: "golden hair, silver tiara"
   - **Tags**: "fantasy, princess"
3. Click **"Upload Image"** and select an image file
4. Click **"Create Character"**
5. **Expected**: Character created with uploaded image

#### Test 2.4: View Character Gallery
1. On `/characters` page, verify:
   - Characters display in grid
   - Images are visible
   - Names and species are shown
   - Tags are displayed as badges
2. **Expected**: All created characters visible with correct information

#### Test 2.5: Search Characters
1. In the search box, type "mouse"
2. **Expected**: Only "Brave Mouse" appears
3. Clear search
4. **Expected**: All characters visible again

#### Test 2.6: Filter by Tags
1. Select a tag from the filter dropdown (e.g., "adventure")
2. **Expected**: Only characters with that tag are shown

#### Test 2.7: Edit Character
1. Click **"Edit"** on a character card
2. Modify the description or add a tag
3. Click **"Update Character"**
4. **Expected**: Character updated, redirected to list with changes visible

#### Test 2.8: Delete Character
1. Click **"Delete"** on a character card
2. Confirm deletion in the dialog
3. **Expected**: Character removed from list

#### Test 2.9: Character Selection in Storybook Generation
1. Navigate back to home page (`/`)
2. Scroll to the **"Select Characters"** section in the generation form
3. **Expected**: 
   - Character cards are displayed
   - Can click to select/deselect
   - Selected characters show checkmark
   - Counter shows "X character(s) selected"

#### Test 2.10: Generate Storybook with Selected Characters
1. Select one or more characters
2. Fill in storybook form:
   - **Theme**: "A brave mouse goes on an adventure"
   - **Pages**: 3
   - **Style**: 3D Rendered
   - **Languages**: English
3. Click **"Generate Storybook"**
4. **Expected**:
   - Job created successfully
   - Progress tracker shows character loading step
   - Storybook uses the selected characters
   - Characters appear consistently in generated images

#### Test 2.11: Navigate Between Pages
1. Test navigation:
   - Home → Characters (via header button)
   - Characters → Home (via "Back to Storybook" button)
   - Characters → Home (via "Manage Characters" link in form)
2. **Expected**: Smooth navigation, state preserved

---

### 3. File System Testing

#### Test 3.1: Verify Character Storage Structure
1. Check `characters/` directory:
```bash
ls characters/
```
**Expected**: Folders like `chr_brave_mouse/`, `chr_princess_luna/`

#### Test 3.2: Verify Character Folder Contents
```bash
ls characters/chr_brave_mouse/
```
**Expected**: 
- `character.json` (metadata file)
- `image.png` (reference image)

#### Test 3.3: Verify Character JSON Structure
```bash
cat characters/chr_brave_mouse/character.json
```
**Expected**: Valid JSON with:
- `name`, `species`, `physical_description`
- `key_features` (array)
- `color_palette` (object or null)
- `tags` (array)
- `created_at`, `updated_at` (ISO timestamps)
- `seed`, `refined_prompt` (if generated)

#### Test 3.4: Manual Character Creation
1. Create folder manually:
```bash
mkdir characters/chr_test_character
```
2. Create `character.json`:
```json
{
  "name": "Test Character",
  "species": "cat",
  "physical_description": "A fluffy orange cat",
  "key_features": ["fluffy", "orange"],
  "color_palette": null,
  "tags": ["test"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "seed": null,
  "refined_prompt": null
}
```
3. Add an image: `cp some_image.png characters/chr_test_character/image.png`
4. List characters via API
5. **Expected**: Manual character appears in list

---

### 4. Integration Testing

#### Test 4.1: Character Consistency in Storybook
1. Create a character with specific appearance
2. Generate a storybook with that character
3. Check generated images
4. **Expected**: Character appears consistently across all pages

#### Test 4.2: Multiple Characters in Storybook
1. Create 2-3 characters
2. Generate storybook selecting all of them
3. **Expected**: All selected characters appear in story, merged with any auto-extracted characters

#### Test 4.3: Character Priority (Stored vs Extracted)
1. Create character "Brave Mouse" in storage
2. Generate storybook with theme "a brave mouse adventure" and select the character
3. **Expected**: Stored character takes priority over auto-extracted one (no duplicates)

---

### 5. Error Handling Testing

#### Test 5.1: Invalid Character ID
```bash
curl http://localhost:8000/characters/invalid_id
```
**Expected**: 404 error

#### Test 5.2: Missing Required Fields
```bash
curl -X POST http://localhost:8000/characters \
  -F "name=Test" \
  -F "physical_description="
```
**Expected**: Validation error (400)

#### Test 5.3: Invalid Image File
1. Try uploading a non-image file
2. **Expected**: Error message or rejection

#### Test 5.4: Delete Non-existent Character
```bash
curl -X DELETE http://localhost:8000/characters/chr_nonexistent
```
**Expected**: 404 error

#### Test 5.5: Generate Storybook with Invalid Character ID
```bash
curl -X POST "http://localhost:8000/generate?character_ids=invalid_id"
```
**Expected**: 404 error for invalid character

---

### 6. Edge Cases

#### Test 6.1: Special Characters in Name
1. Create character with name: "O'Brien's Mouse"
2. **Expected**: Folder name sanitized (e.g., `chr_obriens_mouse`)

#### Test 6.2: Very Long Description
1. Create character with 1000+ character description
2. **Expected**: Character saved successfully

#### Test 6.3: Many Tags
1. Create character with 20+ tags
2. **Expected**: All tags saved and displayed

#### Test 6.4: Empty Tags Array
1. Create character without tags
2. **Expected**: Tags array is empty `[]`

#### Test 6.5: Character Without Image
1. Create character without uploading or generating image
2. **Expected**: Character saved, `has_image: false` in metadata

---

### 7. Performance Testing

#### Test 7.1: List Many Characters
1. Create 10+ characters
2. List all characters
3. **Expected**: All load quickly, gallery displays efficiently

#### Test 7.2: Search Performance
1. With 20+ characters, use search
2. **Expected**: Filtering is instant

---

## Quick Test Script

For a quick smoke test, run these in order:

```bash
# 1. Create character
curl -X POST http://localhost:8000/characters \
  -F "name=Test Mouse" \
  -F "species=mouse" \
  -F "physical_description=A small brown mouse" \
  -F "tags=test" \
  -F "generate_image=true"

# 2. List characters (get the character_id from response)
curl http://localhost:8000/characters

# 3. Get character (replace chr_test_mouse with actual ID)
curl http://localhost:8000/characters/chr_test_mouse

# 4. Generate storybook with character
curl -X POST "http://localhost:8000/generate?theme=test&num_pages=2&character_ids=chr_test_mouse&languages=en"

# 5. Check job status (use job_id from previous response)
curl http://localhost:8000/status/{job_id}
```

---

## Common Issues & Solutions

### Issue: Character image not generating
- **Check**: API keys in `.env` (POLLINATIONS_API_KEY or OPENAI_API_KEY)
- **Check**: Backend logs for errors
- **Solution**: Verify API keys are valid

### Issue: Characters not appearing in frontend
- **Check**: Backend is running on port 8000
- **Check**: Frontend API_BASE_URL in `frontend/lib/constants.ts`
- **Check**: Browser console for CORS errors
- **Solution**: Ensure backend CORS allows frontend origin

### Issue: Character folder not created
- **Check**: Write permissions on project directory
- **Check**: `characters/` directory exists
- **Solution**: Ensure directory exists and is writable

### Issue: Image upload fails
- **Check**: File size (should be reasonable, < 10MB)
- **Check**: File format (PNG, JPG, etc.)
- **Check**: Backend logs
- **Solution**: Try smaller image or different format

---

## Success Criteria

✅ All API endpoints return expected responses  
✅ Characters can be created, read, updated, deleted  
✅ Images can be uploaded or AI-generated  
✅ Characters appear in frontend gallery  
✅ Characters can be selected for storybook generation  
✅ Selected characters are used in generated storybooks  
✅ Character consistency maintained across story pages  
✅ Search and filter work correctly  
✅ Error handling works for invalid inputs  
✅ File system structure is correct  
