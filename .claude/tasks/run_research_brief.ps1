# Weekly Agent Economy Research Brief — Auto Runner
$promptFile = "$env:USERPROFILE\.claude\tasks\agent_economy_research_brief.txt"
$outputDir  = "$env:USERPROFILE\.claude\tasks\portfolio_briefs"
$date       = Get-Date -Format "yyyy-MM-dd"
$outputFile = "$outputDir\research_$date.md"

if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir | Out-Null }

$prompt     = Get-Content -Path $promptFile -Raw
$claudePath = "$env:APPDATA\npm\claude.cmd"
$result     = & $claudePath --print -p $prompt 2>&1

$header = "# Agent Economy Research Brief — $date`n`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm')`n`n---`n`n"
$header + $result | Out-File -FilePath $outputFile -Encoding UTF8
$header + $result | Out-File -FilePath "$outputDir\research_latest.md" -Encoding UTF8

Write-Host "Research brief saved to: $outputFile"
