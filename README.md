# edge-gps

Containerized GNSS service for the Edge platform. Initial target hardware is the GY-GPS6MV2 breakout using the u-blox NEO-6M receiver over UART.

## Scope

Version 0.1 provides:

- NMEA acquisition over UART
- NMEA checksum validation
- GGA/RMC/GSA/GSV parsing
- normalized fix state
- satellite count and DOP diagnostics
- controller node/service registration
- controller configuration retrieval foundation
- Docker deployment for Raspberry Pi/ARM64

PPS/timepulse is intentionally not enabled in this version. It will be added after UART acquisition is validated on the target Pi.

## Hardware

Connect the breakout according to the electrical characteristics of the specific board. For a Raspberry Pi UART connection, the logical signals are:

- GPS TX -> Pi RX
- GPS RX -> Pi TX
- GPS GND -> Pi GND
- GPS VCC -> appropriate supply for the specific breakout

Do not assume that every GY-GPS6MV2 clone has the same VCC circuitry. Verify the board before powering it from a Pi GPIO/header rail.

## Device

The default device is `/dev/serial0`. Confirm the target Pi's UART mapping before deployment:

```bash
ls -l /dev/serial0 /dev/ttyAMA* /dev/ttyS* 2>/dev/null
```

Also ensure the UART is enabled and that a login console is not consuming the port.

## Local test

Install dependencies and run the parser tests:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

Run against a real receiver:

```bash
GPS_CONFIG=./config/gps.yaml python3 -m app.main
```

## Controller integration

The service uses the generic Edge Controller node/service model. It uses:

- `EDGE_CONTROLLER_URL`
- `EDGE_NODE_ID` (defaults to the container hostname)
- `EDGE_SERVICE_ID` (defaults to `edge-gps`)
- `EDGE_SERVICE_NAME`
- `EDGE_SERVICE_VERSION`

The current edge-controller already exposes generic node/service registration and per-service configuration endpoints, so no GPS-specific database model or controller endpoint is required for this MVP.

## Current Limitations

- UART acquisition depends on correct Raspberry Pi serial configuration.
- The default UART device may differ by host.
- PPS/timepulse is not implemented.
- A common evidence-facing location/time envelope is not implemented here; the project-level evidence architecture owns that common model.

## Future Direction

Future work includes PPS/timepulse support, richer GNSS observation exposure, and integration of GNSS-derived timing/location information into the broader evidence workflow.
