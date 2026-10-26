import unittest
from ecu_workbench.atu import Atu1A,DSTR
from ecu_workbench.nc_boot import BootStop

class DowncounterStartTests(unittest.TestCase):
    def test_zero_write_leaves_known_and_unknown_state_untouched(self):
        for power in (False,True):
            a=Atu1A(power_on=power,trace=[],stop_type=BootStop)
            before=a.regs[DSTR];a.write(DSTR,2,0)
            self.assertEqual(a.regs[DSTR],before);self.assertEqual(a.events,[])
            if not power:
                with self.assertRaises(BootStop):a.read(DSTR,2)
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        a.regs[DSTR]=0x8001;a.write(DSTR,2,0)
        self.assertEqual(a.regs[DSTR],0x8001)

    def test_starts_and_wrong_widths_do_not_mutate(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for value in (1,0x8000,0xFFFF):
            with self.assertRaises(BootStop):a.write(DSTR,2,value)
        for width in (1,4):
            with self.assertRaises(BootStop):a.write(DSTR,width,0)
            with self.assertRaises(BootStop):a.read(DSTR,width)
        self.assertEqual(a.regs[DSTR],0);self.assertEqual(a.events,[])
