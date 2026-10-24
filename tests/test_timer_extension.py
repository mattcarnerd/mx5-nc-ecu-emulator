import unittest
from test_sh2_branch import program
from test_module_interrupts import module_cpu
from ecu_workbench.core import ROMImage
from ecu_workbench.atu import *
from ecu_workbench.interrupts import IPRE_ADDRESS
from ecu_workbench.sh2_control import load_sr
from ecu_workbench.nc_boot import BootStop

class TimerExtensionTests(unittest.TestCase):
    def test_overflow_boundaries_packet_count_flag_clear_and_stopped(self):
        t=program(0x0009).bus.atu;t.write(TCNT,2,0xFFFE);t.write(TSTR,1,2);t.write(TIER,2,0x100)
        t.advance_ticks(1);self.assertEqual(t.read(TSR,2),0)
        t.advance_ticks(1);self.assertEqual(t.regs[TSR],0x100);self.assertTrue(t.interrupt_pending)
        t.write(TSR,2,0);self.assertTrue(t.interrupt_pending)
        t.read(TSR,2);t.write(TSR,2,0);self.assertFalse(t.interrupt_pending)
        t.advance_ticks(3*65536+7);self.assertEqual(t.read(TCNT,2),7)
        self.assertEqual(t.events[-1]['occurrences'],3)
        t.write(TSTR,1,0);old=t.regs[TCNT];t.advance_ticks(65536);self.assertEqual(t.regs[TCNT],old)

    def test_compare_overflow_packet_event_order_and_capture_flags(self):
        t=program(0x0009).bus.atu;t.write(TCNT,2,0xFFFF);t.write(GR,2,2);t.write(TIOR,1,1);t.write(TSTR,1,2)
        t.advance_ticks(3)
        self.assertEqual(t.regs[TSR],0x101)
        self.assertEqual([e['kind'] for e in t.events],['counter_overflow','compare_match'])
        self.assertEqual([e['tick'] for e in t.events],[1,3])
        t.read(TSR,2);t.write(TSR,2,1);self.assertEqual(t.regs[TSR],1)

    def test_ovi_vector_priority_firmware_ack_and_return(self):
        for priority,mask,expected in ((0,0,0),(5,5,0),(6,5,1)):
            d=module_cpu();data=bytearray(d.bus.image.data);data[0x1A0:0x1A4]=(0x500).to_bytes(4,'big')
            d.bus.image=ROMImage('synthetic',bytes(data));d.bus.write(IPRE_ADDRESS,2,priority<<12)
            load_sr(d,mask<<4);t=d.bus.atu;t.write(TIER,2,0x100);t.write(TSTR,1,2);t.advance_ticks(65536)
            sp=d.r[15];d.run(8 if expected else 1)
            self.assertEqual(d.interrupt_entries,expected)
            if expected:
                self.assertEqual(d.exception_events[0]['vector'],104);self.assertFalse(t.interrupt_pending)
                self.assertEqual(d.r[15],sp)

    def test_all_internal_divisors_and_packet_fraction(self):
        for first in range(32):
            for second in range(6):
                t=Atu1A(power_on=True,trace=[],stop_type=BootStop)
                t.write(PSCR,1,first);t.write(TCR,1,second);t.begin_clock_fixture(phase=0);t.write(TSTR,1,2)
                divisor=(first+1)*(1<<second)
                t.advance_phi_cycles(divisor-1);self.assertEqual(t.read(TCNT,2),0)
                t.advance_phi_cycles(1);self.assertEqual(t.read(TCNT,2),1)
                t.advance_phi_cycles(3*divisor+1);self.assertEqual(t.read(TCNT,2),(4*divisor+1)//divisor)
                self.assertIsNone(t.clock_report()['frequency_hz'])

    def test_clock_phase_stop_configuration_unknown_and_width(self):
        t=Atu1A(power_on=True,trace=[],stop_type=BootStop);t.write(PSCR,1,2)
        t.begin_clock_fixture(phase=0);t.advance_phi_cycles(2);t.write(TSTR,1,2)
        t.advance_phi_cycles(1);self.assertEqual(t.read(TCNT,2),1)
        with self.assertRaises(ValueError):t.advance_ticks(1)
        with self.assertRaises(BootStop):t.write(PSCR,1,3)
        for value in (32,255):
            with self.assertRaises(BootStop):Atu1A(power_on=True,trace=[],stop_type=BootStop).write(PSCR,1,value)
        with self.assertRaises(BootStop):t.write(PSCR,2,0)
        with self.assertRaises(ValueError):Atu1A(power_on=True,trace=[],stop_type=BootStop).begin_clock_fixture(phase=1)
        with self.assertRaises(BootStop):Atu1A(power_on=False,trace=[],stop_type=BootStop).begin_clock_fixture(phase=0)
        with self.assertRaises(ValueError):Atu1A(power_on=True,trace=[],stop_type=BootStop).advance_phi_cycles(1)
        b=program(0x0009).bus;b.write(PSCR,1,31);self.assertEqual(b.read(PSCR,1),31)
