import unittest
from ecu_workbench.atu import Atu1A,PWM_TCR_STOP,TSTR2
from ecu_workbench.nc_boot import BootStop

class PwmClockConfigurationTests(unittest.TestCase):
    def test_two_independent_fields_and_registers(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for address in PWM_TCR_STOP:
            for lo in range(6):
                for hi in range(6):
                    value=lo|(hi<<4);a.write(address,1,value)
                    self.assertEqual(a.read(address,1),value)
        self.assertEqual(a.events,[]);self.assertEqual(a.ticks,0)

    def test_invalid_selectors_reserved_unknown_and_starts(self):
        for address,bits in PWM_TCR_STOP.items():
            a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
            for value in (6,7,0x60,0x70,0x08,0x80,0xFF):
                with self.assertRaises(BootStop):a.write(address,1,value)
                self.assertEqual(a.regs[address],0)
            a.regs[TSTR2]=bits
            with self.assertRaises(BootStop):a.write(address,1,0x44)
            with self.assertRaises(BootStop):a.write(address,2,0)
            m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
            with self.assertRaises(BootStop):m.read(address,1)
            with self.assertRaises(BootStop):m.write(address,1,0x44)

    def test_pmdr_zero_only_with_timer6_stopped(self):
        from ecu_workbench.atu import PMDR
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        a.write(PMDR,1,0);self.assertEqual(a.read(PMDR,1),0)
        with self.assertRaises(BootStop):a.write(PMDR,1,1)
        a.regs[TSTR2]=1
        with self.assertRaises(BootStop):a.write(PMDR,1,0)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.write(PMDR,1,0)
        self.assertEqual(a.events,[])
