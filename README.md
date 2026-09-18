# edge-gps

Containerized GNSS service for the Edge platform. The initial target hardware is the GY-GPS6MV2 breakout using a u-blox NEO-6M receiver over UART.

## Current Status

The service has progressed beyond the original GNSS acquisition MVP. The current foundation includes GNSS parsing and diagnostics, controller registration, UTC-canonical time normalization, IANA local-time conversion, location/navigation separation, and a GPS evidence-context model foundation.

The service is currently **development / paused** while platform development advances the evidence/video workflow.

The GPS context-provider integration is not yet complete. A node-local context service foundation exists, but its lifecycle integration, health reporting, cross-Compose/node-local networking, stable shared contract, and consumer integration still require completion and verification.

## Scope

The current service foundation provides:

- NMEA acquisition over UART
- NMEA checksum validation
- GGA/RMC/GSA/GSV parsing
- normalized fix state
- latitude, longitude, and altitude
- satellite count and DOP diagnostics
- controller node/service registration foundation
- UTC-canonical timestamp normalization
- IANA local-time conversion and UTC offset calculation
- separation of location data from navigation/fix diagnostics
- GPS evidence-context model foundation
- Docker deployment for Raspberry Pi/ARM64

RMC/GGA date handling avoids fabricating a calendar date when only a time-of-day value is available.

PPS/timepulse is intentionally not enabled. UART/NMEA time must not be represented as equivalent to PPS precision.

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

The UART device mapping is host-specific and must be verified on each target node before deployment.

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

## Controller Integration

The service uses the generic Edge Controller node/service model. It uses:

- `EDGE_CONTROLLER_URL`
- `EDGE_NODE_ID` (defaults to the container hostname)
- `EDGE_SERVICE_ID` (defaults to `edge-gps`)
- `EDGE_SERVICE_NAME`
- `EDGE_SERVICE_VERSION`

The service does not require a GPS-specific controller database model or GPS-specific controller endpoint for its generic registration/configuration foundation.

Controller integration is part of the management plane. GPS-derived time and location context remains node-local to the producing service and is not dependent on the controller as a real-time timestamp broker.

## GPS Context

The service foundation separates GPS location/navigation information from time/context information so consumers can distinguish:

- receiver fix state from timing context;
- location from navigation diagnostics;
- UTC-canonical values from local-time presentation;
- GNSS time acquired over UART/NMEA from higher-precision timing sources such as PPS.

The intended context-provider architecture is node-local. Evidence-producing services should obtain GPS context through the hosting node's service path rather than requiring the central controller to broker real-time GPS data.

The current context-provider foundation is not yet a completed platform-wide integration. Lifecycle, health, networking, consumer integration, and stale/unavailable-context behavior remain to be verified.

## Current Limitations

- UART acquisition depends on correct Raspberry Pi serial configuration.
- The default UART device may differ by host.
- The tested GY-GPS6MV2 breakout does not provide a usable PPS/timepulse signal.
- UART/NMEA time is not equivalent to PPS precision.
- The node-local GPS context-provider lifecycle and health integration are incomplete.
- Cross-Compose/node-local service networking has not yet been fully verified.
- Consumer integration is not yet complete.
- Stale or unavailable GPS context behavior is not yet finalized and verified.
- The service does not currently provide platform-wide GPS context integration.

## Future Direction

When development resumes, work will continue from the existing context-provider foundation rather than reopening the completed UART/parser foundation unless new runtime evidence identifies a regression.

Planned work includes:

- completing context-server lifecycle integration
- adding and verifying health reporting
- establishing the actual node-local service path
- stabilizing the shared GPS context contract
- integrating evidence-producing consumers
- defining and verifying stale/unavailable context handling
- adding live-receiver integration tests
- PPS/timepulse support when suitable hardware is available
- GPS-backed system-clock discipline where architecturally appropriate

PPS/timepulse work follows the common context architecture rather than preceding it.
