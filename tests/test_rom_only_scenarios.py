import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, diagnose_nc_reset
from ecu_workbench.hcan import MCR_ADDRESSES, mcr_scenario_metadata
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.trace_review import summarise
from ecu_workbench.cli import main

class RomOnlyScenarios(unittest.TestCase):
    def test_readback_both_channels_strict_and_explicit(self):
        image=program(0x0009).bus.image
        strict=BootBus(image)
        self.assertEqual(strict.read_cpu_word(MCR_ADDRESSES[0]).mask,0xFFBF)
        with self.assertRaises(BootStop):strict.read(MCR_ADDRESSES[0],2)
        for bit in (0,1):
            b=BootBus(image,experimental_mcr_bit6=bit)
            for address in MCR_ADDRESSES:
                self.assertEqual(b.read_cpu_word(address).concrete(),1|(bit<<6))
                b.write(address,2,0)
                self.assertEqual(b.read(address,2),bit<<6)
                before=(list(b.hcan.commands),list(b.peripheral_trace))
                with self.assertRaises(BootStop):b.write(address,2,0x40)
                self.assertEqual((b.hcan.commands,b.peripheral_trace),before)
            manual=BootBus(image,power_on=False,experimental_mcr_bit6=bit)
            with self.assertRaises(BootStop):manual.read_cpu_word(MCR_ADDRESSES[0])
            for width in (1,4):
                with self.assertRaises(BootStop):b.read(MCR_ADDRESSES[0],width)

    def test_scenario_validation_and_early_stop_provenance(self):
        for value in (True,False,2,-1,'0',[],{}):
            with self.assertRaises(ValueError):mcr_scenario_metadata(value)
        for bit in (0,1):
            r=diagnose_nc_reset(program(0x0009).bus.image,max_steps=1,experimental_mcr_bit6=bit)
            self.assertEqual(r['experimental_mcr_bit6'],bit)
            self.assertTrue(r['conditional_mcr_scenario'])
            self.assertTrue(r['conditional_hardware_scenario'])
            self.assertFalse(r['boot_complete'])

    def diagnostic(self,bit):
        image=program(0x0009).bus.image
        boot=diagnose_nc_reset(image,max_steps=1,nmi_high=True,experimental_mcr_bit6=bit)
        return {'image':{'sha256':image.sha256},'nc_boot':boot,
                'diagnostic_settings':{'reset':'power','nmi':'high','max_steps':1,
                'explicit_pin_values':False,'experimental_mcr_bit6':bit}}

    def test_export_provenance_and_tamper_rejection(self):
        for bit in (0,1):
            d=self.diagnostic(bit);share=make_shareable_blocker_report(d)
            self.assertTrue(share['conditional_mcr_scenario'])
            self.assertFalse(share['reference_lf9veb_scenario'])
            self.assertEqual(share['experimental_mcr_bit6'],bit)
            for field,value in (('experimental_mcr_bit6',1-bit),('experimental_mcr_bit6',None),
                                ('conditional_mcr_scenario',False)):
                changed=copy.deepcopy(d);changed['nc_boot'][field]=value
                with self.assertRaises(ValueError):make_shareable_blocker_report(changed)
            changed=copy.deepcopy(d);del changed['nc_boot']['experimental_mcr_bit6']
            with self.assertRaises(ValueError):make_shareable_blocker_report(changed)

    def test_baseline_and_review_provenance(self):
        for bit in (None,0,1):
            r=capture_boot_baseline(program(0x0009).bus.image,max_steps=1,nmi_high=True,experimental_mcr_bit6=bit)
            self.assertEqual(r['experimental_mcr_bit6'],bit)
            self.assertEqual(r['conditional_mcr_scenario'],bit is not None)
            self.assertFalse(summarise(r)['reference_scenario'])
            if bit is not None:
                self.assertEqual(r['inputs']['experimental_mcr_bit6'],bit)
                changed=copy.deepcopy(r);del changed['experimental_mcr_bit6']
                with self.assertRaises(ValueError):summarise(changed)
                changed=copy.deepcopy(r);changed['experimental_mcr_bit6']=1-bit
                with self.assertRaises(ValueError):summarise(changed)

    def test_cli_detailed_and_baseline_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'synthetic.bin';path.write_bytes(program(0x0009).bus.image.data)
            for baseline in (False,True):
                out=io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(main(['--rom',str(path),'--steps','1','--nmi','high',
                        '--experimental-mcr-bit6','0']+(['--baseline'] if baseline else [])),0)
                result=json.loads(out.getvalue())
                if baseline:self.assertTrue(result['conditional_mcr_scenario'])
                else:
                    self.assertEqual(result['diagnostic_settings']['experimental_mcr_bit6'],0)
                    self.assertEqual(make_shareable_blocker_report(result)['experimental_mcr_bit6'],0)

    def test_firmware_read_or_write_keeps_both_branches_explicit(self):
        image=program(0x6031,0xCB01,0x2301).bus.image
        for bit in (None,0,1):
            cpu=NCBootDiagnostic(image,experimental_mcr_bit6=bit);cpu.r[3]=MCR_ADDRESSES[0]
            r=cpu.run(3)
            self.assertEqual(r['executed_instructions'],3)
            self.assertEqual(r['stop']['reason'],'unknown_register' if bit is None else 'instruction_limit' if bit==0 else 'unsupported_peripheral_mode')
            self.assertEqual(any(e.get('access')=='write' for e in cpu.bus.peripheral_trace),bit==0)
            self.assertEqual(cpu.bus.hcan.software_reset_requests[0],bit==0)
