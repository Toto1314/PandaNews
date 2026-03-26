# Start Kiriko Telegram bot
$env:TELEGRAM_BOT_TOKEN = (Get-Content "$HOME\.claude\settings.json" | ConvertFrom-Json).env.TELEGRAM_BOT_TOKEN
$env:TELEGRAM_CHAT_ID   = (Get-Content "$HOME\.claude\settings.json" | ConvertFrom-Json).env.TELEGRAM_CHAT_ID

Write-Host "[kiriko] Starting bot..." -ForegroundColor Cyan
python "$HOME\.claude\kiriko_bot.py"
