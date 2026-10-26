import unittest
from ecu_workbench.atu import Atu1A,TCR1B,TSTR
from ecu_workbench.nc_boot import BootStop

class Tcr1BConfigurationTests(unittest.TestCase):
    def test_stopped_clock_selection_no_counter_alias_or_events(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        before=dict(a.regs)
        for select in range(8):
            for edge in range(4):
                value=(edge<<4)|select;a.write(TCR1B,1,value)
                self.assertEqual(a.read(TCR1B,1),value)
        for key in before:
            if key!=TCR1B:self.assertEqual(a.regs[key],before[key])
        self.assertEqual(a.events,[])

    def test_unknown_reserved_other_clocks_and_widths(self):
        a=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):a.read(TCR1B,1)
        with self.assertRaises(BootStop):a.write(TCR1B,1,4)
        a.write(TSTR,1,0);a.write(TCR1B,1,4)
        for value in (8,9,0x40,0xFF):
            with self.assertRaises(BootStop):a.write(TCR1B,1,value)
            self.assertEqual(a.read(TCR1B,1),4)
        for width in (2,4):
            with self.assertRaises(BootStop):a.write(TCR1B,width,0)
