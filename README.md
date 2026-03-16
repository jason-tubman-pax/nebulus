# Pax Nebulus

A Linux-based solar monitoring and control system that mimics Victron Ekrano functionality with **Solar Assistant–style feature parity**. Run a real-time dashboard on a headless device (web) or on HDMI with a locked-down kiosk OS.

## Features

- **Real-time dashboard** – Live inverter, battery, and solar data via Modbus (RTU over serial/USB or TCP over Ethernet)
- **Data persistence** – SQLite-backed history with configurable storage limits and rollover (delete oldest or keep last N days); UI shows disk available and lets you cap usage
- **Beautiful web UI** – Responsive dashboard and full settings; works headless or fullscreen on HDMI
- **Inverter support** – Same inverter set as Solar Assistant (Deye, Sofar, Growatt, Luxpower, Pylontech, BYD, etc.) via pluggable Modbus drivers
- **Full inverter settings** – Read/write setpoints, modes, schedules, and limits through the UI
- **WiFi & system settings** – Configure WiFi, hostname, and system options from the web interface
- **Public share link** – Expose the dashboard via a free tunnel (Cloudflare Quick Tunnels or localtunnel) so you can view it from anywhere
- **Kiosk mode** – Locked-down browser on HDMI for a dedicated display appliance

## Architecture

- **Backend**: FastAPI (Python) – REST API, WebSocket for live data, Modbus client abstraction
- **Frontend**: Modern SPA (Vite + React or Vue) – dashboard, charts, settings forms
- **Modbus**: pymodbus for RTU (serial) and TCP; one driver per inverter family with register maps
- **Tunneling**: `cloudflared` (trycloudflare.com) or `lt` (localtunnel) for share links
- **OS**: Debian/Ubuntu or Raspberry Pi OS; kiosk via Chromium in fullscreen or a minimal Wayland/X session

See [docs/architecture.md](docs/architecture.md) for details.

## Raspberry Pi: run on your local network

**Simplest way:** get the repo onto the Pi (clone or copy), then run one command:

```bash
cd pax-nebulus
sudo ./setup.sh
```

When it finishes, the dashboard is available at **http://\<your-pi-ip\>:8000** from any device on the same network (phone, laptop, etc.).

**Find the Pi’s IP** (on the Pi):
```bash
hostname -I | awk '{print $1}'
```
Or check your router’s “connected devices” list for the hostname (often `raspberrypi`).

**If you don’t have the repo on the Pi yet** – clone from your machine over SSH, or clone on the Pi if it has internet:
```bash
# On the Pi (replace with your repo URL):
git clone https://github.com/you/pax-nebulus.git
cd pax-nebulus
sudo ./setup.sh
```

**Optional – HDMI kiosk** (dashboard fullscreen on a connected monitor):
```bash
sudo ./setup.sh --kiosk
```
Then enable desktop auto-login in `raspi-config` and reboot.

---

## What the setup script does

The script will:

- Install Python 3, Node.js, Chromium (if `--kiosk`), NetworkManager, and cloudflared
- Create a venv and install Python dependencies
- Build the frontend and serve it from the backend
- Install and start the `pax-nebulus` systemd service
- With `--kiosk`: add Chromium to desktop autostart (enable “Desktop auto-login” in `raspi-config` and reboot to use)

When it finishes, open **http://\<your-pi-ip\>:8000** in a browser. Use **Settings** to configure the inverter (Modbus TCP or RTU) and WiFi.

## Quick start (development)

**Backend**
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
# API at http://localhost:8000
```

**Frontend** (from repo root)
```bash
cd frontend && npm install && npm run dev
# Dashboard at http://localhost:5173 (proxies /api to backend)
```

**Production (single device)**  
Build the frontend (`cd frontend && npm run build`), then serve `frontend/dist` with the same FastAPI app (uncomment the `StaticFiles` mount in `app/main.py`) or put the backend and frontend behind nginx.

## Project layout

```
pax-nebulus/
├── app/                    # FastAPI backend
│   ├── main.py
│   ├── api/                # Route modules
│   ├── core/               # Config, security
│   ├── services/           # Modbus, tunnel, wifi
│   ├── drivers/            # Inverter/battery Modbus drivers
│   └── models/             # Pydantic schemas
├── frontend/               # Dashboard SPA
├── docs/                   # Architecture, inverter register maps, kiosk setup
├── scripts/                # OS/kiosk/WiFi helpers
└── requirements.txt
```

## Supported inverters (target parity with Solar Assistant)

Drivers are implemented per manufacturer; register maps follow public Modbus docs and community maps where available.

| Manufacturer | Models (typical) | Interface |
|-------------|------------------|-----------|
| Deye        | SUN-xK-SG04LP3, etc. | Modbus RTU/TCP |
| Sofar       | HYD-xK-ET, etc.  | Modbus RTU/TCP |
| Growatt     | MIN/MOD series   | Modbus RTU/TCP |
| Luxpower    | SNA series       | Modbus RTU/TCP |
| Victron     | MultiPlus, etc.  | VE.Direct / Modbus |
| Pylontech   | US2000, etc.     | Modbus RTU (battery) |
| BYD         | Battery boxes    | Modbus RTU |
| Solax       | X1, Hybrid       | Modbus TCP |
| SolarEdge   | SE series        | Modbus TCP / API |
| …           | (extensible)     | Add drivers in `app/drivers/` |

## License

Proprietary / your choice.
