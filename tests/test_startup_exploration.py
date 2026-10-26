import unittest
from test_sh2_branch import program
from ecu_workbench.startup_exploration import explore_startup
from ecu_workbench.nc_boot import BootStop

class StartupExplorationTests(unittest.TestCase):
    def test_explicit_envelope_retains_assumptions_and_excludes_paths(self):
        rom=program(0x0009).bus.image
        r=explore_startup(rom,prior_ram_word=0xFFFFFFFF,phi_cycles_per_instruction=4,max_steps=1)
        self.assertEqual(r['schema'],'nc-ecu-startup-exploration-v1')
        self.assertEqual(r['assumptions']['prior_ram_words'][0]['value'],'0xFFFFFFFF')
        self.assertEqual(r['assumptions']['phi_cycles_per_instruction'],4)
        self.assertIsNone(r['assumptions']['port_b_pins'])
        self.assertFalse(r['initialization_verified']);self.assertEqual(r['interrupt_entries'],0)
        self.assertNotIn('trace',r);self.assertNotIn('image',r)
        self.assertNotIn('rom',r['assumptions'])

    def test_invalid_hypotheses_rejected(self):
        rom=program(0x0009).bus.image
        for value in (None,True,-1,0x100000000):
            with self.assertRaises(ValueError):
                explore_startup(rom,prior_ram_word=value,phi_cycles_per_instruction=4,max_steps=1)
        for value in (True,-1,0x10000):
            with self.assertRaises(ValueError):
                explore_startup(rom,prior_ram_word=0,phi_cycles_per_instruction=4,max_steps=1,port_b_pins=value)

    def test_default_cpu_ram_still_unknown_and_experiment_not_mutating_rom(self):
        c=program(0x0009);original=c.bus.image.data
        explore_startup(c.bus.image,prior_ram_word=0,phi_cycles_per_instruction=4,max_steps=1)
        self.assertEqual(c.bus.image.data,original)
        with self.assertRaises(BootStop):c.bus.read(0xFFFFBFFC,4)

    def test_exploration_is_not_accepted_as_a_reset_baseline(self):
        from ecu_workbench.trace_review import summarise
        r=explore_startup(program(0x0009).bus.image,prior_ram_word=0,phi_cycles_per_instruction=4,max_steps=1)
        with self.assertRaises(ValueError):summarise(r)
        for phi in (None,True,0,1000001):
            with self.assertRaises(ValueError):
                explore_startup(program(0x0009).bus.image,prior_ram_word=0,phi_cycles_per_instruction=phi,max_steps=1)

    def test_extra_pin_hypotheses_preserved_and_validated(self):
        rom=program(0x0009).bus.image
        r=explore_startup(rom,prior_ram_word=0,phi_cycles_per_instruction=16,max_steps=1,
                          port_c_pins=0x1F,port_d_pins=0xFFFF)
        self.assertEqual(r['assumptions']['port_c_pins'],'0x001F')
        self.assertEqual(r['assumptions']['port_d_pins'],'0xFFFF')
        self.assertTrue(r['diagnostic']['settings']['explicit_pin_values'])
        for name,bad in (('port_c_pins',0x20),('port_d_pins',0x10000),('port_c_pins',True),('port_d_pins',-1)):
            with self.assertRaises(ValueError):
                explore_startup(rom,prior_ram_word=0,phi_cycles_per_instruction=16,max_steps=1,**{name:bad})

    def test_pin_defaults_are_still_unsupplied(self):
        r=explore_startup(program(0x0009).bus.image,prior_ram_word=0,phi_cycles_per_instruction=4,max_steps=1)
        for name in ('port_b_pins','port_c_pins','port_d_pins'):
            self.assertIsNone(r['assumptions'][name])
        self.assertFalse(r['diagnostic']['settings']['explicit_pin_values'])
