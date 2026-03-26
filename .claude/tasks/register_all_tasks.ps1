# Register ALL portfolio automation tasks with Windows Task Scheduler
# Run once: powershell -ExecutionPolicy Bypass -File register_all_tasks.ps1

$claudePath = "$env:APPDATA\npm\claude.cmd"
$tasksDir   = "$env:USERPROFILE\.claude\tasks"

function Register-ClaudeTask {
    param($TaskName, $ScriptPath, $TriggerArgs, $Description)

    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    $action    = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""
    $settings  = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable -RunOnlyIfNetworkAvailable

    $trigger   = & $TriggerArgs

    Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Principal $principal -Action $action -Settings $settings -Description $Description -Force
    Write-Host "  Registered: $TaskName"
}

Write-Host ""
Write-Host "Registering Claude Portfolio Automation Tasks..."
Write-Host "------------------------------------------------"

# 1. Earnings Check — daily at 7:03 AM
Register-ClaudeTask `
    -TaskName "ClaudeEarningsCheck" `
    -ScriptPath "$tasksDir\run_earnings_check.ps1" `
    -TriggerArgs { New-ScheduledTaskTrigger -Daily -At "07:03" } `
    -Description "Daily earnings and macro events check — flags upcoming events for held tickers"

# 2. Risk Monitor — daily at 7:33 AM
Register-ClaudeTask `
    -TaskName "ClaudeRiskMonitor" `
    -ScriptPath "$tasksDir\run_risk_monitor.ps1" `
    -TriggerArgs { New-ScheduledTaskTrigger -Daily -At "07:33" } `
    -Description "Daily pre-market risk monitor — concentration, drawdown, 52-week alerts, thesis integrity"

# 3. Portfolio Daily Brief — daily at 8:47 AM
Register-ClaudeTask `
    -TaskName "ClaudePortfolioBrief" `
    -ScriptPath "$tasksDir\run_portfolio_brief.ps1" `
    -TriggerArgs { New-ScheduledTaskTrigger -Daily -At "08:47" } `
    -Description "Daily qualitative portfolio brief — macro, positions, connections, cash deployment"

# 4. Agent Economy Research Brief — weekly Monday at 6:33 AM
Register-ClaudeTask `
    -TaskName "ClaudeResearchBrief" `
    -ScriptPath "$tasksDir\run_research_brief.ps1" `
    -TriggerArgs { New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "06:33" } `
    -Description "Weekly agent economy research brief — new companies, thesis validators, watchlist update"

# 5. Weekly Review — every Sunday at 8:03 AM
Register-ClaudeTask `
    -TaskName "ClaudeWeeklyReview" `
    -ScriptPath "$tasksDir\run_weekly_review.ps1" `
    -TriggerArgs { New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "08:03" } `
    -Description "Weekly execution review — git activity scan, portfolio summary, drift check, one thing for next week"

# 6. News Song Briefing — daily at 7:57 AM
Register-ClaudeTask `
    -TaskName "ClaudeNewsSongBriefing" `
    -ScriptPath "$tasksDir\run_news_song_briefing.ps1" `
    -TriggerArgs { New-ScheduledTaskTrigger -Daily -At "07:57" } `
    -Description "Daily news song briefing — Perplexity headlines → Claude lyrics → Suno song → delivery"

Write-Host ""
Write-Host "All tasks registered. Daily schedule:"
Write-Host "  07:03  Earnings Check"
Write-Host "  07:33  Risk Monitor"
Write-Host "  07:57  News Song Briefing"
Write-Host "  08:47  Portfolio Brief"
Write-Host "  Monday 06:33  Research Brief (weekly)"
Write-Host "  Sunday 08:03  Weekly Review"
Write-Host ""
Write-Host "Briefs saved to: $env:USERPROFILE\.claude\tasks\portfolio_briefs\"
Write-Host ""
Write-Host "Quick access files (always latest):"
Write-Host "  earnings_latest.md"
Write-Host "  risk_latest.md"
Write-Host "  latest.md  (portfolio brief)"
Write-Host "  research_latest.md"
Write-Host ""
Write-Host "To run any task immediately:"
Write-Host "  Start-ScheduledTask -TaskName 'ClaudeEarningsCheck'"
Write-Host "  Start-ScheduledTask -TaskName 'ClaudeRiskMonitor'"
Write-Host "  Start-ScheduledTask -TaskName 'ClaudePortfolioBrief'"
Write-Host "  Start-ScheduledTask -TaskName 'ClaudeResearchBrief'"
