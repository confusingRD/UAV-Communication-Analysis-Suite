import unittest
from math import log10
from cubesat_link import Effect, Radio, fspl_db, compute_budget
from cubesat_link.budget import LOSS_NAMES


class BudgetTests(unittest.TestCase):
    def test_p525_reference_and_scaling(self):
        # P.525-5 Eq (6), rounded constant 32.4, MHz/km.
        expected=32.4+20*log10(2400)+20*log10(500)
        self.assertAlmostEqual(fspl_db(500000,2.4e9)-expected,0.0477832218834,places=10)
        self.assertAlmostEqual(fspl_db(1000000,2.4e9)-fspl_db(500000,2.4e9),6.02059991328,places=10)
        self.assertAlmostEqual(fspl_db(500000,1.83e9)-fspl_db(500000,915e6),6.02059991328,places=10)

    def test_ledger_and_no_double_count(self):
        losses={n:Effect(0,"dB","assumed","explicit vacuum/alignment") for n in LOSS_NAMES}
        losses['free_space']=Effect(150,"dB","computed","fixture")
        losses['gas']=Effect(2,"dB","computed","fixture gamma integral")
        radio=Radio(30,2,10,1,2,3,-120,"test mode","specified boresight offset")
        b=compute_budget(losses,radio,path_available=True)
        self.assertEqual(b.received_power_dbm.value,-116)
        self.assertEqual(b.margin_db.value,4)
        self.assertEqual(b.throughput_bps.status,"not_computable")
        with self.assertRaises(ValueError):
            compute_budget(dict(losses,total_atmosphere=losses['gas']),radio,path_available=True)
        losses['gas']=Effect(None,"dB","not_computable","missing")
        self.assertIsNone(compute_budget(losses,radio,path_available=True).margin_db.value)

    def test_invalid(self):
        for d,f in [(0,1e9),(1e3,0),(float('nan'),1e9)]:
            with self.assertRaises(ValueError): fspl_db(d,f)


if __name__ == '__main__': unittest.main()
