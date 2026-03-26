# News Song Briefing — Daily Auto Runner
# Runs the full pipeline: Perplexity news → Claude lyrics → Suno song → delivery

$projectDir = "$env:USERPROFILE\news-song-briefing"
$pythonPath = "$env:USERPROFILE\anaconda3\python.exe"

# Fallback to system python if anaconda not found
if (-not (Test-Path $pythonPath)) {
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $pythonPath) {
    Write-Host "ERROR: Python not found. Check anaconda3 installation."
    exit 1
}

Write-Host "Running news-song-briefing pipeline..."
Set-Location $projectDir
& $pythonPath main.py --run-now

Write-Host "News song briefing complete."
