# Modbus register maps

Register mappings are defined **inside each driver** in `app/drivers/` (e.g. `deye.py`). This doc summarises what each driver uses and where the numbers come from so you can verify or extend them.

## Deye / Sunsynk (`app/drivers/deye.py`)

- **Live data**: **Input registers** (function code 0x04), **not** holding registers. The original placeholder used holding registers at 0x00–0x50, which do **not** contain the real monitoring data on Deye inverters.
- **Source**: [Sunsynk sensor definitions](https://kellerza.github.io/sunsynk/reference/definitions) (Deye and Sunsynk share the same protocol). Implemented set: **single-phase (1PH)** addresses.
- **Addresses used** (input registers):
  - PV: 109–112 (PV1/2 V, I × 0.1), 186–187 (PV1/2 power, signed)
  - Battery: 182–184, 190–191 (temp×0.1, V×0.01, SOC, power signed, I×0.01)
  - Grid: 79, 150, 169 (freq×0.01, V×0.1, power signed)
  - Load: 178 (power signed)
  - Inverter: 90, 91 (DC transformer / radiator temp × 0.1), 59 (overall state)
- **Three-phase**: The same docs define a 3PH column with different offsets (e.g. battery SOC 588, grid power 625/690). The driver can be extended with a “phase” or “model” option and a second address set.
- **Settings (read/write)**: Use **holding registers** per the Deye/Sunsynk protocol doc; addresses are model-specific (e.g. grid charge, export limit). Not yet fully implemented in the driver.

## Generic (`app/drivers/generic.py`)

- Placeholder map (holding registers 0–19) for unknown/test devices. Replace or configure offsets for your hardware.

## Adding or checking a map

1. **In-code**: Edit the driver file (e.g. `deye.py`): add or change the `DEYE_INPUT` dict and the `read_live_data()` parsing. Use input vs holding and signed/scale as in the official or community doc.
2. **References**:
   - Deye SUN Modbus manual (from Deye or distributor) – version (e.g. V118 single-phase, V104 three-phase) affects addresses.
   - [Sunsynk definitions](https://github.com/kellerza/sunsynk/blob/main/src/sunsynk/definitions) for a maintained community map.
   - Solar Assistant and other open projects often publish or derive maps from the same manuals.

## Will it actually get data?

- **Deye**: Yes, **if** you use **input registers** with the correct single-phase addresses (as in the updated `deye.py`). Connect via Modbus TCP (inverter LAN port) or RTU (USB/RS485 adapter), set correct slave ID (often 1), and the dashboard should show live PV, battery, grid, and load.
- **Generic**: Only if your device uses holding registers in the 0–19 range; otherwise add a proper driver with the right register type and addresses.
