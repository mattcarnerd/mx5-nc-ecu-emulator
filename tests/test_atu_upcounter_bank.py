import unittest
from ecu_workbench.atu import Atu1A,TSTR,PSCR,TCNT,TCNT0
from ecu_workbench.atu_upcounter_bank import MEMBERS
from ecu_workbench.nc_boot import BootStop

def bank():
    a=Atu1A(power_on=True,trace=[],stop_type=BootStop);a.write(PSCR,1,4)
    a.write(0xFFFFF45D,1,4)
    for address,(tcr,_,_) in MEMBERS.items():a.write(tcr,1,5 if address==0xFFFFF4E0 else 4)
    a.begin_upcounter_bank_clock_fixture(phase=0);return a

class UpcounterBankTests(unittest.TestCase):
    def test_independent_divisors_and_partitioned_packets(self):
        a=bank();b=bank();a.write(TSTR,1,0x7F);b.write(TSTR,1,0x7F)
        a.advance_phi_cycles(1600)
        for count in (1,79,320,1200):b.advance_phi_cycles(count)
        self.assertEqual(a.regs[TCNT0],320);self.assertEqual(a.regs[TCNT],20)
        for address in MEMBERS:
            self.assertEqual(a.read(address,2),10 if address==0xFFFFF4E0 else 20)
            self.assertEqual(a.regs[address],b.regs[address])
        self.assertEqual(a.events,b.events)

    def test_stop_and_resume_keep_explicit_global_phase(self):
        a=bank();a.write(TSTR,1,8);a.advance_phi_cycles(79)
        self.assertEqual(a.regs[0xFFFFF442],0)
        a.write(TSTR,1,0);a.advance_phi_cycles(80)
        a.write(TSTR,1,8);a.advance_phi_cycles(1)
        self.assertEqual(a.regs[0xFFFFF442],1)

    def test_first_unimplemented_event_is_atomic_across_bank(self):
        a=bank();a.write(0xFFFFF442,2,0xFFFE);a.write(TSTR,1,0x7F)
        before=dict(a.regs);phase=a.phi_cycles;events=list(a.events)
        with self.assertRaises(BootStop):a.advance_phi_cycles(80)
        self.assertEqual(a.regs,before);self.assertEqual(a.phi_cycles,phase)
        self.assertEqual(a.events,events);self.assertEqual(a.counter0.counter_ticks,0)

    def test_channel10_external_clocks_running_writes_and_unknowns_guarded(self):
        a=bank();before=dict(a.regs)
        with self.assertRaises(BootStop):a.write(TSTR,1,0xFF)
        self.assertEqual(a.regs,before)
        a.write(TSTR,1,8)
        with self.assertRaises(BootStop):a.write(0xFFFFF442,2,0)
        with self.assertRaises(BootStop):a.write(0xFFFFF45C,1,5)
        a.write(TSTR,1,0)
        with self.assertRaises(BootStop):a.write(0xFFFFF45C,1,5)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.begin_upcounter_bank_clock_fixture(phase=0)
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        a.write(0xFFFFF45C,1,6);a.begin_upcounter_bank_clock_fixture(phase=0)
        with self.assertRaises(BootStop):a.write(TSTR,1,8)
