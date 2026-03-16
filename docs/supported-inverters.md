# Supported inverters (Solar Assistant parity target)

Pax Nebulus uses pluggable Modbus drivers. The goal is **feature parity with Solar Assistant**: same inverter set and full read/write of settings.

## Implemented

| Driver   | Brand    | Connection | Status        |
|----------|----------|------------|---------------|
| `deye`   | Deye     | RTU / TCP  | Live + settings (partial) |
| `generic`| Generic  | RTU / TCP  | Live only (test/unknown devices) |

## To implement (same as Solar Assistant)

- **Sofar** – HYD, etc. (Modbus RTU/TCP)
- **Growatt** – MIN, MOD (Modbus RTU/TCP)
- **Luxpower** – SNA (Modbus TCP)
- **Victron** – MultiPlus, Quattro (VE.Direct or Modbus)
- **Pylontech** – US2000, etc. (BMS, Modbus RTU)
- **BYD** – Battery boxes (Modbus RTU)
- **Solax** – X1, Hybrid (Modbus TCP)
- **SolarEdge** – SE (Modbus TCP or Cloud API)
- **Huawei** – SUN2000 (Modbus TCP)
- **GoodWe** – ES, EM (Modbus)
- **Fronius** – Primo, Symo (Modbus)
- **Delta** – RPS (Modbus)

Register maps come from manufacturer manuals, Solar Assistant open references, and community projects (e.g. sunsynk-python, deye-inverter). Add a new file under `app/drivers/` implementing `BaseInverterDriver` and register it in `app/drivers/registry.py`.
