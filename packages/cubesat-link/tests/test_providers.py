import unittest
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from cubesat_link import *


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.epoch = datetime(2026,11,14,tzinfo=timezone.utc)
        self.station = GroundStation(0,0,0)
        self.state = SatelliteState((6871000,0,0),'ECEF',self.epoch)
        self.meta = ProviderMetadata('synthetic fixture','1',self.epoch,'This 500 km radial path only',
                                      {'distance_m':'m','density_per_m3':'el/m3','b_parallel_t':'T'},'synthetic')
        self.binding = PathBinding(self.station,self.state,SPHERE,'straight',500000)

    def test_bound_electrons_and_missing_coverage(self):
        data = ElectronPath((0,500000),(2e11,2e11),'synthetic',(5e-5,5e-5))
        provider = BoundElectronProvider(data,self.meta,self.binding)
        result = evaluate_link(self.station,self.state,1e9,earth=SPHERE,electron_provider=provider)
        self.assertAlmostEqual(result.ionosphere['faraday_rotation'].value,0.118)
        self.assertEqual(result.providers['electrons']['version'],'1')
        self.assertAlmostEqual(result.ionosphere['slant_tec'].value/1e16,10)
        incomplete = replace(provider,data=ElectronPath((0,1000),(2e11,2e11),'incomplete'))
        result = evaluate_link(self.station,self.state,1e9,earth=SPHERE,electron_provider=incomplete)
        self.assertEqual(result.ionosphere['group_delay'].status,'not_computable')

    def test_wrong_epoch_endpoint_branch_and_units(self):
        provider = BoundElectronProvider(ElectronPath((0,500000),(0,0),'fixture'),self.meta,self.binding)
        for binding in (replace(self.binding,state=replace(self.state,epoch_utc=self.epoch+timedelta(seconds=1))),
                        replace(self.binding,earth=Earth(6370000,0)),
                        replace(self.binding,path_kind='spherical_refracted'),
                        replace(self.binding,path_length_m=500001)):
            self.assertEqual(provider.get(binding).status,'not_computable')
        with self.assertRaises(ValueError):
            replace(provider,metadata=replace(self.meta,units={'distance_m':'km','density_per_m3':'el/cm3'}))

    def test_p676_unavailable_and_no_clamping(self):
        for frequency in (868e6,915e6,2.4e9):
            result = P676GasProvider().get(frequency)
            self.assertEqual(result.status,'not_computable')
            self.assertIsNone(result.data)
        self.assertIn('Outside',P676GasProvider().get(915e6).reason)
        self.assertIn('spectral-line',P676GasProvider().get(2.4e9).reason)

    def test_bounded_uav_profile_never_extrapolated_to_cubesat(self):
        profile = NeutralProfile((0,11000),(1.0003,1.0001),'synthetic',(1e9,3e9),outside='unavailable')
        low = SatelliteState((6377000,0,0),'ECEF')
        ray = trace_spherical(self.station,low,2.4e9,profile,SPHERE)
        self.assertEqual(ray.status,'computed')
        self.assertAlmostEqual(ray.path_length_m,6000,places=6)
        high = trace_spherical(self.station,self.state,2.4e9,profile,SPHERE)
        self.assertEqual(high.status,'not_computable')
        self.assertIn('bounded',high.reason)
        self.assertIsNone(high.total_excess_m)

    def test_observation_epoch_is_not_silently_reused(self):
        profile = NeutralProfile((0,20000),(1.0003,1),'synthetic',(1e9,3e9))
        metadata = replace(self.meta,units={'height_m':'m','refractive_index':'1'},temporal_kind='observation',
                           epoch_utc=self.epoch+timedelta(seconds=1))
        provider = NeutralTableProvider(profile,metadata)
        result = evaluate_link(self.station,self.state,2.4e9,earth=SPHERE,neutral_provider=provider)
        self.assertIsNone(result.path_available)
        self.assertEqual(result.neutral_excess_delay_s.status,'not_computable')


if __name__=='__main__':
    unittest.main()
