"""B40 conditional assumptions must survive every frontend/export path."""
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from test_port_l import image
from test_share_report import detailed
from ecu_workbench.hudi import HUDI_SCENARIOS,HUDI_SCENARIO_LABELS
from ecu_workbench.nc_boot import BootBus,BootStop,diagnose_nc_reset
from ecu_workbench.core import ROMImage
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.trace_review import summarise,LF9VEB_SHA256
from ecu_workbench.boot_presenter import present_reset_diagnostic
from ecu_workbench.cli import main

class ScenarioTests(unittest.TestCase):
    def test_bus_scenarios_and_reset_independence(self):
        for power in (True,False):
            for scenario,value in (('unknown',None),('trst-reset',0x0B01),('transfer-complete',0x0B00)):
                b=BootBus(image(),power_on=power,hudi_scenario=scenario)
                if value is None:
                    with self.assertRaises(BootStop):b.read(0xFFFFF7C2,2)
                else:self.assertEqual(b.read(0xFFFFF7C2,2),value)
                self.assertEqual(b.hudi.scenario,scenario)

    def test_repeated_api_runs_and_invalid_image_keep_scenario(self):
        for scenario in HUDI_SCENARIOS:
            a=diagnose_nc_reset(image(),max_steps=1,hudi_scenario=scenario)
            b=diagnose_nc_reset(image(),max_steps=1,hudi_scenario=scenario)
            self.assertEqual(a,b)
            for r in (a,diagnose_nc_reset(ROMImage('invalid',b''),hudi_scenario=scenario)):
                self.assertEqual(r['hudi_scenario'],scenario)
                self.assertEqual(r['conditional_hardware_scenario'],scenario!='unknown')
                self.assertFalse(r['boot_complete'])

    def test_invalid_scenarios_are_rejected(self):
        for v in ('bad',True,None,12,{},'private path'):
            with self.assertRaises(ValueError):diagnose_nc_reset(image(),hudi_scenario=v)
            with self.assertRaises(ValueError):capture_boot_baseline(image(),hudi_scenario=v)

    def test_shareable_classification_preserves_assumptions(self):
        for scenario in HUDI_SCENARIOS:
            d=detailed();d['nc_boot']['hudi_scenario']=scenario
            d['nc_boot']['conditional_hardware_scenario']=scenario!='unknown'
            d['diagnostic_settings']['hudi_scenario']=scenario
            out=make_shareable_blocker_report(d)
            self.assertEqual(out['settings']['hudi_scenario'],scenario)
            self.assertEqual(out['reference_lf9veb_scenario'],scenario=='unknown')
            self.assertEqual(out['conditional_hardware_scenario'],scenario!='unknown')
            if scenario!='unknown':self.assertEqual(out['assessment'],'conditional_hardware_scenario')
            self.assertFalse(out['boot_complete'])
            self.assertNotIn('PRIVATE-DO-NOT-EXPORT',json.dumps(out))
            # Missing settings must fall back to the actual run, never to unknown.
            del d['diagnostic_settings']['hudi_scenario']
            self.assertEqual(make_shareable_blocker_report(d)['hudi_scenario'],scenario)
        self.assertTrue(make_shareable_blocker_report(detailed())['reference_lf9veb_scenario'])

    def test_contradictory_metadata_cannot_hide_an_assumption(self):
        for mutate in (
            lambda d:d['diagnostic_settings'].update(hudi_scenario='unknown'),
            lambda d:d['nc_boot'].pop('hudi_scenario'),
            lambda d:d['nc_boot'].update(conditional_hardware_scenario=False),
            lambda d:d['diagnostic_settings'].update(hudi_scenario='bad'),
        ):
            d=detailed();d['nc_boot'].update(hudi_scenario='trst-reset',conditional_hardware_scenario=True)
            d['diagnostic_settings']['hudi_scenario']='trst-reset';mutate(d)
            with self.assertRaises(ValueError):make_shareable_blocker_report(d)

    def test_baseline_reviewer_and_presenter_mark_conditional(self):
        for scenario in HUDI_SCENARIOS:
            b=capture_boot_baseline(image(),max_steps=300,nmi_high=True,hudi_scenario=scenario)
            b['rom']['sha256']=LF9VEB_SHA256  # classification fixture only
            result=summarise(b)
            self.assertEqual(result['reference_scenario'],scenario=='unknown')
            r=diagnose_nc_reset(image(),max_steps=1,hudi_scenario=scenario)
            shown=present_reset_diagnostic(r)
            self.assertEqual(shown['summary']['hudi_scenario'],scenario)
            self.assertEqual('Conditional' in shown['status'],scenario!='unknown')
            self.assertFalse(shown['summary']['boot_complete'])

    def test_cli_detailed_and_baseline_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'synthetic.bin';p.write_bytes(image().data)
            for scenario in HUDI_SCENARIOS:
                for baseline in (False,True):
                    args=['--rom',str(p),'--steps','1','--nmi','high','--hudi-scenario',scenario]
                    if baseline:args+=['--baseline']
                    out=StringIO()
                    with redirect_stdout(out):self.assertEqual(main(args),0)
                    d=json.loads(out.getvalue())
                    self.assertEqual(d['hudi_scenario'] if baseline else d['nc_boot']['hudi_scenario'],scenario)
                    if not baseline:
                        self.assertEqual(make_shareable_blocker_report(d)['hudi_scenario'],scenario)

    def test_gui_records_actual_selection_before_later_edits(self):
        from ecu_workbench.gui import Workbench
        class Var:
            def __init__(self,v):self.v=v
            def get(self):return self.v
            def set(self,v):self.v=v
        for label,scenario in HUDI_SCENARIO_LABELS.items():
            ui=SimpleNamespace(rom=image(),reset=Var('power'),nmi=Var('high'),steps=Var('1'),
                hudi_scenario=Var(label),port_b_pins=Var(''),port_c_pins=Var(''),port_d_pins=Var(''),
                port_b_mask=Var('0xFFFF'),port_c_mask=Var('0x1F'),port_d_mask=Var('0xFFFF'),
                status=Var(''),summary='summary',blocker='blocker',trace='trace',peripherals='peripherals')
            ui._set=lambda *a:None
            Workbench.run_boot(ui)
            ui.hudi_scenario.set('Unknown (default)')
            self.assertEqual(ui.report['diagnostic_settings']['hudi_scenario'],scenario)
            out=make_shareable_blocker_report(ui.report)
            self.assertEqual(out['hudi_scenario'],scenario)

    def test_optional_original_reference_scenario_comparison(self):
        source=os.environ.get('MX5_NC_TEST_ROM')
        if not source:self.skipTest('Private original-reference ROM unavailable')
        rom=ROMImage('private',Path(source).read_bytes())
        if rom.sha256!=LF9VEB_SHA256:self.skipTest('Different private ROM hash')
        for scenario in HUDI_SCENARIOS:
            r=diagnose_nc_reset(rom,max_steps=300,nmi_high=True,hudi_scenario=scenario)
            self.assertFalse(r['boot_complete'])
            self.assertGreaterEqual(r['executed_instructions'],188 if scenario=='unknown' else 212)
            if scenario=='unknown':
                self.assertEqual(r['stop']['reason'],'unknown_peripheral_reset_state')
                self.assertEqual(r['next_dependency']['instruction_pc'],'0x00000EF8')
            elif r['executed_instructions']==212:
                self.assertEqual(r['next_dependency']['opcode'],'880B')
                self.assertEqual(r['next_dependency']['instruction_pc'],'0x00000F0C')
