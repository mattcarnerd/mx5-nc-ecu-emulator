import unittest
from ecu_workbench.atu import Atu1A,TSTR,PSCR,ITVRR,TCNT0,TSR0,TIER0
from ecu_workbench.nc_boot import BootStop

def timer(prescale=0):
    a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
    a.write(PSCR,1,prescale);a.begin_counter0_clock_fixture(phase=0)
    return a

class Counter0RuntimeTests(unittest.TestCase):
    def test_phase_division_packet_partition_and_zero_packet(self):
        a=timer(3);b=timer(3)
        a.write(TSTR,1,1);b.write(TSTR,1,1)
        for count in (1,2,0,5,9):a.advance_phi_cycles(count)
        b.advance_phi_cycles(17)
        self.assertEqual(a.regs[TCNT0],4);self.assertEqual(a.regs[TCNT0],b.regs[TCNT0])
        self.assertEqual(a.phi_cycles,b.phi_cycles)

    def test_interval_rising_edges_repeat_and_read_before_clear(self):
        a=timer();a.write(ITVRR[0],1,1);a.write(TSTR,1,1)
        a.advance_phi_cycles(63);self.assertFalse(a.counter0.interval_pending)
        a.advance_phi_cycles(1);self.assertEqual(a.read(TSR0,2),0x20)
        a.write(TSR0,2,0);self.assertFalse(a.counter0.interval_pending)
        a.advance_phi_cycles(127);self.assertFalse(a.counter0.interval_pending)
        a.advance_phi_cycles(1);self.assertTrue(a.counter0.interval_pending)
        a.write(TSR0,2,0);self.assertTrue(a.counter0.interval_pending)
        a.read(TSR0,2);a.write(TSR0,2,0);self.assertFalse(a.counter0.interval_pending)

    def test_shared_interval_flags_and_overflow_are_distinct(self):
        a=timer()
        for address in ITVRR:a.write(address,1,0xF)
        a.write(TIER0,2,0x10);a.write(TCNT0,4,0xFFFFFFF0);a.write(TSTR,1,1)
        a.advance_phi_cycles(16)
        self.assertEqual(a.regs[TCNT0],0);self.assertTrue(a.counter0.overflow_pending)
        self.assertFalse(a.counter0.interval_pending)
        a.advance_phi_cycles(8192)
        self.assertEqual(a.regs[TSR0]&0xE0,0xE0)
        a.read(TSR0,2);a.write(TSR0,2,0x20)
        self.assertTrue(a.counter0.interval_pending);self.assertFalse(a.counter0.overflow_pending)

    def test_adc_other_starts_capture_and_phase_changes_remain_guarded(self):
        a=timer();before=dict(a.regs)
        for address,width,value in ((ITVRR[0],1,0x10),(TIER0,2,1),(TSTR,1,3),(TSTR,1,0xFF)):
            with self.assertRaises(BootStop):a.write(address,width,value)
        self.assertEqual(a.regs,before)
        with self.assertRaises(BootStop):a.write(PSCR,1,1)
        with self.assertRaises(ValueError):a.begin_counter0_clock_fixture(phase=0)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.begin_counter0_clock_fixture(phase=0)

    def test_unimplemented_cpu_route_stops_when_unmasked(self):
        from test_sh2_branch import program
        c=program(0x0009);a=c.bus.atu
        a.begin_counter0_clock_fixture(phase=0);a.write(ITVRR[0],1,1)
        a.write(TSTR,1,1);a.advance_phi_cycles(64)
        c.bus.ipr[0xFFFFED04]=0xF0;c.known_sr_mask|=0xF0;c.known_sr_value&=~0xF0
        r=c.run(1)
        self.assertEqual(r['stop']['reason'],'unsupported_interrupt_source')
        self.assertEqual(r['completed_instructions'],0);self.assertEqual(r['interrupt_entries'],0)
