"""Independent numerical formulation and analytic orbit checks, not field validation."""
import unittest
from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from math import acos, cos, sin, radians, sqrt

from cubesat_link import (Earth, SPHERE, GroundStation, SatelliteState, geometry,
                          contact_windows, evaluate_link, trace_spherical,
                          p834_reference_profile)
from cubesat_link.types import C


def cartesian_fermat_endpoint(step_m):
    """Independent Cartesian RK4: d(n*u)/ds=grad(n), fixed arc length.

    Does not use the production Bouguer integrals, quadrature, or shooting.
    Same piecewise-linear input medium, independently interpolated here.
    """
    profile = p834_reference_profile()
    h, ns = profile.height_m, profile.refractive_index
    def rhs(y):
        x, z, ux, uz, optical = y
        r = sqrt(x*x+z*z)
        height = r-SPHERE.semi_major_m
        if height >= h[-1]:
            n, dn = 1.0, 0.0
        else:
            i = max(0, bisect_right(h, height)-1)
            dn = (ns[i+1]-ns[i])/(h[i+1]-h[i])
            n = ns[i]+dn*(height-h[i])
        gx, gz = dn*x/r, dn*z/r
        proj = ux*gx+uz*gz
        return (ux, uz, (gx-ux*proj)/n, (gz-uz*proj)/n, n-1)
    y = (SPHERE.semi_major_m, 0., sin(radians(10)), cos(radians(10)), 0.)
    def advance(y, k, scale):
        return tuple(a+scale*b for a,b in zip(y,k))
    for _ in range(round(500000/step_m)):
        a = rhs(y)
        b = rhs(advance(y,a,step_m/2))
        c = rhs(advance(y,b,step_m/2))
        d = rhs(advance(y,c,step_m))
        y = tuple(v+step_m*(aa+2*bb+2*cc+dd)/6
                  for v,aa,bb,cc,dd in zip(y,a,b,c,d))
    return y


class ReleaseCoreTests(unittest.TestCase):
    def test_defaults_do_not_switch_earth(self):
        station = GroundStation(0,0,0)
        state = SatelliteState((6878137,0,0),'ECEF')
        profile = p834_reference_profile()
        self.assertEqual(trace_spherical(station,state,2.4e9,profile).status,'not_computable')
        r = evaluate_link(station,state,2.4e9,neutral_profile=profile)
        self.assertIsNone(r.path_available)
        self.assertEqual(r.geometry.slant_range_m,500000)
        # A custom radius must be used unchanged by BOTH geometry and tracing.
        earth = Earth(6000000,0)
        state = SatelliteState((6500000,0,0),'ECEF')
        r = evaluate_link(station,state,2.4e9,earth=earth,neutral_profile=profile)
        self.assertAlmostEqual(r.neutral_ray.path_length_m,r.geometry.slant_range_m,places=5)

    def test_curved_delay_against_cartesian_fermat_ode(self):
        coarse, fine = cartesian_fermat_endpoint(10), cartesian_fermat_endpoint(5)
        self.assertLess(sqrt(sum((a-b)**2 for a,b in zip(coarse[:2],fine[:2]))),0.005)
        x,z,_,_,refractivity = fine
        r = evaluate_link(GroundStation(0,0,0), SatelliteState((x,z,0),'ECEF'),
                          2.4e9,earth=SPHERE,neutral_profile=p834_reference_profile())
        ray = r.neutral_ray
        self.assertEqual(ray.status,'computed')
        self.assertAlmostEqual(ray.apparent_elevation_deg,10,delta=1e-5)
        self.assertAlmostEqual(ray.path_length_m,500000,delta=0.005)
        self.assertAlmostEqual(ray.refractivity_excess_m,refractivity,delta=0.001)
        chord = sqrt((x-SPHERE.semi_major_m)**2+z*z)
        expected = (500000-chord+refractivity)/C
        self.assertGreater(ray.geometric_excess_m,0.01)
        self.assertAlmostEqual(r.neutral_excess_delay_s.value,expected,delta=0.006/C)

    def test_orbit_windows_time_step_convergence(self):
        epoch = datetime(2026,11,14,tzinfo=timezone.utc)
        radius = SPHERE.semi_major_m+500000
        omega = sqrt(3.986004418e14/radius**3)-7.292115e-5
        station = GroundStation(0,0,0,10)
        # Analytic circular equatorial orbit intersecting the elevation mask.
        half_angle = acos(SPHERE.semi_major_m/radius*cos(radians(10)))-radians(10)
        expected = (600-half_angle/omega,600+half_angle/omega)
        errors = []
        for step in (60,30,10,5):
            states = [SatelliteState((radius*cos(omega*(t-600)),
                                      radius*sin(omega*(t-600)),0),'ECEF',
                                      epoch+timedelta(seconds=t))
                      for t in range(0,1201,step)]
            windows = contact_windows(station,states,SPHERE,mode='geometric')
            self.assertEqual(len(windows),1)
            w = windows[0]
            self.assertFalse(w.start_clipped or w.end_clipped)
            values = ((w.start_utc-epoch).total_seconds(),(w.end_utc-epoch).total_seconds())
            errors.append(max(abs(a-b) for a,b in zip(values,expected)))
            for t in (values[0]-1,600,values[1]+1):
                state = SatelliteState((radius*cos(omega*(t-600)),radius*sin(omega*(t-600)),0),'ECEF')
                visible = evaluate_link(station,state,2.4e9,earth=SPHERE,vacuum=True).path_available
                self.assertEqual(visible,t==600)
        self.assertLess(errors[-1],0.02)
        self.assertLess(errors[-1],errors[0]/20)
        with self.assertRaises(ValueError):
            contact_windows(station,states,SPHERE,mode='refracted')


if __name__ == '__main__':
    unittest.main()

