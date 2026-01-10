# PowerShell script to run Final Product Test
# This tests the complete storybook generation with authenticated Pollinations API

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STORY BOOKER - FINAL PRODUCT TEST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
$projectDir = "c:\Users\Guill\Desktop\SCRIPTING\Story_Booker\SB_0.0.1"
Set-Location $projectDir

Write-Host "Project Directory: $projectDir" -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting Final Product Test..." -ForegroundColor Yellow
Write-Host "This will generate a 2-page storybook with:" -ForegroundColor Yellow
Write-Host "  - AI-generated story (Groq)" -ForegroundColor Yellow
Write-Host "  - AI-generated images (Pollinations authenticated API - enter.pollinations.ai)" -ForegroundColor Yellow
Write-Host "  - Background removal & processing" -ForegroundColor Yellow
Write-Host "  - PDF compilation" -ForegroundColor Yellow
Write-Host ""
Write-Host "Estimated time: 3-5 minutes" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: POLLINATIONS_API_KEY is REQUIRED (free tier no longer supported)" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run the test
python test_final_product.py

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "TEST COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Check the 'output' folder for your generated PDF." -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "TEST FAILED!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
