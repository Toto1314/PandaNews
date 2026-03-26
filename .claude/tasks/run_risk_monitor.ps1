# Daily Risk Monitor — Auto Runner
$promptFile = "$env:USERPROFILE\.claude\tasks\risk_monitor_brief.txt"
$outputDir  = "$env:USERPROFILE\.claude\tasks\portfolio_briefs"
$date       = Get-Date -Format "yyyy-MM-dd"
$outputFile = "$outputDir\risk_$date.md"

if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir | Out-Null }

$prompt     = Get-Content -Path $promptFile -Raw
$claudePath = "$env:APPDATA\npm\claude.cmd"
$result     = & $claudePath --print -p $prompt 2>&1

$header = "# Risk Monitor — $date`n`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm')`n`n---`n`n"
$header + $result | Out-File -FilePath $outputFile -Encoding UTF8
$header + $result | Out-File -FilePath "$outputDir\risk_latest.md" -Encoding UTF8

Write-Host "Risk monitor saved to: $outputFile"
