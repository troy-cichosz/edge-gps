# edge-gps — Sprint Status

**Current sprint:** PAUSED — GPS context-provider integration  
**Status:** PAUSED  
**Development phase:** GPS foundation → node-local context integration

## Sprint Objective

Complete the transition from GNSS acquisition service to a reliable node-local GPS context provider for evidence-producing services.

## Completed

- UART/NMEA acquisition
- NMEA parsing and checksum validation
- GPS fix/diagnostic model
- UTC/timezone context normalization
- Location/navigation separation
- GPS evidence-context model foundation
- Controller registration/status foundation

## Remaining Work

- Wire context server into service lifecycle
- Add health endpoint
- Verify actual cross-Compose/node-local networking
- Finalize stable shared GPS context contract
- Integrate edge-video and edge-audio consumers
- Define stale/unavailable context handling
- Add live-receiver integration tests

## Deferred

- PPS/timepulse hardware
- GPS-backed system-clock discipline
- Formal timing authority policy
- Context authentication/access control
- Event/pub/sub delivery
- Additional GPS persistence

## Handoff

The service is intentionally paused. When resumed, continue from context-provider integration rather than reopening the completed UART/parser foundation unless new runtime evidence identifies a regression.
