from app.nmea import NMEAParser

GGA = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
RMC = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
GSA = "$GPGSA,A,3,04,05,09,12,24,25,29,31,,,,,1.8,1.0,1.5*33"


def test_gga():
    p = NMEAParser()
    state = p.feed(GGA)
    assert state is not None
    assert state.fix.valid
    assert round(state.fix.latitude, 5) == 48.11730
    assert round(state.fix.longitude, 5) == 11.51667
    assert state.fix.satellites == 8
    assert state.fix.altitude_m == 545.4


def test_rmc():
    p = NMEAParser()
    state = p.feed(RMC)
    assert state is not None
    assert state.fix.valid
    assert round(state.fix.speed_mps, 2) == 11.52
    assert round(state.fix.course_deg, 1) == 84.4
    assert state.gps_time.year == 1994


def test_bad_checksum_is_rejected():
    p = NMEAParser()
    assert p.feed(GGA[:-2] + "00") is None
    assert p.invalid_checksum_count == 1


def test_gsa():
    p = NMEAParser()
    state = p.feed(GSA)
    assert state is not None
    assert state.fix.pdop == 1.8
    assert state.fix.hdop == 1.0
    assert state.fix.vdop == 1.5
