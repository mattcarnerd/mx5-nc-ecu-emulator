import unittest
from ecu_workbench.atu import Atu1A,TCR11,TSTR3
from ecu_workbench.nc_boot import BootStop

class Tcr11ConfigurationTests(unittest.TestCase):
    def test_clock_and_edge_fields_while_stopped(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for select in range(8):
            for edge in range(4):
                value=select|(edge<<4);a.write(TCR11,1,value)
                self.assertEqual(a.read(TCR11,1),value)
        self.assertEqual(a.events,[]);self.assertEqual(a.regs[TSTR3],0)

    def test_reserved_width_running_and_unknown_guards(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for value in (8,0x40,0x80,0xFF):
            with self.assertRaises(BootStop):a.write(TCR11,1,value)
            self.assertEqual(a.regs[TCR11],0)
        for width in (2,4):
            with self.assertRaises(BootStop):a.write(TCR11,width,0)
        a.regs[TSTR3]=1
        with self.assertRaises(BootStop):a.write(TCR11,1,4)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.read(TCR11,1)
        with self.assertRaises(BootStop):m.write(TCR11,1,4)
