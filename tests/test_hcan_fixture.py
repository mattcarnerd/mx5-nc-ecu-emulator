import copy,io,json,tempfile,unittest
from pathlib import Path
from contextlib import redirect_stdout
from test_sh2_branch import program
from ecu_workbench.nc_boot import NCBootDiagnostic
from ecu_workbench.hcan import MCR_ADDRESSES,GSR_ADDRESSES
from ecu_workbench.hcan_fixture import normalize_hcan_fixture
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.trace_review import summarise
from ecu_workbench.cli import main

class HcanFixtureTests(unittest.TestCase):
    def cpu(self,fixture):
        return NCBootDiagnostic(program(0x0009).bus.image,hcan_fixture=fixture)

    def test_completion_is_opt_in_delayed_isolated_and_cancelled(self):
        f={'reset_completion_ticks':3,'recessive_bus_ticks':1}
        d=self.cpu(f);b=d.bus;b.write(MCR_ADDRESSES[0],2,1)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
        for _ in range(2):d.clock.completed_instruction()
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
        d.clock.completed_instruction()
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).value,12)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,63)
        b.write(MCR_ADDRESSES[0],2,1);b.write(MCR_ADDRESSES[0],2,0)
        d.clock.completed_instruction()
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,8)
        for _ in range(4):d.clock.completed_instruction()
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,8)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[1]).value,12)
        d=self.cpu(None);d.bus.write(MCR_ADDRESSES[0],2,1)
        for _ in range(5):d.clock.completed_instruction()
        self.assertEqual(d.bus.read_cpu_word(GSR_ADDRESSES[0]).mask,0)

    def test_validation_and_omitted_event_stays_unknown(self):
        for value in ({},{'reset_completion_ticks':1},{'reset_completion_ticks':True,'recessive_bus_ticks':1},
                      {'reset_completion_ticks':None,'recessive_bus_ticks':None},
                      {'reset_completion_ticks':0,'recessive_bus_ticks':1}):
            with self.assertRaises(ValueError):normalize_hcan_fixture(value)
        d=self.cpu({'reset_completion_ticks':None,'recessive_bus_ticks':1})
        d.bus.write(MCR_ADDRESSES[0],2,1);d.clock.completed_instruction()
        self.assertEqual(d.bus.read_cpu_word(GSR_ADDRESSES[0]).mask,0)

    def test_report_baseline_export_and_tamper_checks(self):
        f={'reset_completion_ticks':1,'recessive_bus_ticks':None}
        image=program(0x0009).bus.image
        d=NCBootDiagnostic(image,hcan_fixture=f,nmi_high=True);r=d.run(1)
        settings={'reset':'power','nmi':'high','max_steps':1,'explicit_pin_values':False,'hcan_fixture':f}
        full={'image':{'sha256':image.sha256},'nc_boot':r,'diagnostic_settings':settings}
        s=make_shareable_blocker_report(full)
        self.assertEqual(s['hcan_fixture'],f);self.assertTrue(s['conditional_hardware_scenario'])
        self.assertFalse(s['reference_lf9veb_scenario'])
        self.assertGreater(s['explicit_peripheral_inputs'],0)
        for mutation in ('remove','change','marker'):
            changed=copy.deepcopy(full)
            if mutation=='remove':del changed['nc_boot']['hcan_fixture']
            elif mutation=='change':changed['nc_boot']['hcan_fixture']['reset_completion_ticks']=2
            else:changed['nc_boot']['conditional_hcan_fixture']=False
            with self.assertRaises(ValueError):make_shareable_blocker_report(changed)
        base=capture_boot_baseline(image,max_steps=1,nmi_high=True,hcan_fixture=f)
        self.assertEqual(base['hcan_fixture'],f);self.assertFalse(summarise(base)['reference_scenario'])
        del base['hcan_fixture']
        with self.assertRaises(ValueError):summarise(base)

    def test_cli_completion_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'synthetic.bin';path.write_bytes(program(0x0009).bus.image.data)
            for baseline in (False,True):
                out=io.StringIO()
                with redirect_stdout(out):
                    main(['--rom',str(path),'--nmi','high','--steps','1',
                          '--hcan-reset-completion-ticks','1','--hcan-recessive-bus-ticks','2']+
                         (['--baseline'] if baseline else []))
                r=json.loads(out.getvalue())
                meta=r if baseline else r['nc_boot']
                self.assertTrue(meta['conditional_hcan_fixture'])
                self.assertEqual(meta['hcan_fixture'],{'reset_completion_ticks':1,'recessive_bus_ticks':2})
