import unittest
from ecu_workbench.atu import Atu1A,TCR1B,TCR2A,TCR2B,TSTR
from ecu_workbench.nc_boot import BootStop

class Tcr2ConfigurationTests(unittest.TestCase):
    def test_separate_latches_and_exact_clock_fields(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for address in (TCR2A,TCR2B):
            for select in range(8):
                for edge in range(4):
                    value=select|(edge<<4);a.write(address,1,value)
                    self.assertEqual(a.read(address,1),value)
        self.assertEqual(a.regs[TCR1B],0);self.assertEqual(a.events,[])

    def test_per_counter_start_guard_and_invalid_fields_are_atomic(self):
        for address,bit in ((TCR2A,4),(TCR2B,8)):
            a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
            a.regs[TSTR]=bit
            with self.assertRaises(BootStop):a.write(address,1,4)
            self.assertEqual(a.regs[address],0);a.regs[TSTR]=0
            for value in (8,9,0x40,0x80):
                with self.assertRaises(BootStop):a.write(address,1,value)
            with self.assertRaises(BootStop):a.write(address,2,0)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.write(TCR2A,1,4)
