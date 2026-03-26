# Run this once as Administrator to register Kiriko as a startup task
# Right-click PowerShell -> "Run as Administrator" -> paste this file path

$vbs    = "$env:USERPROFILE\.claude\run_kiriko_hidden.vbs"
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbs`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName   "KirikoBot" `
    -Action     $action `
    -Trigger    $trigger `
    -Settings   $settings `
    -RunLevel   Highest `
    -Force

Write-Host "KirikoBot task registered. It will auto-start on next login." -ForegroundColor Green
Write-Host "To start it now without rebooting, run:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName 'KirikoBot'" -ForegroundColor Cyan
