#!/usr/bin/env bash
#
# Pax Nebulus – one-command Raspberry Pi setup
# Run from repo root:  sudo ./setup.sh
# Optional:  sudo ./setup.sh --kiosk   to also configure HDMI kiosk mode
#
set -euo pipefail

# Re-exec as root if needed
if [[ "$(id -u)" -ne 0 ]]; then
  echo "This script must be run as root. Re-running with sudo..."
  exec sudo "$0" "$@"
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIOSK=false
for arg in "$@"; do
  [[ "$arg" == "--kiosk" ]] && KIOSK=true
done

RUN_USER="${SUDO_USER:-pi}"
USER_HOME="$(getent passwd "$RUN_USER" | cut -d: -f6)"
SERVICE_NAME="pax-nebulus"

echo "=============================================="
echo "  Pax Nebulus – Raspberry Pi setup"
echo "  Repo: $REPO_ROOT"
echo "  User: $RUN_USER"
echo "  Kiosk: $KIOSK"
echo "=============================================="

# --- System packages ---
echo "[1/7] Updating apt and installing system packages..."
apt-get update -qq
apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  curl \
  network-manager \
  || true

# Node.js 18+ for frontend build (Bookworm has 18; older Pi OS may need NodeSource)
NODE_VER=0
if command -v node &>/dev/null; then
  NODE_VER=$(node -v 2>/dev/null | sed 's/v//;s/\..*//' || echo "0")
fi
if [[ "${NODE_VER:-0}" -lt 18 ]]; then
  echo "Installing Node.js 20..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

# Chromium for kiosk (optional but install if kiosk requested)
if [[ "$KIOSK" == true ]]; then
  apt-get install -y chromium-browser || apt-get install -y chromium || true
fi

# --- Python venv and dependencies ---
echo "[2/7] Creating Python virtualenv and installing dependencies..."
cd "$REPO_ROOT"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# Ensure pip is up to date
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
chown -R "$RUN_USER:$RUN_USER" .venv

# --- Frontend build ---
echo "[3/7] Building frontend..."
cd "$REPO_ROOT/frontend"
if [[ -f package.json ]]; then
  npm install --silent
  npm run build
  chown -R "$RUN_USER:$RUN_USER" node_modules dist 2>/dev/null || true
else
  echo "  (No frontend/package.json found – skipping frontend build)"
fi
cd "$REPO_ROOT"

# --- Data directory ---
echo "[4/7] Creating data directory..."
mkdir -p "$REPO_ROOT/data"
chown "$RUN_USER:$RUN_USER" "$REPO_ROOT/data"

# --- Cloudflared (tunnel for share link) ---
echo "[5/7] Installing cloudflared..."
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)   ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  armv7l)   ARCH="arm" ;;
  *)        ARCH="arm64" ;; # default for Pi
esac
CLOUDFLARED_VERSION="2024.2.0"
CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-linux-${ARCH}"
if ! command -v cloudflared &>/dev/null; then
  curl -sL -o /usr/local/bin/cloudflared "$CLOUDFLARED_URL"
  chmod +x /usr/local/bin/cloudflared
  echo "  Installed cloudflared to /usr/local/bin/cloudflared"
else
  echo "  cloudflared already installed"
fi

# --- Systemd service ---
echo "[6/7] Installing systemd service..."
cat > /etc/systemd/system/"$SERVICE_NAME".service << EOF
[Unit]
Description=Pax Nebulus – solar dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$REPO_ROOT
Environment=PATH=$REPO_ROOT/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$REPO_ROOT/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"
echo "  Service enabled and started: $SERVICE_NAME"

# --- Optional: kiosk autostart ---
if [[ "$KIOSK" == true ]] && [[ -n "$USER_HOME" ]] && [[ -d "$USER_HOME" ]]; then
  echo "[7/7] Configuring kiosk autostart for $RUN_USER..."
  KIOSK_DIR="$USER_HOME/.config/autostart"
  mkdir -p "$KIOSK_DIR"
  cat > "$KIOSK_DIR/pax-nebulus-kiosk.desktop" << 'KIO'
[Desktop Entry]
Type=Application
Name=Pax Nebulus Kiosk
  Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble --app=http://127.0.0.1:8000
  Comment=Start Pax Nebulus dashboard in kiosk mode
KIO
  # Raspberry Pi OS may use 'chromium' instead of 'chromium-browser'
  if ! command -v chromium-browser &>/dev/null && command -v chromium &>/dev/null; then
    sed -i 's/chromium-browser/chromium/' "$KIOSK_DIR/pax-nebulus-kiosk.desktop"
  fi
  chown -R "$RUN_USER:$RUN_USER" "$USER_HOME/.config"
  echo "  Kiosk autostart installed. Enable auto-login to desktop and reboot to use."
else
  echo "[7/7] Skipping kiosk (use --kiosk to enable)."
fi

# --- Summary ---
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "=============================================="
echo "  Setup complete"
echo "=============================================="
echo ""
echo "  Dashboard:  http://${IP:-localhost}:8000"
echo "  Local:      http://127.0.0.1:8000"
echo ""
echo "  Service:    systemctl status $SERVICE_NAME"
echo "  Logs:       journalctl -u $SERVICE_NAME -f"
echo ""
if [[ "$KIOSK" == true ]]; then
  echo "  Kiosk:      Auto-login to desktop and reboot to show dashboard on HDMI."
  echo "              Or run: raspi-config → Boot → Desktop Autologin"
  echo ""
fi
echo "  Next:       Open the dashboard in a browser, go to Settings to"
echo "              configure inverter (Modbus TCP/RTU) and WiFi."
echo ""
