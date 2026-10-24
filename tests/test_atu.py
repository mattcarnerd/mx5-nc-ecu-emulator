import unittest
from test_sh2_branch import program
from ecu_workbench.atu import *
from ecu_workbench.nc_boot import BootStop

class AtuTests(unittest.TestCase):
    def timer(self):return program(0x0009).bus.atu
    def test_compare_wrap_interrupt_and_read_before_clear(self):
        t=self.timer();t.write(GR,2,2);t.write(TIOR,1,1);t.write(TIER,2,1);t.write(TSTR,1,2)
        t.advance_ticks(1);self.assertEqual(t.read(TSR,2),0)
        t.advance_ticks(1);self.assertTrue(t.interrupt_pending)
        t.write(TSR,2,0);self.assertTrue(t.interrupt_pending)
        self.assertEqual(t.read(TSR,2),1);t.write(TSR,2,0);self.assertFalse(t.interrupt_pending)
        t.advance_ticks(65536);self.assertEqual(t.read(TCNT,2),2);self.assertTrue(t.interrupt_pending)
        self.assertEqual(t.events[-1]['kind'],'compare_match')

    def test_capture_edge_filter_and_read_only(self):
        for mode,levels,captures in ((5,(False,True,False),1),(6,(True,False,True),1),(7,(False,True,False),2)):
            t=self.timer();t.write(TIOR,1,mode);t.write(TSTR,1,2);t.advance_ticks(11)
            for level in levels:t.set_pin(level)
            self.assertEqual(t.read(GR,2),11);self.assertEqual(len(t.events),captures)
            with self.assertRaises(BootStop):t.write(GR,2,0)

    def test_reset_width_clock_and_stopped_counter(self):
        t=self.timer();self.assertEqual(t.read(GR,2),0xFFFF)
        t.advance_ticks(100);self.assertEqual(t.read(TCNT,2),0)
        t=self.timer();t.write(TSTR,1,2)
        with self.assertRaises(BootStop):t.read(TCNT,2)
        for address,width,value in ((TCNT,1,0),(TCNT+1,2,0),(TSTR,1,4),(TIOR,1,8),(TCR,1,1)):
            with self.assertRaises(BootStop):t.write(address,width,value)
        t.regs[TIER]=None;self.assertIsNone(t.interrupt_pending)
        t.regs[TCNT]=None
        with self.assertRaises(BootStop):t.advance_ticks(1)
        for count in (-1,True,1.5):
            with self.assertRaises(ValueError):self.timer().advance_ticks(count)
