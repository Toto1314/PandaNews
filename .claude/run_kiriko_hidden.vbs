' Launches Kiriko bot hidden, inheriting full environment
' Reads Telegram creds from settings.json via PowerShell
Set WShell = CreateObject("WScript.Shell")
cmd = "powershell.exe -NoProfile -WindowStyle Hidden -Command """ & _
  "$s = Get-Content (Join-Path $env:USERPROFILE '.claude\settings.json') | ConvertFrom-Json;" & _
  "$psi = New-Object System.Diagnostics.ProcessStartInfo;" & _
  "$psi.FileName = 'python';" & _
  "$psi.Arguments = (Join-Path $env:USERPROFILE '.claude\kiriko_bot.py');" & _
  "$psi.UseShellExecute = $false;" & _
  "$psi.CreateNoWindow = $true;" & _
  "foreach ($k in [System.Environment]::GetEnvironmentVariables().Keys) { if (-not $psi.EnvironmentVariables.ContainsKey($k)) { $psi.EnvironmentVariables[$k] = [System.Environment]::GetEnvironmentVariable($k) } };" & _
  "$psi.EnvironmentVariables['TELEGRAM_BOT_TOKEN'] = $s.env.TELEGRAM_BOT_TOKEN;" & _
  "$psi.EnvironmentVariables['TELEGRAM_CHAT_ID'] = $s.env.TELEGRAM_CHAT_ID;" & _
  "[System.Diagnostics.Process]::Start($psi) | Out-Null" & _
  """"
WShell.Run cmd, 0, False
