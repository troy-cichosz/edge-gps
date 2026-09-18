# edge-gps — ChatGPT Development Handoff

## Purpose

This document is the authoritative continuation point for future ChatGPT sessions working on the `edge-gps` service in the AI Legal Edge platform.

It is intended for ChatGPT/internal project continuity rather than general end-user documentation.

The repository is maintained through Azure DevOps and synchronized to the public GitHub repository:

* GitHub: `https://github.com/troy-cichosz/edge-gps`
* Active public branch: `public`
* Local Windows working directory: `D:\src\edge-gps`

The user commits working changes to ADO `master`, which subsequently updates/synchronizes the public GitHub repository. The user may also have local changes that are not yet pushed. When discrepancies exist:

1. Treat explicitly supplied local files/output as authoritative for the current working state.
2. Use the public GitHub repository to confirm the last committed/public state.
3. Do not assume the public repository contains the latest local changes until the user confirms synchronization.


---

# GitHub access
If there are issues using the API to pull from the public code base, always try to access any files via direct access/links for reference. 
GitHub public repos will ALWAYS be up to date on builds/commits. 

---

# 1. Project Role

`edge-gps` is a containerized GPS acquisition and context service for the AI Legal Edge platform.

Its initial hardware target is:

* Raspberry Pi 4
* GY-GPS6MV2 breakout
* u-blox NEO-6M GPS receiver
* UART/NMEA communication

The service is intended to provide:

* GPS acquisition
* normalized location/fix state
* satellite and DOP diagnostics
* GPS-derived UTC time
* local-time derivation
* node-local GPS context for other edge services
* future common timestamp/location authority for evidence-producing services

The service is not itself an evidence recorder. It supplies authoritative contextual information to services such as:

* `edge-audio`
* `edge-video`
* future sensor services
* future vehicle/edge capture services

The architecture remains local-first and evidence-first. GPS data should be available locally on the edge node without requiring every evidence event to make a controller request.

---

# 2. Current Hardware and Wiring

The tested GPS module is a GY-GPS6MV2 board using a u-blox NEO-6M receiver.

The particular breakout has four exposed pins:

* VCC
* GND
* TX
* RX

This board does not expose a usable PPS/timepulse pin. PPS should not be pursued with this exact breakout unless the hardware is replaced with a receiver/module exposing PPS.

Verified Raspberry Pi UART wiring:

```text
GPS TX  -> Raspberry Pi GPIO15 / physical pin 10 / UART RX
GPS RX  -> Raspberry Pi GPIO14 / physical pin 8  / UART TX
GPS GND -> Raspberry Pi GND
GPS VCC -> appropriate supply for the specific breakout
```

Do not assume every GY-GPS6MV2 clone has identical voltage regulation or protection circuitry.

---

# 3. UART Configuration

The UART was made usable by:

* disabling Bluetooth UART occupation with `dtoverlay=disable-bt`
* removing the serial login console entry:

  * `console=serial0,115200`

The service uses:

```text
/dev/serial0
```

The deployed containers pass the serial device through Docker:

```yaml
devices:
  - /dev/serial0:/dev/serial0
```

Both tested Raspberry Pi nodes have successfully received valid NMEA:

* `pi4SSD`
* `pi4nVME`

Earlier problems included missing `/dev/serial0`, missing expected `/dev/ttyAMA*` mappings, and serial-console conflicts. Those issues were resolved through UART configuration rather than application changes.

---

# 4. Verified Runtime Functionality

The following functionality is working:

## NMEA acquisition

The receiver continuously produces valid NMEA sentences over UART.

## Checksum validation

Valid checksums have been observed with no invalid checksum errors during extended runtime.

## Supported sentence families

The parser handles:

* GGA
* RMC
* GSA
* GSV

## Normalized GPS fix state

The service exposes normalized values including:

* fix validity
* fix quality
* latitude
* longitude
* altitude
* speed
* course
* satellites
* HDOP
* VDOP
* PDOP

## Diagnostics

The service tracks diagnostics such as:

* received message count
* valid checksum count
* invalid checksum count
* last sentence type
* satellites in view
* fix validity
* fix quality
* whether NMEA is actively arriving
* seconds since the last NMEA message

## Controller integration

The service successfully follows the generic controller node/service model used by the other edge services.

The controller integration includes:

* node registration
* service registration
* service status publication
* configuration retrieval foundation

No GPS-specific controller database model is required for the MVP because `edge-controller` already supports generic services attached to nodes.

---

# 5. Verified GPS Runtime Examples

A verified `pi4nVME` status sample included:

```text
GPS time:       2026-09-09T14:56:29+00:00
Fix valid:      true
Fix quality:    1
Latitude:       38.914947
Longitude:      -104.71621866666666
Altitude:       2065.7 m
Speed:          0.868 m/s
Satellites:     6
HDOP:           1.4
VDOP:           3.07
PDOP:           3.37
Receiver:       NEO-6M / NMEA
Raw GGA:        valid
Messages:       3658
Valid checksums:3658
Invalid:        0
Last sentence:  GGA
Satellites view:9
NMEA receiving: true
Seconds since NMEA: 0
```

A later `pi4SSD` GUI sample included:

```text
GPS time:       2026-09-09T16:05:06+00:00
Fix valid:      true
Satellites:     5
HDOP:           3.61
VDOP:           4.12
PDOP:           5.48
Latitude:       38.9150325
Longitude:      -104.716361
Altitude:       2020.5 m
Speed:          1.1142866666666664 m/s
Messages:       12795
Valid checksums:12795
Invalid:        0
Seconds since NMEA: approximately 0.047
```

The Pis are stationary on desks. The nonzero speed values are understood to be normal GPS position jitter, receiver noise, or incidental movement. Do not artificially filter, zero, or overwrite the raw speed value merely because the devices are stationary.

The common location context should not use speed/course. Speed and course belong in a separate navigation section.

---

# 6. Important GPS Date Bug and Resolution

Earlier implementation behavior could produce an incorrect date such as:

```text
2000-01-01
```

This occurred because GGA provides time-of-day but not the full calendar date.

The fix added date tracking from RMC and fallback handling:

* maintain `self.gps_date`
* allow `_utc_datetime()` to use a fallback date
* return `None` when no valid date is available rather than inventing a fake date
* GGA uses `fallback_date=self.gps_date`
* RMC updates `self.gps_date`

The corrected behavior was deployed and verified with current dates.

Do not reintroduce fake-date fallback behavior.

---

# 7. Timestamp Architecture

The timestamp model is now explicitly UTC-canonical.

Requirements:

* UTC is authoritative.
* Local time is derived.
* Timezone is represented using an IANA timezone name.
* UTC offset is explicitly included.
* GPS event time is distinct from host receipt/processing time.

The current timestamp representation is:

```json
{
  "utc": "2026-09-09T16:05:06+00:00",
  "local": "2026-09-09T10:05:06-06:00",
  "timezone": "America/Denver",
  "utc_offset": "-06:00"
}
```

The `TimestampContext` implementation is in:

```text
app/time_context.py
```

It:

* requires timezone-aware datetimes
* converts to UTC
* converts to the configured IANA timezone
* calculates the actual UTC offset
* serializes through `to_dict()`

The GPS service status timestamp data includes the conceptual distinction between:

* GPS time
* receipt time
* local derived time
* timezone
* UTC offset

Future evidence-producing services should use the common timestamp envelope:

```json
{
  "timestamp": {
    "utc": "2026-09-09T16:05:06+00:00",
    "local": "2026-09-09T10:05:06-06:00",
    "timezone": "America/Denver",
    "utc_offset": "-06:00"
  }
}
```

---

# 8. Evidence Context Model

The service now has the beginning of a reusable GPS/evidence context model.

Relevant files:

```text
app/evidence_context.py
app/context.py
```

The location model contains:

```text
latitude
longitude
altitude_m
quality
satellites
hdop
vdop
pdop
```

The GPS context model is conceptually:

```json
{
  "timestamp": {
    "utc": "...",
    "local": "...",
    "timezone": "America/Denver",
    "utc_offset": "-06:00"
  },
  "location": {
    "latitude": 38.9150325,
    "longitude": -104.716361,
    "altitude_m": 2020.5,
    "quality": 1,
    "satellites": 5,
    "hdop": 3.61,
    "vdop": 4.12,
    "pdop": 5.48
  },
  "navigation": {
    "speed_mps": 1.1142866666666664,
    "course_deg": null
  },
  "receiver": {
    "model": "NEO-6M",
    "protocol": "NMEA"
  }
}
```

Important separation:

## Location

Location context includes:

* latitude
* longitude
* altitude
* fix quality
* satellite count
* DOP values

## Navigation

Navigation includes:

* speed
* course

Speed/course must not be inserted into the common static location context.

---

# 9. Current Local Code State

The local working tree contains:

```text
app/__init__.py
app/config.py
app/context.py
app/context_server.py
app/controller.py
app/evidence_context.py
app/main.py
app/models.py
app/nmea.py
app/time_context.py
config/gps.yaml
tests/test_evidence_context.py
tests/test_nmea.py
tests/test_time_context.py
```

The local code has advanced beyond the currently published README.

The public GitHub repository should be checked after the user's ADO commit to confirm synchronization.

---

# 10. Critical Local Code Correction Before Commit

At the latest review point, local `app/main.py` contained an initialization bug:

```python
self.last_state = None
self.last_gps_context = build_gps_context(
    state,
    self.config.timezone,
)
```

`state` is undefined during service initialization.

The correct initialization is:

```python
self.last_state = None
self.last_gps_context = None
self.last_valid_state = None
```

Then, after a state is received in the runtime loop:

```python
if state is not None:
    self.last_state = state
```

the service should build the context:

```python
self.last_gps_context = build_gps_context(
    state,
    self.config.timezone,
)
```

The context must only be built after an actual parsed state exists.

---

# 11. Critical Local Context Correction

The local `app/context.py` had been using attributes that do not exist on the actual `GPSState` model:

Incorrect:

```python
receiver={
    "model": state.receiver_model,
    "protocol": state.protocol,
}
```

The actual model stores receiver information as a dictionary.

Correct approach:

```python
receiver=state.receiver.copy()
```

This preserves the receiver metadata already present in the state model and avoids inventing nonexistent model attributes.

---

# 12. Context Server

A node-local HTTP context server has been created in:

```text
app/context_server.py
```

Current behavior:

* exposes `GET /context`
* returns `503` with JSON when GPS context is not yet available
* returns serialized GPS context when available
* uses a background thread
* suppresses standard HTTP request logging

Current unavailable response:

```json
{
  "status": "unavailable",
  "reason": "no_gps_context"
}
```

Current context response is the serialized `GPSContext`.

The context server is not yet fully wired into `main.py` at the latest checkpoint.

The next implementation step is to integrate it into the GPS service lifecycle:

* initialize server
* start server after service initialization
* stop server during shutdown
* update `last_gps_context` as GPS state arrives

A `/health` endpoint should be added alongside `/context`.

---

# 13. Network Architecture Warning

Do not assume that separate Docker Compose projects can resolve one another by service name.

`edge-audio` currently uses a separate Compose service definition with:

```yaml
container_name: edge-audio
uts: host
```

and no shared external Docker network in its public Compose file.

The `edge-gps` Compose file also currently has no explicit shared network and no published HTTP port.

Therefore, before deciding how `edge-audio` or `edge-video` will consume GPS context, inspect the actual deployment topology.

Possible future approaches:

1. Shared external Docker network.
2. Host-published GPS context port.
3. Host networking.
4. A controller-mediated discovery/configuration mechanism.
5. A node-local gateway/sidecar.
6. Shared local files or socket-based access.

Do not blindly use:

```text
http://edge-gps:8090/context
```

unless the services are confirmed to share a Docker network where that name resolves.

The preferred architecture remains node-local access with no controller round-trip for every evidence event.

---

# 14. Docker/Deployment State

Current Compose characteristics:

* service name: `edge-gps`
* image is injected through the ADO variable:

  * `$(edge-gps_TAG)`
* restart policy:

  * `unless-stopped`
* host UTS namespace:

  * `uts: host`
* serial device:

  * `/dev/serial0`
* configuration mounted read-only
* logs mounted under:

  * `../logs/edge-gps:/logs`
* metadata mounted under:

  * `../metadata:/metadata`

Current environment variables include:

```text
GPS_CONFIG
GPS_DEVICE
GPS_BAUDRATE
GPS_LOG_LEVEL
EDGE_CONTROLLER_URL
EDGE_CONTROLLER_TIMEOUT
EDGE_NODE_ID
EDGE_SERVICE_ID
EDGE_SERVICE_NAME
EDGE_SERVICE_VERSION
```

The service is ARM64/Raspberry Pi oriented and uses Python 3.12 slim.

Dockerfile structure:

```text
python:3.12-slim
WORKDIR /app
install requirements
copy app
copy config
run python -u -m app.main
```

---

# 15. Relationship to Other Services

## edge-controller

`edge-controller` provides the generic control-plane API for:

* node registration
* service registration
* service configuration
* service status

The GPS service should remain generic and should not require GPS-specific controller database tables for normal operation.

## edge-audio

The public `edge-audio` Compose design confirms the broader service pattern:

* containerized service
* generic controller integration
* local recording/metadata paths
* no assumption that the controller stores every evidence payload

GPS context should eventually be consumable by audio without making the controller part of the real-time evidence path.

## edge-video

The current `edge-video` design is explicitly evidence-first:

* local segmented evidence
* hashes/manifests
* system timestamps currently marked unsynchronized
* future GPS/PPS integration
* optional network streaming separate from evidence capture

GPS integration should enrich video evidence metadata without modifying the fundamental local evidence spool architecture.

The current video README states that GPS/PPS will extend the common timestamp envelope without requiring changes to the video payload.

---

# 16. Current Tests

The repository includes:

```text
tests/test_nmea.py
tests/test_time_context.py
tests/test_evidence_context.py
```

The expected validation commands from the Windows development directory are:

```powershell
pytest -q
```

```powershell
python -c "from app.main import GPSService; print('GPSService import OK')"
```

```powershell
python -c "from app.context import build_gps_context; print('GPS context import OK')"
```

These should be run after the initialization and receiver-context corrections.

---

# 17. What Is Working

The following should be considered working and verified:

* Raspberry Pi UART communication
* GY-GPS6MV2/NEO-6M NMEA acquisition
* valid NMEA checksum processing
* GGA/RMC/GSA/GSV parsing
* normalized GPS fix state
* valid latitude/longitude acquisition
* altitude acquisition
* satellite and DOP diagnostics
* controller node/service registration
* controller status updates
* controller configuration foundation
* Docker deployment structure
* correct current GPS calendar dates after the RMC/GGA date fix
* UTC timestamp normalization
* IANA local timezone conversion
* explicit UTC offset calculation
* evidence-context data model foundation
* separation of location and navigation fields
* node-local context server implementation exists
* local test suite structure exists

---

# 18. What Is Not Yet Complete

The following are not yet complete production features:

* context server lifecycle wiring in `main.py`
* `/health` endpoint
* confirmed cross-Compose network path for sibling services
* consumer integration from `edge-audio`
* consumer integration from `edge-video`
* common context discovery/configuration through controller
* PPS support
* hardware with exposed PPS/timepulse
* GPS-backed system clock discipline
* evidence timestamp authority policy
* stale-context handling policy for consumers
* context freshness/age metadata
* context authentication or local access control
* event stream/pub-sub delivery
* GPS context persistence
* formal service API contract shared across all edge services
* integration tests against a live GPS receiver
* production-grade failover behavior when GPS becomes unavailable

---

# 19. Immediate Next Steps

After the user commits the current working state:

## Step 1 — Confirm repository synchronization

Verify that:

* ADO `master` contains the intended changes.
* GitHub `public` contains the same changes.
* The public README is updated separately from this internal `chatgpt.md`.

## Step 2 — Validate local code

Run:

```powershell
cd D:\src\edge-gps
pytest -q
python -c "from app.main import GPSService; print('GPSService import OK')"
python -c "from app.context import build_gps_context; print('GPS context import OK')"
```

## Step 3 — Wire `GPSContextServer`

Modify `main.py` to:

* initialize `last_gps_context` to `None`
* create the context server
* start it during service startup
* stop it during shutdown
* update the context after each parsed state

## Step 4 — Add `/health`

The endpoint should report:

* service alive
* GPS data availability
* last NMEA receipt age
* fix validity
* context availability
* service version

It should not claim GPS validity merely because the HTTP process is alive.

## Step 5 — Decide actual service-to-service networking

Inspect the real deployment topology of:

* `edge-gps`
* `edge-audio`
* `edge-video`

Determine whether the services are:

* in one Compose project
* in separate Compose projects
* on a shared external Docker network
* using host-published ports
* deployed independently through ADO pipelines

Only then select the context URL/discovery mechanism.

## Step 6 — Define the stable context contract

The contract should include:

```json
{
  "timestamp": {},
  "location": {},
  "navigation": {},
  "receiver": {}
}
```

Likely future additions:

```json
{
  "context_age_ms": 42,
  "received_at": {},
  "fix_valid": true,
  "source": {
    "node_id": "...",
    "service_id": "edge-gps"
  }
}
```

Do not add fields casually. The contract will be shared by audio, video, and future sensors.

## Step 7 — Integrate with edge-video first or edge-audio first

The next consumer should:

* retrieve GPS context locally
* include GPS context in newly created evidence metadata
* preserve the original evidence payload
* record whether GPS context was available
* distinguish GPS time from local receipt time
* tolerate unavailable/stale GPS context

## Step 8 — Add PPS only with appropriate hardware

The current GY-GPS6MV2 module has no exposed PPS pin. PPS requires:

* a GPS receiver/module exposing PPS
* a selected Pi GPIO
* kernel/device configuration
* timestamp validation
* eventually chrony or equivalent clock discipline if desired

Do not treat UART NMEA time as equivalent to PPS precision.

---

# 20. Architectural Constraints

Do not violate these constraints:

* Keep the service containerized.
* Keep local-first operation.
* Do not make the controller a real-time evidence dependency.
* Do not hardcode a single consumer such as edge-audio.
* Do not hardcode node hostnames.
* Do not assume one node hosts only one service.
* Do not overwrite raw GPS speed/course values.
* Do not mix navigation into the common location context.
* Do not fabricate dates when GPS date is unavailable.
* Do not treat system time as GPS-authoritative without explicit synchronization.
* Keep UTC canonical.
* Preserve local timezone and UTC offset as derived metadata.
* Do not modify finalized evidence payloads after capture.
* GPS context should enrich evidence metadata, not replace the evidence itself.
* Keep controller integration generic.
* Prefer configuration/environment variables over hardcoded operational values.
* Preserve compatibility with ARM64 Raspberry Pi deployment.

---

# 21. Current Overall Status

`edge-gps` is beyond the initial UART/parser MVP.

The hardware, UART path, NMEA parser, diagnostics, controller registration, timestamp normalization, and context-model foundation are working.

The project is currently at the transition between:

```text
GPS acquisition service
```

and:

```text
node-local GPS context provider for the entire Edge platform
```

The next meaningful milestone is not PPS. The next milestone is completing and validating the local context service, then integrating that context into `edge-video` and `edge-audio` through a stable shared contract.

PPS and system-clock discipline should follow only after the common timestamp/context architecture is proven.
