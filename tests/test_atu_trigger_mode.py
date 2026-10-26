import unittest
from ecu_workbench.atu import Atu1A,TRGMDR,TCNR,OTR,DSTR
from ecu_workbench.nc_boot import BootStop

class TriggerModeTests(unittest.TestCase):
    def test_disconnected_trigger_mode_readback_no_events(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for value in (0x80,0):
            a.write(TRGMDR,1,value);self.assertEqual(a.read(TRGMDR,1),value)
        self.assertEqual(a.events,[]);self.assertEqual(a.regs[DSTR],0)
        for control in (TCNR,OTR):a.write(control,2,0)

    def test_unknown_enabled_reserved_and_width_guards(self):
        for control in (DSTR,):
            a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
            a.regs[control]=None
            with self.assertRaises(BootStop):a.write(TRGMDR,1,0x80)
            a.regs[control]=1
            with self.assertRaises(BootStop):a.write(TRGMDR,1,0x80)
            self.assertEqual(a.regs[TRGMDR],0)
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):a.write(TRGMDR,1,1)
        with self.assertRaises(BootStop):a.write(TRGMDR,2,0)
        for control in (TCNR,OTR):
            with self.assertRaises(BootStop):a.write(control,1,0)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.read(TRGMDR,1)
        m.write(TCNR,2,0);m.write(OTR,2,0)
        with self.assertRaises(BootStop):m.write(TRGMDR,1,0)
