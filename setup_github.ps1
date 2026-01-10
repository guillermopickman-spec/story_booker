# PowerShell script to set up and push to GitHub
# Story Booker v0.1 - GitHub Setup

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STORY BOOKER - GITHUB SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$repoUrl = "https://github.com/guillermopickman-spec/story_booker_v0.1.git"
$projectDir = "c:\Users\Guill\Desktop\SCRIPTING\Story_Booker\SB_0.0.1"

Set-Location $projectDir

Write-Host "Project Directory: $projectDir" -ForegroundColor Green
Write-Host ""

# Check if git is initialized
if (Test-Path .git) {
    Write-Host "[INFO] Git repository already initialized" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] Initializing git repository..." -ForegroundColor Yellow
    git init
    Write-Host "[OK] Git repository initialized" -ForegroundColor Green
}

Write-Host ""
Write-Host "[INFO] Checking git status..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "[INFO] Adding all files..." -ForegroundColor Yellow
git add .

Write-Host ""
Write-Host "[INFO] Checking what will be committed..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ready to commit and push!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the files above" -ForegroundColor White
Write-Host "2. Commit with: git commit -m 'Initial commit: Story Booker v0.1 - AI-powered storybook generator'" -ForegroundColor White
Write-Host "3. Add remote: git remote add origin $repoUrl" -ForegroundColor White
Write-Host "4. Push to GitHub: git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "OR run this script with -AutoCommit flag to auto-commit and push" -ForegroundColor Cyan
Write-Host ""

if ($args -contains "-AutoCommit") {
    Write-Host "[AUTO] Committing changes..." -ForegroundColor Yellow
    git commit -m "Initial commit: Story Booker v0.1 - AI-powered storybook generator

- FastAPI backend for generating children's storybooks
- AI-generated stories with multi-provider LLM support (Groq, OpenAI, GPT4All)
- Sticker-style image generation with Pollinations.ai and OpenAI DALL-E
- Automatic background removal and auto-cropping
- Professional PDF output with grid-based layouts
- Real-time progress tracking and job management
- Comprehensive test suite with integration and unit tests
- Full documentation and configuration examples"

    Write-Host "[OK] Changes committed" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[AUTO] Adding remote repository..." -ForegroundColor Yellow
    $existingRemote = git remote get-url origin 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[INFO] Remote 'origin' already exists: $existingRemote" -ForegroundColor Yellow
        git remote set-url origin $repoUrl
        Write-Host "[OK] Remote URL updated" -ForegroundColor Green
    } else {
        git remote add origin $repoUrl
        Write-Host "[OK] Remote 'origin' added" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "[AUTO] Checking current branch..." -ForegroundColor Yellow
    $branch = git branch --show-current
    if (-not $branch) {
        Write-Host "[INFO] Creating 'main' branch..." -ForegroundColor Yellow
        git branch -M main
        $branch = "main"
    }
    Write-Host "[OK] Current branch: $branch" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "[AUTO] Pushing to GitHub..." -ForegroundColor Yellow
    git push -u origin $branch
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "[SUCCESS] Code pushed to GitHub!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Repository URL: $repoUrl" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "[ERROR] Failed to push to GitHub" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Possible reasons:" -ForegroundColor Yellow
        Write-Host "1. Authentication required - you may need to use GitHub CLI or SSH keys" -ForegroundColor White
        Write-Host "2. Repository doesn't exist or you don't have push access" -ForegroundColor White
        Write-Host "3. Network connectivity issues" -ForegroundColor White
        Write-Host ""
        Write-Host "Try:" -ForegroundColor Yellow
        Write-Host "  gh auth login  # If using GitHub CLI" -ForegroundColor White
        Write-Host "  Or configure SSH keys at: https://github.com/settings/keys" -ForegroundColor White
    }
}

Write-Host ""
