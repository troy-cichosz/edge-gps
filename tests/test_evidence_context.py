from app.evidence_context import (
    EvidenceContext,
    LocationContext,
    SourceContext,
)


def test_location_context():
    location = LocationContext(
        latitude=38.914947,
        longitude=-104.71621866666666,
        altitude_m=2065.7,
        quality=1,
        satellites=6,
        hdop=1.4,
        vdop=3.07,
        pdop=3.37,
    )

    assert location.to_dict() == {
        "latitude": 38.914947,
        "longitude": -104.71621866666666,
        "altitude_m": 2065.7,
        "quality": 1,
        "satellites": 6,
        "hdop": 1.4,
        "vdop": 3.07,
        "pdop": 3.37,
    }


def test_evidence_context():
    timestamp = {
        "utc": "2026-09-09T14:56:29+00:00",
        "local": "2026-09-09T08:56:29-06:00",
        "timezone": "America/Denver",
        "utc_offset": "-06:00",
    }

    source = SourceContext(
        node_id="pi4nVME",
        service_id="edge-gps",
    )

    location = LocationContext(
        latitude=38.914947,
        longitude=-104.71621866666666,
        altitude_m=2065.7,
        quality=1,
        satellites=6,
        hdop=1.4,
        vdop=3.07,
        pdop=3.37,
    )

    context = EvidenceContext(
        timestamp=timestamp,
        source=source,
        location=location,
    )

    result = context.to_dict()

    assert result["timestamp"] == timestamp
    assert result["source"]["node_id"] == "pi4nVME"
    assert result["source"]["service_id"] == "edge-gps"
    assert result["location"]["satellites"] == 6