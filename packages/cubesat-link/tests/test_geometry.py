import unittest
from datetime import datetime, timedelta, timezone
from math import cos, sin, radians
from cubesat_link import *


class GeometryTests(unittest.TestCase):
    def test_overhead_and_antipode(self):
        s = GroundStation(0, 0, 0)
        g = geometry(s, SatelliteState((6878137, 0, 0), "ECEF"))
        self.assertEqual(g.slant_range_m, 500000)
        self.assertEqual(g.elevation_deg, 90)
        self.assertIsNone(g.azimuth_deg)
        self.assertTrue(g.geometric_visible)
        g = geometry(s, SatelliteState((-6878137, 0, 0), "ECEF"))
        self.assertTrue(g.earth_occulted)
        self.assertFalse(g.geometric_visible)

    def test_tangent_mask_and_elevated_station(self):
        p = SatelliteState((6378137, 1000000, 0), "ECEF")
        self.assertTrue(geometry(GroundStation(0, 0, 0), p).geometric_visible)
        self.assertFalse(geometry(GroundStation(0, 0, 0, 0.1), p).above_mask)
        g = geometry(GroundStation(0, 0, 1000), SatelliteState((6379136, 1000, 0), "ECEF"))
        self.assertFalse(g.earth_occulted)
        self.assertFalse(g.above_mask)

    def test_wgs84_pole_and_enu(self):
        self.assertAlmostEqual(station_ecef(GroundStation(90, 0, 0))[2], 6356752.314245, places=5)
        g = geometry(GroundStation(0, 0, 0), SatelliteState((6378137, 1000, 0), "ECEF"))
        self.assertEqual(g.azimuth_deg, 90)

    def test_windows_hidden_between_two_samples(self):
        # up=100 km, east=-200..200 km: 45-degree cone entered at t=10, exited at 30.
        epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
        states = [SatelliteState((6478137, y, 0), "ECEF", epoch+timedelta(seconds=t))
                  for t, y in [(0, -200000), (40, 200000)]]
        w = contact_windows(GroundStation(0, 0, 0, 45), states)
        self.assertEqual(len(w), 1)
        self.assertAlmostEqual((w[0].start_utc-epoch).total_seconds(), 10)
        self.assertAlmostEqual((w[0].end_utc-epoch).total_seconds(), 30)
        self.assertFalse(w[0].start_clipped)
        self.assertFalse(w[0].end_clipped)

    def test_frame_epoch_and_gaps(self):
        with self.assertRaises(ValueError):
            SatelliteState((1, 2, 3), "ECI")
        with self.assertRaises(ValueError):
            SatelliteState((1, 2, 3), "ECEF", datetime(2026, 1, 1))
        epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
        a = SatelliteState((6878137, 0, 0), "ECEF", epoch)
        b = SatelliteState(a.position_m, "ECEF", epoch+timedelta(seconds=61))
        with self.assertRaises(ValueError):
            contact_windows(GroundStation(0,0,0), [a,b])

    def test_multiple_passes_and_clipping(self):
        epoch=datetime(2026,1,1,tzinfo=timezone.utc)
        # Geometric elevation sign changes at t=5,15,25,35 seconds.
        states=[SatelliteState((6378137+x,1000000,0),'ECEF',epoch+timedelta(seconds=10*i))
                for i,x in enumerate((-10000,10000,-10000,10000,-10000))]
        w=contact_windows(GroundStation(0,0,0),states)
        self.assertEqual([(int((a.start_utc-epoch).total_seconds()),int((a.end_utc-epoch).total_seconds()))
                          for a in w],[(5,15),(25,35)])
        states=[SatelliteState((6878137,0,0),'ECEF',epoch+timedelta(seconds=i)) for i in (0,10)]
        w=contact_windows(GroundStation(0,0,0),states)
        self.assertTrue(w[0].start_clipped and w[0].end_clipped)


if __name__ == "__main__":
    unittest.main()
