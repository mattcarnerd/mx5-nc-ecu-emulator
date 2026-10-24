import json,tempfile,unittest
from io import StringIO
from contextlib import redirect_stdout
from ecu_workbench.integration_fixture import run_integration_fixture,build_integration_rom,main
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.trace_review import summarise,LF9VEB_SHA256
from ecu_workbench.share_report import make_shareable_blocker_report
from test_share_report import detailed
from test_sh2_branch import program

class IntegrationFixtureTests(unittest.TestCase):
    def run_fixture(self,**changes):
        args=dict(voltage=1,reference=5,adc_delay=8,capture_delay=2,capture_counter_ticks=17)
        args.update(changes);return run_integration_fixture(**args)

    def test_nested_irq_firmware_capture_adc_gpio_and_determinism(self):
        first=self.run_fixture();self.assertEqual(first,self.run_fixture())
        self.assertTrue(first['fixture_passed']);self.assertFalse(first['boot_complete'])
        self.assertFalse(first['manufacturer_firmware_used']);self.assertFalse(first['validated_NC_pattern'])
        self.assertEqual(first['capture_word'],17);self.assertEqual(first['adc_word'],204<<6)
        self.assertTrue(first['stack_restored']);self.assertEqual(first['handler_counts'],{'IMI1A':1,'ADI0':1})
        events=first['timeline']
        self.assertEqual([e['sequence'] for e in events],list(range(len(events))))
        self.assertEqual([e['tick'] for e in events],sorted(e['tick'] for e in events))
        self.assertTrue(all(e['time_unit']=='completed_instruction_ticks' for e in events))
        self.assertEqual([e['source'] for e in events if e['kind']=='exception_entry'],['IMI1A','ADI0'])
        self.assertEqual([e['active_source'] for e in events if e['kind']=='exception_return'],['ADI0','IMI1A'])
        self.assertEqual([e['latch_value'] for e in events if e['kind']=='gpio_command' and e['active_source']=='ADI0'],[19])
        self.assertEqual(first['timeline_events_dropped'],0)

    def test_explicit_inputs_change_isr_results_and_commands(self):
        r=self.run_fixture(voltage=4,capture_counter_ticks=123)
        self.assertTrue(r['fixture_passed']);self.assertEqual(r['capture_word'],123)
        self.assertEqual(r['adc_word'],819<<6)
        adc_commands=[e['latch_value'] for e in r['timeline'] if e['kind']=='gpio_command' and e['active_source']=='ADI0']
        self.assertEqual(adc_commands,[12])
        capture=next(e for e in r['timeline'] if e['kind']=='input_capture_A')
        self.assertEqual(capture['counter_tick'],123)
        self.assertNotEqual(capture['tick'],capture['counter_tick'])

    def test_simultaneous_requests_choose_configured_priority_and_budget_does_not_prove_completion(self):
        r=self.run_fixture(adc_delay=2,capture_delay=2)
        self.assertTrue(r['fixture_passed'])
        entries=[e['source'] for e in r['timeline'] if e['kind']=='exception_entry']
        self.assertEqual(entries,['ADI0','IMI1A'])
        short=self.run_fixture(max_steps=1)
        self.assertFalse(short['fixture_passed']);self.assertEqual(short['interrupt_entries'],0)
        self.assertEqual(short['scheduled_peripheral_events'],1)

    def test_injected_peripheral_provenance_cannot_be_reference(self):
        for field in ('explicit_peripheral_inputs','scheduled_peripheral_events'):
            d=detailed();d['nc_boot'][field]=1
            r=make_shareable_blocker_report(d)
            self.assertTrue(r['injected_peripheral_scenario']);self.assertFalse(r['reference_lf9veb_scenario'])
            d['nc_boot'][field]=True
            with self.assertRaises(ValueError):make_shareable_blocker_report(d)
        baseline=capture_boot_baseline(build_integration_rom(),nmi_high=True)
        baseline['rom']['sha256']=LF9VEB_SHA256
        baseline['result']['scheduled_peripheral_events']=1
        self.assertFalse(summarise(baseline)['reference_scenario'])
        self.assertTrue(summarise(baseline)['injected_peripheral_scenario'])
        cpu=program(0x0009);cpu.bus.atu.advance_ticks(0);cpu.bus.atu.set_pin(False)
        self.assertEqual(cpu.run(1)['explicit_peripheral_inputs'],2)

    def test_validation_and_source_cli(self):
        for change in ({'capture_delay':0},{'capture_counter_ticks':True},{'max_steps':0},{'reference':0}):
            with self.assertRaises(ValueError):self.run_fixture(**change)
        out=StringIO()
        with redirect_stdout(out):code=main(['--voltage','1','--reference','5','--adc-delay','8',
            '--capture-delay','2','--capture-counter-ticks','17'])
        self.assertEqual(code,0);self.assertTrue(json.loads(out.getvalue())['fixture_passed'])
