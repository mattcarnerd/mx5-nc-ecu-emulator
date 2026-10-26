import unittest
from ecu_workbench.atu import Atu1A,TSTR,TSTR2,TSTR3,TCR11,PSCR
from ecu_workbench.atu_aux_timers import MEMBERS
from ecu_workbench.nc_boot import BootStop

def timer():
    a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
    a.channel10.set_initial_candidates({'A':1,'C':1,'F':1},zero_reload_policy='experimental-wrap16')
    a.begin_startup_timer_clock_fixture(phase=0);return a

class AuxiliaryTimerRuntimeTests(unittest.TestCase):
    def test_reset_differences_all_independent_clocks_and_packet_partition(self):
        a=timer();b=timer()
        for t in (a,b):t.write(TSTR2,1,0xFF);t.write(TSTR3,1,1)
        a.advance_phi_cycles(17)
        for n in (1,2,5,9):b.advance_phi_cycles(n)
        for address in MEMBERS:
            self.assertEqual(a.read(address,2),17 if address==0xFFFFF5C0 else 18)
            self.assertEqual(a.regs[address],b.regs[address])
        self.assertEqual(a.events,[])

    def test_stop_resume_phase_and_tstr3_reserved(self):
        a=timer();a.write(TSTR2,1,1);a.advance_phi_cycles(4)
        a.write(TSTR2,1,0);a.advance_phi_cycles(5);a.write(TSTR2,1,1);a.advance_phi_cycles(1)
        self.assertEqual(a.regs[0xFFFFF500],6);self.assertEqual(a.regs[0xFFFFF502],1)
        with self.assertRaises(BootStop):a.write(TSTR3,1,2)
        self.assertEqual(a.regs[TSTR3],0)

    def test_compare_boundary_is_atomic_across_all_timer_banks(self):
        a=timer();a.write(0xFFFFF500,2,0xFFFE)
        a.write(TSTR2,1,1);a.write(TSTR,1,0xFF)
        before=dict(a.regs);c10=dict(a.channel10.regs)
        with self.assertRaises(BootStop):a.advance_phi_cycles(1)
        self.assertEqual(a.regs,before);self.assertEqual(a.channel10.regs,c10)
        self.assertEqual(a.phi_cycles,0);self.assertEqual(a.events,[])

    def test_active_writes_clock_modes_unknown_and_widths_guarded(self):
        a=timer();a.write(TSTR2,1,1)
        with self.assertRaises(BootStop):a.write(0xFFFFF500,2,0)
        with self.assertRaises(BootStop):a.write(0xFFFFF521,1,1)
        with self.assertRaises(BootStop):a.write(0xFFFFF406,1,1)
        with self.assertRaises(BootStop):a.write(0xFFFFF500,1,0)
        a.write(TSTR2,1,0)
        with self.assertRaises(BootStop):a.write(TCR11,1,1)
        a.aux_timers.comparators[0xFFFFF5C2]=None
        with self.assertRaises(BootStop):a.write(TSTR3,1,1)
