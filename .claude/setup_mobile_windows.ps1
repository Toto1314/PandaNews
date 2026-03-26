# Mobile Terminal Setup — Windows Side
# Run this in PowerShell as Administrator
# Sets up WSL2, firewall rules, and Tailscale port routing
#
# Usage:
#   Right-click PowerShell → Run as Administrator
#   cd C:\Users\atank\.claude
#   .\setup_mobile_windows.ps1

param(
    [switch]$SkipWSL,
    [switch]$SkipFirewall,
    [switch]$SkipPortProxy
)

$ErrorActionPreference = "Continue"

function Write-Step { param($msg) Write-Host "`n[>>] $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  [XX] $msg" -ForegroundColor Red }

Write-Host "`n================================================" -ForegroundColor Magenta
Write-Host "  Mobile Terminal Setup — Windows" -ForegroundColor Magenta
Write-Host "  Stack: Tailscale + WSL2 + Mosh + tmux" -ForegroundColor Magenta
Write-Host "================================================`n" -ForegroundColor Magenta

# ── Step 1: Check admin ───────────────────────────────────────────────────────
Write-Step "Checking administrator privileges"
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Fail "Must run as Administrator. Right-click PowerShell → Run as Administrator"
    exit 1
}
Write-OK "Running as Administrator"

# ── Step 2: WSL2 ─────────────────────────────────────────────────────────────
if (-not $SkipWSL) {
    Write-Step "Checking WSL2"

    $wslStatus = wsl --status 2>&1
    $hasUbuntu = wsl --list --quiet 2>&1 | Where-Object { $_ -match "Ubuntu" }

    if (-not $hasUbuntu) {
        Write-Warn "Ubuntu not found — installing WSL2 + Ubuntu"
        wsl --install -d Ubuntu
        Write-Warn "WSL2 install launched. After Ubuntu finishes setup, run this script again."
        Write-Warn "Create a Linux username when prompted, then rerun this script."
        exit 0
    }

    # Try to fix common WSL2 issues
    Write-Step "Repairing WSL2 user configuration if needed"
    $testResult = wsl -e whoami 2>&1
    if ($testResult -match "getpwuid|failed|error") {
        Write-Warn "WSL2 user issue detected — attempting repair"
        # Reset default user to root temporarily to fix passwd
        ubuntu config --default-user root 2>$null
        wsl -e bash -c "id ubuntu 2>/dev/null || adduser --disabled-password --gecos '' ubuntu" 2>&1
        # Restore
        $linuxUser = Read-Host "  Enter your WSL2 username (or press Enter for 'ubuntu')"
        if (-not $linuxUser) { $linuxUser = "ubuntu" }
        ubuntu config --default-user $linuxUser 2>$null
        Write-OK "WSL2 user configuration repaired for: $linuxUser"
    } else {
        Write-OK "WSL2 is working: $testResult"
    }

    # Get WSL2 IP
    $wslIP = wsl hostname -I 2>&1 | ForEach-Object { $_.Trim().Split(' ')[0] }
    if ($wslIP -match "^\d+\.\d+\.\d+\.\d+$") {
        Write-OK "WSL2 IP: $wslIP"
        $env:WSL_IP = $wslIP
        # Save for the bash setup script
        Set-Content -Path "$env:USERPROFILE\.claude\wsl_ip.txt" -Value $wslIP
    } else {
        Write-Warn "Could not get WSL2 IP yet — run this script again after WSL2 is running"
    }
}

# ── Step 3: Tailscale ─────────────────────────────────────────────────────────
Write-Step "Checking Tailscale"
$tailscaleInstalled = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $tailscaleInstalled) {
    Write-Warn "Tailscale not found"
    Write-Warn "Install from: https://tailscale.com/download/windows"
    Write-Warn "After installing, run: tailscale up"
    Write-Warn "Then run this script again"
} else {
    $tsStatus = tailscale status 2>&1
    if ($tsStatus -match "Logged out|not connected") {
        Write-Warn "Tailscale installed but not connected — run: tailscale up"
    } else {
        $tsIP = tailscale ip -4 2>&1
        Write-OK "Tailscale connected — your PC IP: $tsIP"
        Set-Content -Path "$env:USERPROFILE\.claude\tailscale_ip.txt" -Value $tsIP.Trim()
    }
}

# ── Step 4: Windows Firewall — Mosh UDP ports ─────────────────────────────────
if (-not $SkipFirewall) {
    Write-Step "Configuring Windows Firewall for Mosh (UDP 60000-61000)"

    $existingRule = Get-NetFirewallRule -DisplayName "Mosh Mobile Shell" -ErrorAction SilentlyContinue
    if ($existingRule) {
        Write-OK "Mosh firewall rule already exists"
    } else {
        New-NetFirewallRule `
            -DisplayName "Mosh Mobile Shell" `
            -Direction Inbound `
            -Protocol UDP `
            -LocalPort 60000-61000 `
            -Action Allow `
            -Profile Any | Out-Null
        Write-OK "Mosh firewall rule created (UDP 60000-61000)"
    }

    # SSH rule
    $sshRule = Get-NetFirewallRule -DisplayName "OpenSSH Mobile" -ErrorAction SilentlyContinue
    if (-not $sshRule) {
        New-NetFirewallRule `
            -DisplayName "OpenSSH Mobile" `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort 22 `
            -Action Allow `
            -Profile Any | Out-Null
        Write-OK "SSH firewall rule created (TCP 22)"
    } else {
        Write-OK "SSH firewall rule already exists"
    }
}

# ── Step 5: Port proxy Windows → WSL2 ────────────────────────────────────────
if (-not $SkipPortProxy) {
    Write-Step "Setting up port proxy (Windows → WSL2)"

    $wslIPFile = "$env:USERPROFILE\.claude\wsl_ip.txt"
    if (Test-Path $wslIPFile) {
        $wslIP = Get-Content $wslIPFile

        # Clear existing proxies on these ports
        netsh interface portproxy delete v4tov4 listenport=22    listenaddress=0.0.0.0 2>$null
        netsh interface portproxy delete v4tov4 listenport=60001 listenaddress=0.0.0.0 2>$null

        # Add fresh proxies
        netsh interface portproxy add v4tov4 listenport=22    listenaddress=0.0.0.0 connectport=22    connectaddress=$wslIP
        netsh interface portproxy add v4tov4 listenport=60001 listenaddress=0.0.0.0 connectport=60001 connectaddress=$wslIP
        Write-OK "Port proxy: Windows:22 → WSL2:22 ($wslIP)"
        Write-OK "Port proxy: Windows:60001 → WSL2:60001 ($wslIP)"
    } else {
        Write-Warn "WSL2 IP not available yet — skipping port proxy"
        Write-Warn "Run this script again once WSL2 is running"
    }
}

# ── Step 6: Auto-update port proxy on WSL2 restart ───────────────────────────
Write-Step "Creating scheduled task to refresh port proxy on login"

$taskName = "WSL2-PortProxy-Refresh"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if (-not $existingTask) {
    $scriptPath = "$env:USERPROFILE\.claude\refresh_portproxy.ps1"

    # Write the refresh script
    $refreshScript = @'
# Auto-refresh WSL2 port proxy (WSL2 IP changes on every restart)
Start-Sleep -Seconds 8   # wait for WSL2 to fully start
$ip = (wsl hostname -I).Trim().Split(' ')[0]
if ($ip -match "^\d+\.\d+\.\d+\.\d+$") {
    netsh interface portproxy delete v4tov4 listenport=22    listenaddress=0.0.0.0 2>$null
    netsh interface portproxy delete v4tov4 listenport=60001 listenaddress=0.0.0.0 2>$null
    netsh interface portproxy add v4tov4 listenport=22    listenaddress=0.0.0.0 connectport=22    connectaddress=$ip
    netsh interface portproxy add v4tov4 listenport=60001 listenaddress=0.0.0.0 connectport=60001 connectaddress=$ip
    Set-Content "$env:USERPROFILE\.claude\wsl_ip.txt" $ip
}
'@
    Set-Content -Path $scriptPath -Value $refreshScript

    $action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -File `"$scriptPath`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable $false

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -Force | Out-Null

    Write-OK "Scheduled task '$taskName' created — port proxy auto-refreshes at login"
} else {
    Write-OK "Scheduled task already exists"
}

# ── Step 7: Copy WSL2 setup script into WSL2 and run it ──────────────────────
Write-Step "Running WSL2 setup (mosh + tmux + tmux.conf)"

$wslSetupSrc = "$env:USERPROFILE\.claude\setup_mobile_wsl.sh"
if (Test-Path $wslSetupSrc) {
    # Copy to WSL2 home and execute
    $wslPath = wsl wslpath -u "$wslSetupSrc" 2>&1
    wsl bash "$wslPath"
    Write-OK "WSL2 setup script completed"
} else {
    Write-Warn "setup_mobile_wsl.sh not found at $wslSetupSrc"
    Write-Warn "Copy it to ~/.claude/ and re-run, or run it manually inside WSL2"
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "`n================================================" -ForegroundColor Magenta
Write-Host "  Setup Summary" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Magenta

$tsIP = if (Test-Path "$env:USERPROFILE\.claude\tailscale_ip.txt") {
    Get-Content "$env:USERPROFILE\.claude\tailscale_ip.txt"
} else { "<not connected yet>" }

$wslIP = if (Test-Path "$env:USERPROFILE\.claude\wsl_ip.txt") {
    Get-Content "$env:USERPROFILE\.claude\wsl_ip.txt"
} else { "<not available yet>" }

Write-Host ""
Write-Host "  Tailscale IP : $tsIP" -ForegroundColor White
Write-Host "  WSL2 IP      : $wslIP" -ForegroundColor White
Write-Host ""
Write-Host "  Connect from Blink Shell (iPhone):" -ForegroundColor White
Write-Host "  mosh <your-linux-user>@$tsIP -- tmux new -As main" -ForegroundColor Green
Write-Host ""
Write-Host "  Or SSH fallback:" -ForegroundColor White
Write-Host "  ssh <your-linux-user>@$tsIP" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Install Tailscale on your phone (tailscale.com/download)" -ForegroundColor Yellow
Write-Host "  2. Sign in with the same account on both devices" -ForegroundColor Yellow
Write-Host "  3. Install Blink Shell on iPhone (blink.sh) — supports mosh natively" -ForegroundColor Yellow
Write-Host "  4. Connect: mosh user@$tsIP -- tmux new -As main" -ForegroundColor Yellow
Write-Host ""
