import copy,unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import NCBootDiagnostic,BootStop
from ecu_workbench.hcan import MCR_ADDRESSES,GSR_ADDRESSES,MBIMR_ADDRESSES
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.hcan_fixture import normalize_hcan_fixture

class CanCommandRecorderTests(unittest.TestCase):
    fixture={'reset_completion_ticks':1,'recessive_bus_ticks':64,'defer_mailbox_effects':True}
    def cpu(self):
        return NCBootDiagnostic(program(0x2121).bus.image,hcan_fixture=self.fixture,experimental_mcr_bit6=0)

    def test_strict_rejects_recorder_completes_cpu_store_without_applying_it(self):
        strict=program(0x2121);strict.r[1]=0xFFFFD104;strict.r[2]=0x2308
        self.assertEqual(strict.run(1)['stop']['reason'],'invalid_peripheral_write')
        d=self.cpu();d.r[1]=0xFFFFD104;d.r[2]=0x2308
        r=d.run(1)
        self.assertEqual(r['stop']['reason'],'instruction_limit')
        self.assertNotIn(0xFFFFD104,d.bus.hcan.mailbox_writes)
        self.assertEqual(r['unresolved_hcan_command_count'],1)
        self.assertTrue(r['unresolved_hcan_effects'])
        self.assertTrue(r['conditional_hardware_scenario'])
        self.assertEqual(d.bus.hcan.effect_unknown_channels,[True,False])
        self.assertEqual(d.bus.hcan.unresolved_commands[0]['value'],0x2308)

    def test_can_feedback_and_pending_completions_cannot_clear_unknown_effects(self):
        d=self.cpu();b=d.bus
        b.write(MCR_ADDRESSES[0],2,1)
        b.write(0xFFFFD104,2,0x2308)
        for _ in range(4):d.clock.completed_instruction()
        self.assertEqual(b.read_cpu_word(MCR_ADDRESSES[0]).mask,0)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
        self.assertEqual(b.read_cpu_word(MCR_ADDRESSES[0]+4).mask,0)
        for a in (MCR_ADDRESSES[0],MBIMR_ADDRESSES[0],0xFFFFD104):
            with self.assertRaises(BootStop):b.read(a,2)
        self.assertFalse(b.hcan.bit_configuration(0)['known'])
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[1]).value,12)

    def test_recorder_does_not_swallow_gaps_width_unknown_values_or_other_devices(self):
        for a,w,v in ((0xFFFFD114,2,0),(0xFFFFD104,1,0),(0xFFFFD104,4,0),(0xFFFFF900,2,1)):
            d=self.cpu()
            with self.assertRaises(BootStop):d.bus.write(a,w,v)
            self.assertEqual(d.bus.hcan.unresolved_command_count,0)
        d=self.cpu();d.r[1]=0xFFFFD104;d.r[2]=None
        self.assertEqual(d.run(1)['stop']['reason'],'unknown_register')
        self.assertEqual(d.bus.hcan.unresolved_command_count,0)

    def test_export_preserves_recorder_and_rejects_missing_policy(self):
        d=self.cpu();d.r[1]=0xFFFFD104;d.r[2]=0x2308;r=d.run(1)
        settings={'reset':'power','nmi':'unknown','max_steps':1,'explicit_pin_values':False,
                  'experimental_mcr_bit6':0,'hcan_fixture':self.fixture}
        full={'image':{'sha256':d.bus.image.sha256},'nc_boot':r,'diagnostic_settings':settings}
        s=make_shareable_blocker_report(full)
        self.assertTrue(s['unresolved_hcan_effects']);self.assertFalse(s['reference_lf9veb_scenario'])
        bad=copy.deepcopy(full);bad['nc_boot']['unresolved_hcan_effects']=False
        with self.assertRaises(ValueError):make_shareable_blocker_report(bad)
        bad=copy.deepcopy(full)
        for key in ('diagnostic_settings','nc_boot'):bad[key]['hcan_fixture'].pop('defer_mailbox_effects',None)
        with self.assertRaises(ValueError):make_shareable_blocker_report(bad)
        for value in ('yes',1,None):
            bad=dict(self.fixture,defer_mailbox_effects=value)
            with self.assertRaises(ValueError):normalize_hcan_fixture(bad)
