import unittest
from ecu_workbench.watchdog import WatchdogTimer
from ecu_workbench.nc_boot import BootStop


def timer(**kwargs):return WatchdogTimer(power_on=True,trace=[],stop_type=BootStop,clock_supplied=True,**kwargs)

class IntervalTimerTests(unittest.TestCase):
    def test_every_divider_and_fractional_packets(self):
        for select,divisor in enumerate(WatchdogTimer.DIVISORS):
            t=timer();t.write(0xFFFFEC10,2,0xA538|select)
            t.advance_phi_cycles(divisor-1);self.assertEqual(t.tcnt,0)
            t.advance_phi_cycles(1);self.assertEqual(t.tcnt,1)
            t.advance_phi_cycles(divisor*3);self.assertEqual(t.tcnt,4)

    def test_overflow_assert_and_read_before_clear(self):
        levels=[];t=timer(request_interval=levels.append)
        t.write(0xFFFFEC10,2,0xA53C);t.write(0xFFFFEC10,2,0x5AFF)
        t.advance_phi_cycles(512);self.assertEqual(t.tcnt,0);self.assertEqual(t.overflow_count,1)
        self.assertTrue(levels[-1]);self.assertTrue(t.tcsr & 0x80)
        t.write(0xFFFFEC10,2,0xA53C);self.assertTrue(t.tcsr & 0x80)
        t.read(0xFFFFEC10,1);t.write(0xFFFFEC10,2,0xA53C)
        self.assertFalse(t.tcsr & 0x80);self.assertFalse(levels[-1])

    def test_large_packet_matches_split_packets(self):
        a=timer();b=timer()
        for t in (a,b):t.write(0xFFFFEC10,2,0xA538)
        a.advance_phi_cycles(2*513+1)
        for _ in range(2*513+1):b.advance_phi_cycles(1)
        self.assertEqual((a.tcnt,a.tcsr,a.overflow_count,a.phi_cycles),
                         (b.tcnt,b.tcsr,b.overflow_count,b.phi_cycles))

    def test_stop_resets_counter_but_explicit_phase_keeps_advancing(self):
        t=timer();t.advance_phi_cycles(1);t.write(0xFFFFEC10,2,0xA538)
        t.advance_phi_cycles(1);self.assertEqual(t.tcnt,1)
        t.write(0xFFFFEC10,2,0xA518);self.assertEqual(t.tcnt,0)
        t.advance_phi_cycles(100);self.assertEqual(t.tcnt,0)

    def test_counter_write_is_ordered_between_packets(self):
        t=timer();t.write(0xFFFFEC10,2,0xA538);t.advance_phi_cycles(10)
        self.assertEqual(t.tcnt,5);t.write(0xFFFFEC10,2,0x5A80)
        t.advance_phi_cycles(2);self.assertEqual(t.tcnt,0x81)

    def test_running_clock_change_and_watchdog_mode_rejected(self):
        t=timer();t.write(0xFFFFEC10,2,0xA538)
        for value in (0xA539,0xA578):
            state=(t.tcsr,t.tcnt)
            with self.assertRaises(BootStop):t.write(0xFFFFEC10,2,value)
            self.assertEqual((t.tcsr,t.tcnt),state)
        t.write(0xFFFFEC10,2,0xA518)
        with self.assertRaises(BootStop):t.write(0xFFFFEC10,2,0xA578)

    def test_clock_input_is_required_and_validated(self):
        t=WatchdogTimer(power_on=True,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):t.advance_phi_cycles(1)
        with self.assertRaises(BootStop):t.write(0xFFFFEC10,2,0xA538)
        t=timer()
        for value in (-1,True,1.5):
            with self.assertRaises(ValueError):t.advance_phi_cycles(value)
