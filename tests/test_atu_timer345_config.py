import unittest
from ecu_workbench.atu import Atu1A,TSTR,TMDR,TCR3,TCR4,TCR5
from ecu_workbench.nc_boot import BootStop

class Timer345ConfigurationTests(unittest.TestCase):
    def test_mode_zero_and_separate_stopped_clock_latches(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        a.write(TMDR,1,0);self.assertEqual(a.read(TMDR,1),0)
        for address in (TCR3,TCR4,TCR5):
            for select in range(8):
                for edge in range(4):
                    value=select|(edge<<4);a.write(address,1,value)
                    self.assertEqual(a.read(address,1),value)
        self.assertEqual(a.events,[]);self.assertEqual(a.ticks,0)

    def test_reserved_pwm_start_and_width_guards_are_atomic(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for value in (1,7,8,0xFF):
            with self.assertRaises(BootStop):a.write(TMDR,1,value)
        self.assertEqual(a.regs[TMDR],0)
        for address,bit in ((TCR3,0x10),(TCR4,0x20),(TCR5,0x40)):
            a.regs[TSTR]=bit
            with self.assertRaises(BootStop):a.write(TMDR,1,0)
            with self.assertRaises(BootStop):a.write(address,1,4)
            self.assertEqual(a.regs[address],0);a.regs[TSTR]=0
            for value in (8,9,0x40,0x80):
                with self.assertRaises(BootStop):a.write(address,1,value)
            with self.assertRaises(BootStop):a.write(address,2,0)

    def test_unknown_manual_stops_before_configuration(self):
        a=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):a.read(TMDR,1)
        with self.assertRaises(BootStop):a.write(TMDR,1,0)
        with self.assertRaises(BootStop):a.write(TCR3,1,4)
        a.write(TSTR,1,0);a.write(TMDR,1,0);a.write(TCR3,1,4)
        self.assertEqual(a.regs[TCR3],4)
