#!/usr/bin/env bash
# Mobile Terminal Setup — WSL2 Side
# Run this INSIDE WSL2 (Ubuntu)
#
# Usage (from WSL2 terminal):
#   bash ~/.claude/setup_mobile_wsl.sh
#
# Or via Windows PowerShell:
#   wsl bash ~/.claude/setup_mobile_wsl.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

step()  { echo -e "\n${CYAN}[>>] $1${NC}"; }
ok()    { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "  ${YELLOW}[!!]${NC} $1"; }
fail()  { echo -e "  ${RED}[XX]${NC} $1"; }

echo ""
echo "================================================"
echo "  Mobile Terminal Setup — WSL2"
echo "  mosh + tmux + tmux.conf (mobile-optimized)"
echo "================================================"
echo ""

# ── Step 1: Update & install ──────────────────────────────────────────────────
step "Installing mosh + tmux + openssh-server"
sudo apt-get update -qq
sudo apt-get install -y mosh tmux openssh-server locales
ok "Packages installed"

# ── Step 2: Fix locale (mosh needs UTF-8) ─────────────────────────────────────
step "Configuring locale (required for mosh)"
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
ok "Locale set to en_US.UTF-8"

# ── Step 3: SSH server ────────────────────────────────────────────────────────
step "Configuring SSH server"
sudo mkdir -p /run/sshd

# Configure sshd
sudo tee /etc/ssh/sshd_config.d/wsl_mobile.conf > /dev/null << 'EOF'
Port 22
PasswordAuthentication yes
PubkeyAuthentication yes
AllowAgentForwarding yes
AllowTcpForwarding yes
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
EOF

# Start SSH
sudo service ssh start 2>/dev/null || sudo /usr/sbin/sshd -D &
ok "SSH server running on port 22"

# ── Step 4: Mosh firewall ─────────────────────────────────────────────────────
step "Opening mosh ports (UDP 60000-61000)"
if command -v ufw &>/dev/null; then
    sudo ufw allow 60000:61000/udp 2>/dev/null && ok "ufw: mosh ports open" || warn "ufw rule failed (may already exist)"
else
    warn "ufw not installed — skipping (Windows Firewall handles this)"
fi

# ── Step 5: Tailscale in WSL2 (optional but recommended) ─────────────────────
step "Installing Tailscale in WSL2"
if command -v tailscale &>/dev/null; then
    ok "Tailscale already installed"
else
    curl -fsSL https://tailscale.com/install.sh | sh
    ok "Tailscale installed"
fi

# Check if systemd is available for tailscaled
if [[ "$(cat /proc/1/comm 2>/dev/null)" == "systemd" ]]; then
    sudo systemctl enable --now tailscaled 2>/dev/null && ok "tailscaled enabled via systemd"
else
    warn "systemd not running — start tailscale manually: sudo tailscaled &"
    warn "Then: sudo tailscale up"
fi

# ── Step 6: Auto-start services in .bashrc / .profile ────────────────────────
step "Adding SSH auto-start to .profile"
AUTOSTART_MARKER="# mobile-terminal-autostart"
if ! grep -q "$AUTOSTART_MARKER" ~/.profile 2>/dev/null; then
    cat >> ~/.profile << 'EOF'

# mobile-terminal-autostart
# Start SSH server if not running (needed for mosh)
if ! pgrep -x sshd > /dev/null 2>&1; then
    sudo service ssh start 2>/dev/null
fi
EOF
    ok ".profile updated with SSH auto-start"
else
    ok ".profile already has auto-start"
fi

# ── Step 7: SSH key setup helper ──────────────────────────────────────────────
step "Setting up SSH key auth (recommended over password)"
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
ok "~/.ssh/authorized_keys ready — paste your phone's public key here"
warn "In Blink Shell: Settings → Keys → + → copy the public key → paste into ~/.ssh/authorized_keys"

# ── Step 8: Write tmux.conf ───────────────────────────────────────────────────
step "Writing mobile-optimized tmux.conf"
cat > ~/.tmux.conf << 'TMUXEOF'
# ─────────────────────────────────────────────────────────────────────────────
# tmux.conf — Mobile Optimized
# Designed for Blink Shell on iPhone
# ─────────────────────────────────────────────────────────────────────────────

# ── Core ──────────────────────────────────────────────────────────────────────
set -g default-terminal "xterm-256color"
set -ga terminal-overrides ",xterm-256color:Tc"
set -g history-limit 50000
set -g base-index 1              # windows start at 1 (easier on phone keyboard)
setw -g pane-base-index 1
set -g renumber-windows on       # no gaps after closing a window
set -sg escape-time 0            # no delay for escape key (critical for vim)
set -g focus-events on

# ── Prefix ────────────────────────────────────────────────────────────────────
# Keep Ctrl+B (universal) — Blink Shell maps it reliably
set -g prefix C-b
bind C-b send-prefix

# ── Mouse / Touch support ─────────────────────────────────────────────────────
set -g mouse on   # touch scroll, tap to select pane

# ── Window / Pane splits ──────────────────────────────────────────────────────
# Intuitive splits: | for vertical, - for horizontal
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
bind c new-window -c "#{pane_current_path}"     # new window keeps current dir

# Quick pane navigation (no prefix needed after first)
bind -n M-Left  select-pane -L
bind -n M-Right select-pane -R
bind -n M-Up    select-pane -U
bind -n M-Down  select-pane -D

# Window switching without prefix
bind -n M-1 select-window -t 1
bind -n M-2 select-window -t 2
bind -n M-3 select-window -t 3
bind -n M-4 select-window -t 4

# Resize panes (hold prefix + arrow)
bind -r Left  resize-pane -L 5
bind -r Right resize-pane -R 5
bind -r Up    resize-pane -U 5
bind -r Down  resize-pane -D 5

# ── Copy mode ─────────────────────────────────────────────────────────────────
setw -g mode-keys vi
bind Enter copy-mode
bind -T copy-mode-vi v   send-keys -X begin-selection
bind -T copy-mode-vi y   send-keys -X copy-selection-and-cancel
bind -T copy-mode-vi Escape send-keys -X cancel

# ── Session management ────────────────────────────────────────────────────────
bind S choose-session      # list sessions
bind K confirm-before -p "Kill session #S? (y/n)" kill-session

# ── Reload config ─────────────────────────────────────────────────────────────
bind r source-file ~/.tmux.conf \; display-message "Config reloaded"

# ─────────────────────────────────────────────────────────────────────────────
# STATUS BAR — designed for phone screen width (~375px)
# ─────────────────────────────────────────────────────────────────────────────

set -g status on
set -g status-interval 5         # refresh every 5s
set -g status-position bottom
set -g status-justify left

# Colors (dark bg, readable on OLED)
set -g status-style "bg=#1a1b26 fg=#c0caf5"
set -g window-status-current-style "bg=#7aa2f7 fg=#1a1b26 bold"
set -g window-status-style "bg=#1a1b26 fg=#565f89"
set -g pane-border-style "fg=#3b4261"
set -g pane-active-border-style "fg=#7aa2f7"
set -g message-style "bg=#7aa2f7 fg=#1a1b26 bold"

# Status left: session name + window
set -g status-left-length 30
set -g status-left "#[bg=#7aa2f7,fg=#1a1b26,bold] #S #[bg=#1a1b26,fg=#7aa2f7] "

# Window list format
setw -g window-status-format         " #I:#W "
setw -g window-status-current-format " #I:#W "

# Status right: Tailscale IP + time
# Shows Tailscale IP if available, falls back to hostname
set -g status-right-length 60
set -g status-right "#[fg=#565f89]#(tailscale ip -4 2>/dev/null | head -1 || hostname -I | awk '{print $1}') #[fg=#3b4261]│#[fg=#c0caf5] %H:%M #[bg=#7aa2f7,fg=#1a1b26,bold] %d %b "

# ─────────────────────────────────────────────────────────────────────────────
# MOBILE SHORTCUTS (works with Blink Shell gestures)
# ─────────────────────────────────────────────────────────────────────────────

# Quick window close
bind x confirm-before -p "Kill pane? (y/n)" kill-pane

# Zoom current pane (full screen) — toggle
bind z resize-pane -Z

# Show current pane info
bind i display-message "Pane: #P | Window: #W | Session: #S | Host: #H"

TMUXEOF
ok "~/.tmux.conf written"

# ── Step 9: Print connection info ─────────────────────────────────────────────
step "Getting connection info"
WSL_IP=$(hostname -I | awk '{print $1}')
LINUX_USER=$(whoami)
TS_IP=$(tailscale ip -4 2>/dev/null || echo "<run: sudo tailscale up>")

echo ""
echo "================================================"
echo "  WSL2 Setup Complete"
echo "================================================"
echo ""
echo "  Linux user  : $LINUX_USER"
echo "  WSL2 IP     : $WSL_IP"
echo "  Tailscale IP: $TS_IP"
echo ""
echo "  ── Connect from Blink Shell ──────────────────"
echo "  mosh $LINUX_USER@$TS_IP -- tmux new -As main"
echo ""
echo "  ── Reconnect to existing session ────────────"
echo "  mosh $LINUX_USER@$TS_IP -- tmux attach -t main"
echo ""
echo "  ── SSH fallback ─────────────────────────────"
echo "  ssh $LINUX_USER@$TS_IP"
echo ""
echo "  ── Add to Blink Shell hosts ─────────────────"
echo "  Host: $TS_IP"
echo "  User: $LINUX_USER"
echo "  Mosh: ON"
echo "  Startup cmd: tmux new -As main"
echo ""
echo "  ── Next: authorize your phone ───────────────"
echo "  1. In Blink: Settings → Keys → + → copy public key"
echo "  2. Paste into: ~/.ssh/authorized_keys"
echo "  3. Then disable password auth for security:"
echo "     sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config.d/wsl_mobile.conf"
echo ""
