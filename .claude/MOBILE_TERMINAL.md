# Mobile Terminal — Setup & Daily Use Guide
**Stack: Tailscale + Mosh + tmux | Updated: 2026-03-23**

---

## How It Works

```
iPhone (Blink Shell)
      │
      │  Tailscale VPN  ← encrypted, no open ports, works on any network
      │
Windows PC
      └── WSL2 (Ubuntu)
              ├── tailscaled  ← gives WSL2 its own Tailscale IP
              ├── sshd        ← mosh uses SSH to handshake first
              ├── mosh-server ← takes over after handshake, handles mobile reconnect
              └── tmux        ← persistent session survives all disconnects
```

**Why not just SSH?**
SSH drops when you switch WiFi → cellular, or your phone screen locks.
Mosh survives all of that. tmux means your session keeps running even when you close Blink.

---

## First-Time Setup

### Step 1 — Windows (run once, as Administrator)
```powershell
# Open PowerShell as Administrator
cd C:\Users\atank\.claude
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_mobile_windows.ps1
```

### Step 2 — WSL2 (run once, inside WSL2)
```bash
# Open WSL2 terminal (search "Ubuntu" in Start menu)
bash ~/.claude/setup_mobile_wsl.sh
```

### Step 3 — Tailscale on your phone
- iOS: App Store → **Tailscale**
- Android: Play Store → **Tailscale**
- Sign in with the **same account** as your PC
- Both devices now share a private network (100.x.x.x range)

### Step 4 — Blink Shell on iPhone
- App Store → **Blink Shell** ($20 — worth every cent for this use case)
- Free alternative: **a-Shell** (limited mosh support)
- Android: **Termux** + `pkg install openssh mosh`

### Step 5 — Configure Blink Shell host
```
Settings → Hosts → +
  Alias:    home-pc
  Hostname: <your Tailscale IP shown by setup script>
  User:     <your WSL2 Linux username>
  Mosh:     ON
  Startup:  tmux new -As main
```

### Step 6 — Authorize your phone (key auth)
```
In Blink: Settings → Keys → + → copy the public key shown
In WSL2:  echo "PASTE_KEY_HERE" >> ~/.ssh/authorized_keys
```

---

## Daily Use

### Connect (first time or new session)
```bash
mosh user@100.x.x.x -- tmux new -As main
```
Or in Blink: just tap the saved host.

### Reconnect (session already running)
```bash
mosh user@100.x.x.x -- tmux attach -t main
```
Everything is exactly where you left it — Claude Code, running scripts, all of it.

### SSH fallback (if mosh has issues)
```bash
ssh user@100.x.x.x
tmux attach -t main
```

---

## tmux on Mobile — Key Reference

The prefix key is **Ctrl+B** (hold Ctrl, tap B, then tap the next key).
In Blink Shell, use the Ctrl key in the bottom bar.

| Action | Keys |
|--------|------|
| New window | `Ctrl+B` → `c` |
| Split vertical | `Ctrl+B` → `\|` |
| Split horizontal | `Ctrl+B` → `-` |
| Switch pane | `Alt+Arrow` |
| Switch window | `Alt+1` through `Alt+4` |
| Zoom pane (full screen) | `Ctrl+B` → `z` |
| List sessions | `Ctrl+B` → `S` |
| Reload config | `Ctrl+B` → `r` |
| Scroll up | `Ctrl+B` → `Enter` → then `PgUp` / finger scroll |
| Detach (leave session running) | `Ctrl+B` → `d` |
| Kill pane | `Ctrl+B` → `x` |
| Show info | `Ctrl+B` → `i` |

**Touch gestures in Blink:**
- Two-finger swipe left/right → switch windows
- Tap to position cursor
- Scroll to pan in copy mode

---

## Status Bar Reference

The bottom bar shows (left → right):
```
 main   1:claude  2:audit        100.64.x.x │ 14:32  23 Mar
 ^sess  ^windows                 ^tailscale IP  ^time   ^date
```

- **Session name** (blue pill, left) — the tmux session you're in
- **Windows** — numbered, current highlighted in blue
- **Tailscale IP** — always visible so you know your address
- **Time + date** — right side

---

## Troubleshooting

### "Connection refused" on mosh
```bash
# In WSL2 — check SSH is running
sudo service ssh status
sudo service ssh start

# Check mosh is installed
which mosh-server
```

### "SSH connection dropped" when switching networks
This is expected with plain SSH — it's why mosh exists.
With mosh running, switching networks is seamless.

### WSL2 IP changed (happens on every Windows restart)
The scheduled task auto-refreshes the port proxy on login.
If it fails, run manually:
```powershell
# In PowerShell (Admin)
cd C:\Users\atank\.claude
.\refresh_portproxy.ps1
```

### Tailscale not connecting
```bash
# In WSL2
sudo tailscale status
sudo tailscale up   # re-authenticate if needed
```

### tmux session lost
Sessions only die if WSL2 itself was shut down.
If WSL2 is running, your session is still there:
```bash
tmux ls             # list all sessions
tmux attach -t main # reattach
```

---

## Files

| File | Purpose |
|------|---------|
| `setup_mobile_windows.ps1` | Windows setup — firewall, port proxy, scheduled task |
| `setup_mobile_wsl.sh` | WSL2 setup — mosh, tmux, SSH, tmux.conf |
| `refresh_portproxy.ps1` | Auto-generated — refreshes WSL2 port proxy |
| `~/.tmux.conf` | (in WSL2) Mobile-optimized tmux config |
| `tailscale_ip.txt` | Your PC's Tailscale IP (written by setup) |
| `wsl_ip.txt` | Current WSL2 internal IP (auto-refreshed) |

---

## Security Notes

- Tailscale uses WireGuard — all traffic is encrypted end-to-end
- No ports exposed to the public internet — only reachable via Tailscale network
- After setup, disable password auth and use key-only:
  ```bash
  sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' \
      /etc/ssh/sshd_config.d/wsl_mobile.conf
  sudo service ssh restart
  ```
- If you lose your phone: `tailscale logout` on the phone via tailscale.com admin panel instantly revokes access
