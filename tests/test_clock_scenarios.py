import json,os,tempfile,unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from test_sh2_branch import program
from test_share_report import detailed
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import NCBootDiagnostic,diagnose_nc_reset
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.trace_review import summarise,LF9VEB_SHA256
from ecu_workbench.boot_presenter import present_reset_diagnostic
from ecu_workbench.cli import main


def clock_rom():
    d=program(0xD103,0x9204,0x2121,0x0009);data=bytearray(d.bus.image.data)
    data[0x10E:0x110]=bytes.fromhex('A53C');data[0x110:0x114]=(0xFFFFEC10).to_bytes(4,'big')
    return ROMImage('synthetic',bytes(data))

class ClockScenarioTests(unittest.TestCase):
    def test_unknown_refuses_running_but_explicit_policy_advances(self):
        d=NCBootDiagnostic(clock_rom());r=d.run(4)
        self.assertEqual(r['stop']['reason'],'unsupported_peripheral_mode')
        d=NCBootDiagnostic(clock_rom(),phi_cycles_per_instruction=512);r=d.run(4)
        self.assertEqual(r['stop']['reason'],'instruction_limit');self.assertEqual(d.bus.watchdog.tcnt,2)
        self.assertEqual(r['supplied_phi_cycles'],2048);self.assertTrue(r['conditional_clock_scenario'])
        self.assertIsNone(r['virtual_time']['cpu_cycles']);self.assertIsNone(r['virtual_time']['seconds'])
        self.assertFalse(r['boot_complete'])

    def test_timer_irq_is_modelled_from_declared_clock_not_manual_injection(self):
        d=NCBootDiagnostic(clock_rom(),phi_cycles_per_instruction=131072);r=d.run(4)
        self.assertTrue(d.interval_request);self.assertEqual(r['explicit_interrupt_requests'],0)
        self.assertEqual(r['interrupt_inputs'][0]['provenance'],'modelled_timer_explicit_clock_scenario')
        self.assertEqual(d.bus.watchdog.overflow_count,2)

    def test_invalid_policies_and_failed_image_metadata(self):
        for n in (0,-1,True,1.5,1000001):
            with self.assertRaises(ValueError):diagnose_nc_reset(clock_rom(),phi_cycles_per_instruction=n)
        r=diagnose_nc_reset(ROMImage('invalid',b''),phi_cycles_per_instruction=1)
        self.assertTrue(r['conditional_clock_scenario']);self.assertFalse(r['boot_complete'])

    def test_clock_assumptions_cannot_be_reference_or_hidden(self):
        d=detailed();d['nc_boot'].update(phi_cycles_per_instruction=1,conditional_clock_scenario=True,
                                         conditional_hardware_scenario=True)
        d['diagnostic_settings']['phi_cycles_per_instruction']=1
        shared=make_shareable_blocker_report(d)
        self.assertFalse(shared['reference_lf9veb_scenario']);self.assertTrue(shared['conditional_hardware_scenario'])
        self.assertTrue(shared['conditional_clock_scenario']);self.assertEqual(shared['phi_fixture_origin'],0)
        del d['diagnostic_settings']['phi_cycles_per_instruction']
        self.assertEqual(make_shareable_blocker_report(d)['phi_cycles_per_instruction'],1)
        d['diagnostic_settings']['phi_cycles_per_instruction']=None
        with self.assertRaises(ValueError):make_shareable_blocker_report(d)
        self.assertTrue(make_shareable_blocker_report(detailed())['reference_lf9veb_scenario'])

    def test_baseline_presenter_and_cli_keep_conditional_policy(self):
        b=capture_boot_baseline(clock_rom(),nmi_high=True,max_steps=300,phi_cycles_per_instruction=1)
        b['rom']['sha256']=LF9VEB_SHA256
        self.assertFalse(summarise(b)['reference_scenario'])
        r=diagnose_nc_reset(clock_rom(),max_steps=4,phi_cycles_per_instruction=1)
        self.assertIn('Conditional',present_reset_diagnostic(r)['status'])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'synthetic.bin';p.write_bytes(clock_rom().data)
            for baseline in (False,True):
                args=['--rom',str(p),'--steps','4','--phi-cycles-per-instruction','1']
                if baseline:args+=['--baseline']
                out=StringIO()
                with redirect_stdout(out):self.assertEqual(main(args),0)
                report=json.loads(out.getvalue())
                self.assertEqual(report['phi_cycles_per_instruction'] if baseline else report['nc_boot']['phi_cycles_per_instruction'],1)

    def test_gui_keeps_executed_clock_setting_after_edits(self):
        from ecu_workbench.gui import Workbench
        class Var:
            def __init__(self,v):self.v=v
            def get(self):return self.v
            def set(self,v):self.v=v
        ui=SimpleNamespace(rom=clock_rom(),reset=Var('power'),nmi=Var('high'),steps=Var('4'),
            hudi_scenario=Var('Unknown (default)'),phi_cycles_per_instruction=Var('1'),
            port_b_pins=Var(''),port_c_pins=Var(''),port_d_pins=Var(''),port_b_mask=Var('0xFFFF'),
            port_c_mask=Var('0x1F'),port_d_mask=Var('0xFFFF'),status=Var(''),summary='s',blocker='b',trace='t',peripherals='p')
        ui._set=lambda *a:None;Workbench.run_boot(ui);ui.phi_cycles_per_instruction.set('')
        self.assertEqual(make_shareable_blocker_report(ui.report)['phi_cycles_per_instruction'],1)

    def test_optional_original_reference_plus_declared_clock_scenarios(self):
        source=os.environ.get('MX5_NC_TEST_ROM')
        if not source:self.skipTest('Private original-reference ROM unavailable')
        rom=ROMImage('private',Path(source).read_bytes())
        if rom.sha256!=LF9VEB_SHA256:self.skipTest('Different private ROM hash')
        for hudi in ('unknown','trst-reset','transfer-complete'):
            for n in (None,1):
                r=diagnose_nc_reset(rom,max_steps=300,nmi_high=True,hudi_scenario=hudi,phi_cycles_per_instruction=n)
                self.assertEqual(r['conditional_clock_scenario'],n is not None);self.assertFalse(r['boot_complete'])
                baseline=188 if hudi=='unknown' else 225 if n is None else 233
                self.assertGreaterEqual(r['executed_instructions'],baseline)
