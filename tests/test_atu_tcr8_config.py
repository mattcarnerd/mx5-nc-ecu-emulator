import unittest
from ecu_workbench.atu import Atu1A,TCR8
from ecu_workbench.nc_boot import BootStop

class DowncounterClockConfigurationTests(unittest.TestCase):
    def test_independent_fields_no_counter_execution(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for lo in range(6):
            for hi in range(6):
                value=lo|(hi<<4);a.write(TCR8,1,value)
                self.assertEqual(a.read(TCR8,1),value)
        self.assertEqual(a.channel8_counters,[0]*16);self.assertEqual(a.events,[])

    def test_invalid_fields_width_and_unknown_state(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for value in (6,7,0x60,0x70,8,0x80):
            with self.assertRaises(BootStop):a.write(TCR8,1,value)
            self.assertEqual(a.regs[TCR8],0)
        for width in (2,4):
            with self.assertRaises(BootStop):a.write(TCR8,width,0)
        a.channel8_counters[0]=1
        with self.assertRaises(BootStop):a.write(TCR8,1,0x44)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.read(TCR8,1)
        with self.assertRaises(BootStop):m.write(TCR8,1,0x44)

    def test_reload_disable_controls_state_without_counter_mutation(self):
        from ecu_workbench.atu import RLDENR
        for power in (True,False):
            a=Atu1A(power_on=power,trace=[],stop_type=BootStop)
            before=list(a.channel8_counters);a.write(RLDENR,1,0)
            self.assertIs(a.channel8_reload_enabled,False)
            self.assertEqual(a.read(RLDENR,1),0)
            self.assertEqual(a.channel8_counters,before)
            for value in (1,0x80,0xFF):
                with self.assertRaises(BootStop):a.write(RLDENR,1,value)
                self.assertEqual(a.regs[RLDENR],0)
