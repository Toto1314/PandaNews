# Run this once to register the daily portfolio brief with Windows Task Scheduler
# Run as: powershell -ExecutionPolicy Bypass -File register_portfolio_task.ps1

$taskName   = "ClaudePortfolioBrief"
$scriptPath = "$env:USERPROFILE\.claude\tasks\run_portfolio_brief.ps1"
$triggerTime = "08:47"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create daily trigger at 8:47 AM
$trigger = New-ScheduledTaskTrigger -Daily -At $triggerTime

# Run as current user, only when logged on
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Action: run PowerShell with the script
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

# Settings: run even if on battery, don't stop if computer is idle
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Trigger $trigger `
    -Principal $principal `
    -Action $action `
    -Settings $settings `
    -Description "Daily qualitative portfolio brief via Claude Portfolio-Manager agent" `
    -Force

Write-Host ""
Write-Host "Task '$taskName' registered successfully."
Write-Host "Fires daily at $triggerTime — saves briefs to:"
Write-Host "  $env:USERPROFILE\.claude\tasks\portfolio_briefs\"
Write-Host ""
Write-Host "To run manually now:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "To view latest brief:"
Write-Host "  notepad `"$env:USERPROFILE\.claude\tasks\portfolio_briefs\latest.md`""
