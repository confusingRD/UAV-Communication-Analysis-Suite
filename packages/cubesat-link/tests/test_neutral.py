import unittest
from math import acos, cos, sin, radians, sqrt, degrees, exp
from cubesat_link import *


class NeutralTests(unittest.TestCase):
    def test_vacuum_exact_slant_above_old_limit(self):
        profile = NeutralProfile((0, 11000), (1, 1), "test vacuum", (1e8, 12e9),
                                 (0,0), 915e6, "vacuum")
        r = SPHERE.semi_major_m + 500000
        state = SatelliteState((r*cos(radians(10)), r*sin(radians(10)), 0), "ECEF")
        station = GroundStation(0,0,0)
        ray = trace_spherical(station, state, 915e6, profile, earth=SPHERE)
        g = geometry(station,state,SPHERE)
        self.assertEqual(ray.status, "computed", ray.reason)
        self.assertAlmostEqual(ray.path_length_m, g.slant_range_m, places=3)
        self.assertAlmostEqual(ray.apparent_elevation_deg, g.elevation_deg, places=6)
        self.assertAlmostEqual(ray.bending_deg, 0, places=7)
        self.assertEqual(ray.excess_path_m, 0)
        self.assertEqual(ray.gas_loss.value, 0)

    def test_zenith_integrals_and_vacuum_tail(self):
        profile = NeutralProfile((0,10000,20000), (1.0003,1.0001,1), "synthetic", (1e8,12e9),
                                 (0.02,0.01,0), 2.4e9, "synthetic gamma")
        ray = trace_spherical(GroundStation(0,0,0), SatelliteState((6871000,0,0),"ECEF"),2.4e9,profile,earth=SPHERE)
        self.assertEqual(ray.status,"computed",ray.reason)
        self.assertAlmostEqual(ray.path_length_m,500000,places=4)
        self.assertAlmostEqual(ray.excess_path_m,2.5,places=7)
        self.assertAlmostEqual(ray.gas_loss.value,0.2,places=7)
        self.assertEqual(ray.apparent_elevation_deg,90)

    def test_no_silent_gas_clamp(self):
        profile=NeutralProfile((0,10000),(1,1),"synthetic",(1e8,12e9),(0.1,0),1e9,"1 GHz table")
        ray=trace_spherical(GroundStation(0,0,0),SatelliteState((6871000,0,0),"ECEF"),868e6,profile,earth=SPHERE)
        self.assertEqual(ray.gas_loss.status,"not_computable")

    def test_bad_boundary_duct_and_ellipsoid(self):
        with self.assertRaises(ValueError):
            NeutralProfile((0,11000),(1.0003,1.0001),"bad",(1e8,12e9))
        duct=NeutralProfile((0,1000),(1.001,1),"synthetic duct",(1e8,12e9))
        args=(GroundStation(0,0,0),SatelliteState((6871000,0,0),"ECEF"),915e6,duct)
        self.assertEqual(trace_spherical(*args,earth=SPHERE).status,"not_computable")
        self.assertEqual(trace_spherical(*args,earth=WGS84).status,"not_computable")

    def test_reference_bending_and_ground_clear(self):
        station=GroundStation(0,0,0)
        r=6871000
        p=SatelliteState((r*cos(radians(20)),r*sin(radians(20)),0),"ECEF")
        ray=trace_spherical(station,p,915e6,p834_reference_profile(),earth=SPHERE)
        self.assertEqual(ray.status,"computed",ray.reason)
        self.assertGreater(ray.apparent_elevation_deg,geometry(station,p,SPHERE).elevation_deg)
        self.assertTrue(ray.ground_clear)
        self.assertLess(abs(ray.endpoint_residual_rad),1e-8)

    def test_refracted_horizon_distinct_from_geometric(self):
        station=GroundStation(0,0,0)
        profile=p834_reference_profile()
        radius=6871000
        overhead=trace_spherical(station,SatelliteState((radius,0,0),'ECEF'),915e6,profile,earth=SPHERE)
        geometric_horizon=degrees(acos(6371000/radius))
        self.assertGreater(overhead.max_central_angle_deg,geometric_horizon)
        phi=radians((overhead.max_central_angle_deg+geometric_horizon)/2)
        p=SatelliteState((radius*cos(phi),radius*sin(phi),0),'ECEF')
        r=evaluate_link(station,p,915e6,earth=SPHERE,neutral_profile=profile)
        self.assertTrue(r.geometry.earth_occulted)
        self.assertFalse(r.geometry.geometric_visible)
        self.assertTrue(r.refracted_visible)
        self.assertTrue(r.neutral_ray.ground_clear)
        phi=radians(overhead.max_central_angle_deg+0.1)
        p=SatelliteState((radius*cos(phi),radius*sin(phi),0),'ECEF')
        self.assertEqual(trace_spherical(station,p,915e6,profile,earth=SPHERE).status,'not_computable')

    def test_p834_approximation_and_grid_convergence(self):
        earth=Earth(6370000,0)
        radius=earth.semi_major_m+500000
        p=SatelliteState((radius*cos(radians(20)),radius*sin(radians(20)),0),'ECEF')
        coarse=trace_spherical(GroundStation(0,0,0),p,915e6,p834_reference_profile(),earth)
        h=tuple(range(0,100001,125))
        n=tuple(1+0.000315*exp(-0.1361*x/1000) for x in h[:-1])+(1.0,)
        fine=trace_spherical(GroundStation(0,0,0),p,915e6,
                              NeutralProfile(h,n,'P834 finer reference grid',(1e8,12e9)),earth)
        theta=coarse.apparent_elevation_deg
        approximation=1/(1.314+0.6437*theta+0.02869*theta**2)
        self.assertLess(abs(coarse.bending_deg-approximation),0.02)
        self.assertLess(abs(coarse.bending_deg-fine.bending_deg),0.0001)


if __name__ == "__main__":
    unittest.main()
