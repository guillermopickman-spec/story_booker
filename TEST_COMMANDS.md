# Story Booker - Test Commands

## Quick Test Commands

### PowerShell - Final Product Test (Recommended)
```powershell
cd c:\Users\Guill\Desktop\SCRIPTING\Story_Booker\SB_0.0.1
python test_final_product.py
```

### One-Line PowerShell Command
```powershell
cd c:\Users\Guill\Desktop\SCRIPTING\Story_Booker\SB_0.0.1; python test_final_product.py
```

### Quick Mock Test (No API Calls)
```powershell
cd c:\Users\Guill\Desktop\SCRIPTING\Story_Booker\SB_0.0.1
python tests\test_quick_demo.py
```

### Check Latest Generated PDF
```powershell
cd c:\Users\Guill\Desktop\SCRIPTING\Story_Booker\SB_0.0.1
Get-ChildItem -Path output -Filter *.pdf | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Format-List Name, FullName, Length, LastWriteTime
```

### Open Latest PDF
```powershell
cd c:\Users\Guill\Desktop\SCRIPTING\Story_Booker\SB_0.0.1
$latestPdf = Get-ChildItem -Path output -Filter *.pdf | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestPdf) {
    Write-Host "Opening: $($latestPdf.FullName)" -ForegroundColor Green
    Start-Process $latestPdf.FullName
} else {
    Write-Host "No PDF files found" -ForegroundColor Red
}
```

## Test Scripts Available

### Integration Tests

1. **`test_final_product.py`** - Main integration test with real APIs
   - Duration: ~3-5 minutes
   - Uses authenticated Pollinations API (enter.pollinations.ai)
   - Generates complete 2-page PDF storybook with images
   - Shows PDF filename at start and displays final results

2. **`tests/test_quick_demo.py`** - Quick mock test (no API calls)
   - Duration: ~4 seconds
   - Uses mock providers (no API calls)
   - Good for testing pipeline logic quickly

### Unit Tests (in `tests/` directory)

- `test_api.py` - API endpoint unit tests (FastAPI TestClient)
- `test_agents.py` - Author and Art Director agent tests
- `test_api_connection.py` - API connection diagnostic test
- `test_background_remover.py` - Background removal unit tests
- `test_image_service.py` - Image service unit tests
- `test_llm_client.py` - LLM client unit tests
- `test_pdf_generator.py` - PDF generator unit tests
- `test_sticker_generator.py` - Sticker generator tests (includes filename collision test)

## What Gets Tested

### Phase 1: API Foundation ✅
- FastAPI endpoints
- Job creation and tracking
- Status monitoring
- PDF download

### Phase 2: Narrative & Prompt Agents ✅
- Author Agent: Story generation
- Art Director Agent: Image prompt generation
- JSON-structured output validation

### Phase 3: Image Service & Sticker Factory ✅
- Authenticated Pollinations API (enter.pollinations.ai)
- Background removal
- Auto-cropping
- PNG with transparency

### Phase 4: PDF Layout Engine ✅
- Grid-based sticker layout
- Random rotation
- Header and footer
- Professional PDF generation

### Phase 5: Integration ✅
- Complete pipeline
- Progress tracking
- Error handling
- File management

## Expected Output

After running the test, you should see:
1. Progress updates (0-100%)
2. Status messages for each phase
3. Final PDF filename and location
4. PNG images generated count
5. Success confirmation

## PDF Export Location

All PDFs are saved to:
```
C:\Users\Guill\Desktop\SCRIPTING\Story_Booker\SB_0.0.1\output\{job_id}.pdf
```

Where `{job_id}` is a UUID generated for each job.

## Troubleshooting

### If test fails with "POLLINATIONS_API_KEY is required":
- Check your `.env` file has a valid API key
- Get API key at: https://enter.pollinations.ai
- Ensure API key is not a placeholder value

### If test fails with authentication error:
- Verify API key is valid
- Check API key format (should start with valid token)
- Ensure no extra spaces in `.env` file

### If images are not generating:
- Check API key quota/limits
- Verify network connectivity
- Check timeout settings (default 180s per image)

### To view generated files:
```powershell
# List all PDFs
Get-ChildItem -Path output -Filter *.pdf | Sort-Object LastWriteTime -Descending

# List images for a specific job
Get-ChildItem -Path "assets\{job_id}" -Filter *.png -Recurse
```
