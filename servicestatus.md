# edge-gps — Service Status

**Purpose:** Current development phase and maturity of the GNSS service.  
**Status:** Development / PAUSED  
**Last reviewed:** September 2026

## Current Phase

**GNSS Acquisition and Context Provider Foundation: FUNCTIONAL FOUNDATION / INTEGRATION INCOMPLETE**

The service has progressed beyond basic UART/NMEA acquisition. Parser, diagnostics, controller integration, UTC/time-context normalization, and GPS context-model foundations exist.

Development is currently paused while the platform advances evidence/video work.

## Verified Foundation

- GY-GPS6MV2 / u-blox NEO-6M UART acquisition
- NMEA checksum validation
- GGA/RMC/GSA/GSV parsing
- Normalized fix state
- Latitude/longitude/altitude
- Satellite and DOP diagnostics
- Controller node/service registration foundation
- UTC-canonical timestamp normalization
- IANA local-time conversion and UTC offset calculation
- Location/navigation separation
- GPS evidence-context model foundation

The RMC/GGA date handling correction prevents fabricated dates when only time-of-day is available.

## Integration State

A node-local GPS context service foundation exists, but lifecycle integration, health reporting, cross-Compose/node-local service networking, and consumer integration are not complete.

The service must therefore not be described as a completed platform-wide GPS context provider.

## Current Hardware Boundary

The tested GY-GPS6MV2 breakout does not expose a usable PPS/timepulse pin. UART/NMEA time must not be represented as equivalent to PPS precision.

## Next Development Phase

When resumed: complete context-server lifecycle integration, add/verify health reporting, establish the actual node-local service path, stabilize the shared GPS context contract, integrate consumers, and verify stale/unavailable context behavior.

PPS work follows the common context architecture rather than preceding it.
