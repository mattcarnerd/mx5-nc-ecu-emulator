import unittest
from ecu_workbench.atu import Atu1A,TSTR
from ecu_workbench.atu_channel10 import A,C,E,F,G,RLD,TCR,ICR,TSR
from ecu_workbench.nc_boot import BootStop

def startup(*,wrap=None,reload=2):
    a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
    a.channel10.set_initial_candidates({'A':1,'C':1,'F':1},zero_reload_policy=wrap)
    a.write(RLD,2,reload);a.begin_startup_timer_clock_fixture(phase=0)
    a.write(TSTR,1,0x80);return a

class Channel10InitialRuntimeTests(unittest.TestCase):
    def test_ambiguous_defaults_and_explicit_candidates(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for address,width in ((A,4),(C,2),(F,2)):
            with self.assertRaises(BootStop):a.read(address,width)
        with self.assertRaises(ValueError):a.channel10.set_initial_candidates({'A':1,'C':1,'F':1})
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        with self.assertRaises(ValueError):a.channel10.set_initial_candidates({'A':True,'C':1,'F':1})
        self.assertIsNone(a.channel10.regs[A])

    def test_nonzero_reload_and_old_state_correction(self):
        a=startup();a.advance_phi_cycles(1)
        self.assertEqual([a.channel10.regs[x] for x in (A,C,E,F,G)],[2,2,1,1,1])
        a.advance_phi_cycles(2)
        self.assertEqual([a.channel10.regs[x] for x in (A,C,E,F,G)],[4,2,2,1,2])
        a.advance_phi_cycles(1)
        self.assertEqual([a.channel10.regs[x] for x in (A,C,E,F,G)],[5,1,2,2,2])
        self.assertEqual(a.channel10.regs[TSR],0)

    def test_zero_reload_guard_is_atomic_across_all_counters(self):
        a=startup(reload=0);a.write(TSTR,1,0xFF)
        before=dict(a.regs);channel10=dict(a.channel10.regs)
        with self.assertRaises(BootStop):a.advance_phi_cycles(16)
        self.assertEqual(a.regs,before);self.assertEqual(a.channel10.regs,channel10)
        self.assertEqual(a.phi_cycles,0);self.assertEqual(a.events,[])

    def test_explicit_wrap_policy_and_packet_partition(self):
        a=startup(wrap='experimental-wrap16',reload=0)
        b=startup(wrap='experimental-wrap16',reload=0)
        a.advance_phi_cycles(17)
        for n in (1,3,5,8):b.advance_phi_cycles(n)
        self.assertEqual(a.channel10.regs,b.channel10.regs)
        self.assertEqual(a.channel10.regs[C],0xFFF0)
        self.assertEqual(a.channel10.regs[E],1);self.assertEqual(a.channel10.regs[F],1)
        self.assertEqual(a.clock_report()['channel10_zero_reload_policy'],'experimental-wrap16')

    def test_modes_widths_readonly_manual_and_phase_changes_guarded(self):
        a=startup()
        with self.assertRaises(BootStop):a.write(TCR,1,1)
        with self.assertRaises(BootStop):a.write(ICR,4,0)
        with self.assertRaises(BootStop):a.read(A,2)
        with self.assertRaises(BootStop):a.write(RLD,2,3)
        with self.assertRaises(BootStop):a.write(0xFFFFF40A,1,1)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(ValueError):m.channel10.set_initial_candidates({'A':1,'C':1,'F':1})
        with self.assertRaises(BootStop):m.begin_startup_timer_clock_fixture(phase=0)
