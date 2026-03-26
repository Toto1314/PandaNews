@echo off
:: Kiriko bot launcher — called by Windows Task Scheduler at login
:: Reads credentials from settings.json and starts the bot silently

for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content '%USERPROFILE%\.claude\settings.json' | ConvertFrom-Json).env.TELEGRAM_BOT_TOKEN"') do set TELEGRAM_BOT_TOKEN=%%i
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Content '%USERPROFILE%\.claude\settings.json' | ConvertFrom-Json).env.TELEGRAM_CHAT_ID"') do set TELEGRAM_CHAT_ID=%%i

python "%USERPROFILE%\.claude\kiriko_bot.py"
