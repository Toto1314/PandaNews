# Daily Portfolio Brief — Auto Runner
# Runs via Windows Task Scheduler each morning

$promptFile = "$env:USERPROFILE\.claude\tasks\portfolio_daily_brief.txt"
$outputDir  = "$env:USERPROFILE\.claude\tasks\portfolio_briefs"
$date       = Get-Date -Format "yyyy-MM-dd"
$outputFile = "$outputDir\brief_$date.md"

# Ensure output directory exists
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Read prompt
$prompt = Get-Content -Path $promptFile -Raw

# Run Claude CLI in print mode (non-interactive, returns output)
$claudePath = "$env:APPDATA\npm\claude.cmd"

$result = & $claudePath --print -p $prompt 2>&1

# Save to dated file
$header = "# Portfolio Brief — $date`n`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm')`n`n---`n`n"
$header + $result | Out-File -FilePath $outputFile -Encoding UTF8

# Also write to a "latest" file for easy access
$header + $result | Out-File -FilePath "$outputDir\latest.md" -Encoding UTF8

Write-Host "Portfolio brief saved to: $outputFile"
