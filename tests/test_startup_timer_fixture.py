import unittest
from test_sh2_branch import program
from ecu_workbench.startup_exploration import explore_startup
from ecu_workbench.startup_timer_fixture import bind_startup_timer_fixture,normalize_startup_timer_fixture
from ecu_workbench.atu import TSTR,TCR1B
from ecu_workbench.nc_boot import BootStop

FIXTURE={'p_phi_cycles_per_instruction':16,'channel10_initial_candidates':{'A':1,'C':1,'F':1},'zero_reload_policy':'experimental-wrap16'}

def start_rom():
    return program(0x9304,0xE4FF,0x2340,0x0009,0x0009,0x0009,0xF401).bus.image

class StartupTimerFixtureTests(unittest.TestCase):
    def test_defaults_do_not_bind_or_accept_broad_start(self):
        r=explore_startup(start_rom(),prior_ram_word=0,phi_cycles_per_instruction=16,max_steps=4)
        self.assertIsNone(r['startup_timer_binding'])
        self.assertEqual(r['diagnostic']['completed_instructions'],2)
        self.assertEqual(r['diagnostic']['stop']['reason'],'unsupported_peripheral_mode')

    def test_first_start_binding_and_exact_envelope_policies(self):
        r=explore_startup(start_rom(),prior_ram_word=0,phi_cycles_per_instruction=16,max_steps=4,startup_timer_fixture=FIXTURE)
        self.assertEqual(r['diagnostic']['completed_instructions'],4)
        self.assertEqual(r['assumptions']['startup_timer_fixture'],FIXTURE)
        self.assertEqual(r['startup_timer_binding']['bound_tick'],2)
        self.assertEqual(r['startup_timer_binding']['completed_packets'],2)
        self.assertEqual(r['atu_clock_fixture']['supplied_phi_cycles'],32)
        self.assertEqual(r['atu_clock_fixture']['channel10_zero_reload_policy'],'experimental-wrap16')
        self.assertEqual(r['interrupt_entries'],0);self.assertFalse(r['initialization_verified'])

    def test_no_zero_reload_policy_stops_packet_without_fake_completion(self):
        f={**FIXTURE,'zero_reload_policy':None}
        r=explore_startup(start_rom(),prior_ram_word=0,phi_cycles_per_instruction=16,max_steps=4,startup_timer_fixture=f)
        self.assertEqual(r['diagnostic']['completed_instructions'],3)
        self.assertEqual(r['startup_timer_binding']['completed_packets'],0)
        self.assertEqual(r['atu_clock_fixture']['supplied_phi_cycles'],0)
        self.assertEqual(r['diagnostic']['stop']['reason'],'unsupported_peripheral_mode')
        self.assertIsNone(r['diagnostic']['next_dependency']['opcode'])

    def test_rejected_start_does_not_bind_or_schedule(self):
        c=program(0x0009);state=bind_startup_timer_fixture(c,FIXTURE)
        a=c.bus.atu;a.write(TCR1B,1,6);before=dict(a.regs)
        with self.assertRaises(BootStop):a.write(TSTR,1,0xFF)
        self.assertIsNone(state['bound_tick']);self.assertIsNone(a.clock_mode)
        self.assertEqual(c.scheduled_peripheral_events,0);self.assertEqual(a.regs,before)

    def test_invalid_or_duplicate_fixtures_are_rejected(self):
        for bad in ({}, {**FIXTURE,'p_phi_cycles_per_instruction':True},
                    {**FIXTURE,'zero_reload_policy':'guess'},
                    {**FIXTURE,'channel10_initial_candidates':{'A':1,'C':1}}):
            with self.assertRaises(ValueError):normalize_startup_timer_fixture(bad)
        c=program(0x0009);bind_startup_timer_fixture(c,FIXTURE)
        with self.assertRaises(ValueError):bind_startup_timer_fixture(c,FIXTURE)
