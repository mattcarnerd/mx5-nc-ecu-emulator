import json,tempfile,unittest
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout
from types import SimpleNamespace
from test_sh2_branch import program
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import NCBootDiagnostic,diagnose_nc_reset
from ecu_workbench.adc import ADDR0,ADCR0
from ecu_workbench.sensor_fixture import adc_fields,normalize_adc_fixture
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.trace_review import summarise,LF9VEB_SHA256
from ecu_workbench.boot_presenter import present_reset_diagnostic
from ecu_workbench.cli import main


def sensor_rom():
    d=program(0xD105,0xE02F,0x2100,0x0009,0xD204,0x6321)
    data=bytearray(d.bus.image.data)
    data[0x118:0x11C]=ADCR0.to_bytes(4,'big');data[0x11C:0x120]=ADDR0.to_bytes(4,'big')
    return ROMImage('synthetic',bytes(data))

class SensorFixtureTests(unittest.TestCase):
    def test_supplied_voltage_changes_actual_firmware_read(self):
        observed=[]
        for voltage in (1,4):
            d=NCBootDiagnostic(sensor_rom(),adc_fixture=adc_fields(voltage,5,1))
            r=d.run(6);observed.append(d.r[3]&0xFFFF)
            self.assertEqual(r['stop']['reason'],'instruction_limit')
            self.assertTrue(r['conditional_adc_scenario']);self.assertTrue(r['conditional_hardware_scenario'])
            self.assertFalse(r['boot_complete'])
        self.assertEqual(observed,[204<<6,819<<6])
        d=NCBootDiagnostic(sensor_rom());d.run(6)
        self.assertEqual(d.r[3],0);self.assertEqual(d.bus.adc.cr,47)
        self.assertEqual(d.bus.adc.csr,0)  # known reset data, no invented completed conversion

    def test_validation_report_provenance_and_baseline(self):
        fixture=adc_fields('2.5',5,2)
        self.assertEqual(fixture['voltage'],'5/2');self.assertIsNone(adc_fields('','',''))
        for values in ((1,None,None),(1,0,1),(6,5,1),(1,5,0),('nan',5,1)):
            with self.assertRaises(ValueError):adc_fields(*values)
        with self.assertRaises(ValueError):normalize_adc_fixture(dict(voltage=1,reference=5,completion_ticks=True))
        boot=diagnose_nc_reset(sensor_rom(),nmi_high=True,max_steps=300,adc_fixture=fixture)
        detail={'image':{'sha256':boot['rom_sha256']},'nc_boot':boot,
                'diagnostic_settings':{'reset':'power','nmi':'high','max_steps':300,'explicit_pin_values':False}}
        reduced=make_shareable_blocker_report(detail)
        self.assertEqual(reduced['adc_fixture'],fixture);self.assertFalse(reduced['reference_lf9veb_scenario'])
        detail['diagnostic_settings']['adc_fixture']=None
        with self.assertRaises(ValueError):make_shareable_blocker_report(detail)
        baseline=capture_boot_baseline(sensor_rom(),nmi_high=True,adc_fixture=fixture)
        baseline['rom']['sha256']=LF9VEB_SHA256
        self.assertFalse(summarise(baseline)['reference_scenario'])
        self.assertIn('Conditional',present_reset_diagnostic(boot)['status'])
        baseline['inputs']['adc_fixture']=None
        with self.assertRaises(ValueError):summarise(baseline)

    def test_cli_and_gui_save_executed_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'synthetic.bin';path.write_bytes(sensor_rom().data)
            for baseline in (False,True):
                args=['--rom',str(path),'--steps','6','--an0-voltage','1','--adc-reference-voltage','5','--adc-completion-ticks','1']
                if baseline:args+=['--baseline']
                out=StringIO()
                with redirect_stdout(out):self.assertEqual(main(args),0)
                result=json.loads(out.getvalue());result=result if baseline else result['nc_boot']
                self.assertEqual(result['adc_fixture']['voltage'],'1')
        from ecu_workbench.gui import Workbench
        class Var:
            def __init__(self,v):self.v=v
            def get(self):return self.v
            def set(self,v):self.v=v
        ui=SimpleNamespace(rom=sensor_rom(),reset=Var('power'),nmi=Var('high'),steps=Var('6'),
            hudi_scenario=Var('Unknown (default)'),phi_cycles_per_instruction=Var(''),
            an0_voltage=Var('1'),adc_reference=Var('5'),adc_completion_ticks=Var('1'),
            port_b_pins=Var(''),port_c_pins=Var(''),port_d_pins=Var(''),port_b_mask=Var('0xFFFF'),
            port_c_mask=Var('0x1F'),port_d_mask=Var('0xFFFF'),status=Var(''),summary='s',blocker='b',trace='t',peripherals='p')
        ui._set=lambda *a:None;Workbench.run_boot(ui);ui.an0_voltage.set('4')
        self.assertEqual(make_shareable_blocker_report(ui.report)['adc_fixture']['voltage'],'1')
