# Kiosk mode and locked-down OS

Run Pax Nebulus as a dedicated HDMI display: fullscreen dashboard, no desktop, minimal OS.

## Option 1: Raspberry Pi OS (Bullseye/Bookworm)

### Auto-start Chromium in kiosk mode

1. Install Raspberry Pi OS (headless or with desktop; we will only use the browser).
2. Install Chromium:
   ```bash
   sudo apt update && sudo apt install -y chromium-browser
   ```
3. Start the Pax Nebulus backend (systemd unit, see below).
4. Create autostart for Chromium (for the pi user with desktop):
   ```bash
   mkdir -p ~/.config/autostart
   cat > ~/.config/autostart/pax-kiosk.desktop << 'EOF'
   [Desktop Entry]
   Type=Application
   Name=Pax Nebulus Kiosk
   Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble --app=http://127.0.0.1:8000
   EOF
   ```
5. Reboot; the session should log in and launch Chromium in kiosk mode.

### Disable screen blanking

```bash
# Disable DPMS / screen blank
sudo raspi-config  # Interface Options → Screen blanking → No

# Or for X:
xset s off
xset -dpms
```

Add to autostart or a small script that runs after X starts.

### Optional: disable WiFi prompt

If you want the device to remember networks without prompting, configure WiFi via the web UI (Settings → WiFi) or `nmcli` before locking down.

---

## Option 2: Headless + HDMI via console framebuffer

If you prefer no X/Wayland, you can use a minimal browser in a framebuffer (e.g. **electron** or **Qt WebEngine** in kiosk mode) or a **digital signage** stack. Alternatively, keep a minimal X session only for Chromium as above.

---

## Systemd: run the backend

Create `/etc/systemd/system/pax-nebulus.service`:

```ini
[Unit]
Description=Pax Nebulus dashboard backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/pax-nebulus
Environment=PATH=/opt/pax-nebulus/.venv/bin:/usr/bin
ExecStart=/opt/pax-nebulus/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pax-nebulus
sudo systemctl start pax-nebulus
```

Adjust paths and user to match your install (e.g. `/opt/pax-nebulus` with a virtualenv).

---

## Locked-down OS checklist

- **Single user** with auto-login (Raspberry Pi: `sudo raspi-config` → System → Boot / Auto Login → Desktop).
- **No extra software** beyond browser, backend, and network tools.
- **Disable sleep/screen blank** (see above).
- **Optional**: read-only root filesystem (overlayfs) so reboots reset any local changes; persist only `data/` (config) on a writable partition.
- **Optional**: firewall so only LAN (and tunnel outbound) are used; no inbound from WAN except via Cloudflare tunnel if you enable it.
- **Settings only via web**: no need to expose a full desktop; users change WiFi and inverter config from another device or from the kiosk if you add a “Settings” entry point (e.g. long-press or PIN).

---

## Share link when in kiosk

1. On another device, open `http://<device-ip>:8000/settings`.
2. Generate a share token and start the tunnel (Cloudflare).
3. Copy the tunnel URL; append `/share/<token>` for the read-only dashboard.
4. The kiosk can keep showing the main dashboard; shared users see the same data via the public link.
