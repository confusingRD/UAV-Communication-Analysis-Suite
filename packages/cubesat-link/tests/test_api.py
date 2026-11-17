import json
import unittest
from cubesat_link import *


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.station=GroundStation(0,0,0,10)
        self.satellite=SatelliteState((6878137,0,0),'ECEF')
        self.radio=Radio(30,2,12,0,0,2,-120,'synthetic test mode, fixed threshold','ideal tracking')
        self.pol=Polarization('linear','linear',0)

    def test_vacuum_example_json_and_budget(self):
        r=evaluate_link(self.station,self.satellite,915e6,radio=self.radio,polarization=self.pol,vacuum=True)
        self.assertAlmostEqual(r.budget.margin_db.value,16.3443948100673,places=10)
        self.assertTrue(r.path_available)
        json.dumps(r.to_dict(),allow_nan=False)
        self.assertEqual(r.budget.throughput_bps.status,'not_computable')

    def test_missing_not_zero(self):
        r=evaluate_link(self.station,self.satellite,915e6,radio=self.radio,polarization=self.pol)
        self.assertIsNone(r.losses_db['gas'].value)
        self.assertIsNone(r.budget.margin_db.value)
        self.assertIsNone(r.refracted_visible)

    def test_radio_assumptions_survive_incomplete_budget(self):
        r=evaluate_link(self.station,self.satellite,2.4e9,radio=self.radio)
        self.assertEqual(r.budget.radio_assumptions['receiver_mode'],self.radio.receiver_mode)
        self.assertEqual(r.budget.radio_assumptions['antenna_basis'],self.radio.antenna_basis)
        self.assertIsNone(r.budget.margin_db.value)

    def test_unresolved_ray_with_raw_electrons_is_unknown(self):
        r=evaluate_link(self.station,self.satellite,2.4e9,
                        neutral_profile=p834_reference_profile(),
                        electrons=ElectronPath((0,500000),(0,0),'synthetic test'))
        self.assertIsNone(r.path_available)
        self.assertEqual(r.ionosphere['group_delay'].status,'not_computable')

    def test_blocked_no_budget(self):
        r=evaluate_link(self.station,SatelliteState((-6878137,0,0),'ECEF'),915e6,
                        radio=self.radio,polarization=self.pol,vacuum=True)
        self.assertFalse(r.path_available)
        self.assertIsNone(r.budget.received_power_dbm.value)

    def test_duplicate_gas_and_plasma_endpoint(self):
        profile=NeutralProfile((0,10000),(1,1),'fixture',(1e8,12e9),(0.1,0),915e6,'fixture')
        with self.assertRaises(ValueError):
            evaluate_link(self.station,SatelliteState((6871000,0,0),'ECEF'),915e6,
                          earth=SPHERE,neutral_profile=profile,
                          supplied_losses={'gas':Effect(1,'dB','computed','duplicate')})
        with self.assertRaises(ValueError):
            evaluate_link(self.station,self.satellite,915e6,electrons=SlantTEC(1e17,1e7,'wrong endpoint'))

    def test_delay_does_not_change_power(self):
        pol=Polarization('circular','circular',circular_match=True)
        zero={k:Effect(0,'dB','assumed','explicit idealized fixture') for k in
              ('gas','rain','cloud','beam_spreading','neutral_scintillation',
               'ionospheric_scintillation','ionospheric_absorption')}
        a=evaluate_link(self.station,self.satellite,915e6,radio=self.radio,polarization=pol,
                        electrons=SlantTEC(0,500000,'zero fixture',0),supplied_losses=zero)
        b=evaluate_link(self.station,self.satellite,915e6,radio=self.radio,polarization=pol,
                        electrons=SlantTEC(1e18,500000,'large fixture',5e13),supplied_losses=zero)
        self.assertEqual(a.budget.margin_db.value,b.budget.margin_db.value)
        self.assertGreater(b.ionosphere['group_delay'].value,0)


if __name__=='__main__': unittest.main()
