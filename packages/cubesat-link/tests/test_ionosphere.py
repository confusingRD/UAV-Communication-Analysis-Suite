import unittest
from math import pi
from cubesat_link import *


class IonosphereTests(unittest.TestCase):
    def test_finite_endpoint_and_variable_b(self):
        # Both Ne and B linear; integral of their product must not use avg(Ne)*avg(B).
        p=ElectronPath((0,1000000),(0,2e12),"synthetic",(0,1e-4))
        tec=integrate_electrons(p,500000)
        self.assertAlmostEqual(tec.electrons_per_m2/1e16,25)
        self.assertAlmostEqual(tec.ne_b_integral/(1e-4*2e12/1e12*500000**3/3),1)
        self.assertLess(tec.electrons_per_m2,integrate_electrons(p,1000000).electrons_per_m2)
        with self.assertRaises(ValueError): integrate_electrons(p,1000001)

    def test_reference_plasma_and_faraday(self):
        tec=SlantTEC(1e17,500000,"10 TECU fixture",5e12)
        effects=ionospheric_effects(1e9,tec)
        self.assertAlmostEqual(effects['group_delay'].value,4.03/299792458,places=16)
        self.assertAlmostEqual(effects['phase_path'].value,-4.03)
        self.assertAlmostEqual(effects['faraday_rotation'].value,0.118)
        self.assertEqual(effects['scintillation'].status,'not_computable')
        self.assertEqual(effects['absorption'].status,'not_computable')
        self.assertEqual(ionospheric_effects(1e9,SlantTEC(1e17,500000,'fixture'))['faraday_rotation'].status,'not_computable')

    def test_polarization(self):
        faraday=Effect(pi/4,'rad','computed','fixture')
        self.assertAlmostEqual(polarization_loss(Polarization('linear','linear',0),faraday).value,3.01029995664)
        self.assertEqual(polarization_loss(Polarization('circular','circular',circular_match=True),faraday).value,0)
        self.assertEqual(polarization_loss(None,faraday).status,'not_computable')
        self.assertEqual(polarization_loss(Polarization('linear','linear',pi/4),faraday).status,'not_computable')


if __name__ == '__main__': unittest.main()
