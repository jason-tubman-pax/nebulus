# Architecture

## Overview

Pax Nebulus is a single-board or small-form-factor Linux device that runs a web application for solar/inverter monitoring and control. It targets **Victron Ekrano–like** behaviour (dashboard + settings on a local display) and **Solar Assistant–like** feature parity (many inverters, full settings, share link).

## Components

### 1. Backend (FastAPI)

- **REST API**: Settings (WiFi, inverter config, tunnel), CRUD for configuration.
- **WebSocket**: Single endpoint streaming real-time metrics (PV power, battery SoC, grid import/export, setpoints) so the dashboard updates without polling.
- **Modbus service**: Background task or thread that periodically reads/writes registers via the active inverter driver and pushes to an in-memory store (or queue) that the WebSocket reads from.
- **Driver registry**: One Python module per inverter family (e.g. `deye.py`, `sofar.py`). Each implements a common interface: `connect`, `read_live_data()`, `read_settings()`, `write_settings(...)`.

### 2. Modbus and hardware

- **RTU**: Serial port (USB–serial adapter or GPIO UART). Used for most hybrid inverters and battery BMS when connected by RS485/RS232.
- **TCP**: Ethernet connection to inverter or battery. Common for Deye, Sofar, Growatt, Luxpower, Solax.
- **Register maps**: Stored per driver (constants or JSON). Sources: manufacturer docs, Solar Assistant open-source references, community maps. Writes are validated (min/max, enum) before sending.

### 3. Frontend

- **Dashboard**: Single-page view with cards/gauges for PV, battery, grid, load; optional charts (e.g. last 24h from stored samples).
- **Settings**: Forms for WiFi (SSID, password, list of networks), inverter type and connection (port, slave ID, IP), and tunnel (enable/disable, copy share link).
- **Real-time**: WebSocket client that receives JSON and updates the UI (no full reload).

### 4. Public share link

- **Options**: Cloudflare Quick Tunnels (`cloudflared tunnel --url http://127.0.0.1:8000`), or localtunnel (`lt --port 8000`). Both give a public HTTPS URL.
- **Security**: Share link can be read-only (separate route that only serves dashboard, no settings) and/or protected by a random token in the path (e.g. `/share/abc123`).
- **Backend**: Settings API to “start tunnel” / “stop tunnel” and return the current share URL; optional systemd unit or subprocess to run `cloudflared`/`lt`.

### 5. Kiosk mode (HDMI, locked-down OS)

- **Display**: Chromium in kiosk mode (`--kiosk`, `--app=...`) or a minimal fullscreen browser, showing the dashboard URL (e.g. `http://localhost:8000` or `http://127.0.0.1:8000`).
- **Locked-down OS**: 
  - Auto-login, single user.
  - No window manager except what’s needed for fullscreen browser (or use a kiosk framework).
  - Disable sleep, screen blanking; optional reboot watchdog.
  - Settings only via web (no local desktop access).
- **Implementation**: Scripts and docs for Raspberry Pi OS / Debian (e.g. autostart Chromium, disable networking prompts).

## Data flow

1. **Modbus** → Driver reads registers at interval (e.g. 1–5 s) → Backend stores latest “live” snapshot.
2. **WebSocket** → Backend sends snapshot to all connected clients whenever it’s updated.
3. **Settings change** (e.g. inverter type) → API updates config → Backend reconnects Modbus with new driver/params.
4. **Share link** → User enables tunnel in settings → Backend starts cloudflared/lt → User copies URL; traffic hits same backend (or read-only subset).

## Security considerations

- **Local network**: Default bind to `0.0.0.0` so the device is reachable on LAN; no auth by default (device is assumed on trusted network).
- **Share link**: Optional tokenised path and/or read-only view; tunnel itself is unauthenticated unless we add a simple PIN.
- **WiFi credentials**: Stored in local config (e.g. encrypted or restricted file permissions); not exposed in API responses.
- **Modbus writes**: Validate all setpoints; rate-limit write requests to avoid inverter damage.

## Extensibility

- **New inverter**: Add a driver in `app/drivers/` implementing the common interface; register in a driver map by name; add UI option in “Inverter type” dropdown.
- **New metric**: Add register(s) in driver’s `read_live_data()`, extend Pydantic model and WebSocket payload, then add a card/chart in the frontend.
