import unittest
from ecu_workbench.watchdog import WatchdogTimer
from ecu_workbench.nc_boot import BootStop
from ecu_workbench.startup_exploration import explore_startup
from test_sh2_branch import program

class OrderedStopTests(unittest.TestCase):
    def timer(self, policy=False):
        w=WatchdogTimer(power_on=True,trace=[],stop_type=BootStop,clock_supplied=True)
        w.experimental_ordered_stop=policy
        w.write(0xFFFFEC10,2,0xA53C)
        w.advance_phi_cycles(1024)
        return w

    def test_default_rejects_combined_stop_change_without_mutation(self):
        w=self.timer();before=(w.tcsr,w.tcnt,w.phi_cycles)
        with self.assertRaises(BootStop):w.write(0xFFFFEC10,2,0xA518)
        self.assertEqual((w.tcsr,w.tcnt,w.phi_cycles),before)
        self.assertEqual(w.ordered_stop_count,0)

    def test_opt_in_stops_resets_counter_and_retains_read_before_clear(self):
        w=self.timer(True);w.tcsr|=0x80
        w.write(0xFFFFEC10,2,0xA518)
        self.assertEqual(w.tcsr,0x98);self.assertEqual(w.tcnt,0)
        self.assertEqual(w.ordered_stop_count,1)
        w.read(0xFFFFEC10,1);w.write(0xFFFFEC10,2,0xA518)
        self.assertEqual(w.tcsr,0x18)
        w.advance_phi_cycles(10000);self.assertEqual(w.tcnt,0)
        self.assertEqual(w.ordered_stop_count,1)

    def test_experiment_does_not_allow_live_clock_or_mode_change(self):
        for value in (0xA538,0xA558):
            w=self.timer(True)
            with self.assertRaises(BootStop):w.write(0xFFFFEC10,2,value)
            self.assertEqual(w.ordered_stop_count,0)

    def test_generated_program_and_provenance(self):
        words=[0x930E,0x940E,0x2341,0x940D,0x2341,0x0009]+[0x0009]*10+[0xEC10,0xA53C,0xA518]
        rom=program(*words).bus.image
        for policy in (False,True):
            r=explore_startup(rom,prior_ram_word=0,phi_cycles_per_instruction=16,max_steps=6,
                              experimental_wdt_ordered_stop=policy)
            self.assertEqual(r['assumptions']['experimental_wdt_ordered_stop'],policy)
            self.assertEqual(r['diagnostic']['experimental_wdt_ordered_stop'],policy)
            self.assertEqual(r['wdt_ordered_stop_count'],int(policy))
            self.assertEqual(r['diagnostic']['completed_instructions'],6 if policy else 4)
            self.assertFalse(r['initialization_verified'])
        with self.assertRaises(ValueError):
            explore_startup(rom,prior_ram_word=0,phi_cycles_per_instruction=16,experimental_wdt_ordered_stop=1)

    def test_reducer_rejects_lost_or_inconsistent_policy(self):
        from ecu_workbench.share_report import make_shareable_blocker_report
        c=program(0x0009);r=c.run(1)
        r['experimental_wdt_ordered_stop']=False;r['wdt_ordered_stop_count']=1
        with self.assertRaises(ValueError):
            make_shareable_blocker_report({'image':{'sha256':c.bus.image.sha256},'nc_boot':r})
        r['experimental_wdt_ordered_stop']=True
        with self.assertRaises(ValueError):
            make_shareable_blocker_report({'image':{'sha256':c.bus.image.sha256},'nc_boot':r})
