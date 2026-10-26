import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootStop
from ecu_workbench.atu import Atu1A,TSTR,TSTR2,TSTR3,PSCR_EXTRA

class AtuCommonStopTests(unittest.TestCase):
    def test_power_stops_and_prescaler_latches(self):
        b=program(0x0009).bus
        for a in (TSTR2,TSTR3):
            self.assertEqual(b.read(a,1),0);b.write(a,1,0)
        for a in PSCR_EXTRA:
            for value in (0,1,31):b.write(a,1,value);self.assertEqual(b.read(a,1),value)
        self.assertEqual(b.atu.ticks,0);self.assertEqual(b.atu.events,[])

    def test_start_reserved_and_combined_access_rejected_atomically(self):
        b=program(0x0009).bus;before=dict(b.atu.regs)
        for a in (TSTR2,TSTR3):
            with self.assertRaises(BootStop):b.write(a,1,1)
            with self.assertRaises(BootStop):b.write(a,2,0)
        for a in PSCR_EXTRA:
            with self.assertRaises(BootStop):b.write(a,1,32)
        self.assertEqual(b.atu.regs,before)

    def test_manual_unknown_and_running_counter_guard(self):
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.read(TSTR2,1)
        m.write(TSTR2,1,0);self.assertEqual(m.read(TSTR2,1),0)
        with self.assertRaises(BootStop):m.write(PSCR_EXTRA[0],1,1)
        b=program(0x0009).bus;b.write(TSTR,1,2)
        with self.assertRaises(BootStop):b.write(PSCR_EXTRA[0],1,1)
