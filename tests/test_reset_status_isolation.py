import contextlib,io,json,tempfile,unittest
from pathlib import Path
from test_sh2_branch import program
from ecu_workbench.nc_boot import NCBootDiagnostic
from ecu_workbench.hcan import MCR_ADDRESSES,GSR_ADDRESSES
from ecu_workbench.hcan_fixture import normalize_hcan_fixture
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.cli import main

class ResetStatusIsolationTests(unittest.TestCase):
    fixture={'reset_completion_ticks':1,'recessive_bus_ticks':4,'defer_mailbox_effects':True,
             'preserve_supplied_reset_status':True}

    def test_only_known_or_supplied_reset_bit_survives_and_taint_persists(self):
        d=NCBootDiagnostic(program(0x0009).bus.image,hcan_fixture=self.fixture);b=d.bus
        b.write(MCR_ADDRESSES[0],2,1);d.clock.completed_instruction()
        b.write(0xFFFFD104,2,0x2308)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,8)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).value,8)
        b.write(MCR_ADDRESSES[0],2,0)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).value,8)
        for _ in range(4):d.clock.completed_instruction()
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,8)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).value,0)
        self.assertTrue(b.hcan.effect_unknown_channels[0])
        self.assertEqual(b.hcan.unresolved_command_count,1)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[1]).value,12)

    def test_legacy_policy_stays_unknown_and_stale_event_cannot_override_new_request(self):
        f=dict(self.fixture);f.pop('preserve_supplied_reset_status')
        d=NCBootDiagnostic(program(0x0009).bus.image,hcan_fixture=f);b=d.bus
        b.write(MCR_ADDRESSES[0],2,1);b.write(0xFFFFD104,2,0x2308)
        d.clock.completed_instruction();self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
        d=NCBootDiagnostic(program(0x0009).bus.image,hcan_fixture=self.fixture);b=d.bus
        b.write(MCR_ADDRESSES[0],2,1);b.write(0xFFFFD104,2,0x2308);b.write(MCR_ADDRESSES[0],2,0)
        d.clock.completed_instruction();self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
        for _ in range(3):d.clock.completed_instruction()
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,8)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).value,0)

    def test_explicit_boolean_and_deferred_policy_are_required(self):
        for value in (1,'yes',None):
            with self.assertRaises(ValueError):normalize_hcan_fixture(dict(self.fixture,preserve_supplied_reset_status=value))
        bad=dict(self.fixture);bad.pop('defer_mailbox_effects')
        with self.assertRaises(ValueError):normalize_hcan_fixture(bad)

    def test_cli_baseline_and_shareable_provenance(self):
        image=program(0x0009).bus.image
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'synthetic.bin';path.write_bytes(image.data)
            out=io.StringIO()
            with contextlib.redirect_stdout(out):
                main(['--rom',str(path),'--nmi','high','--steps','1',
                      '--hcan-reset-completion-ticks','1','--hcan-recessive-bus-ticks','4',
                      '--experimental-record-can-commands','--experimental-isolate-can-reset-status'])
            full=json.loads(out.getvalue());share=make_shareable_blocker_report(full)
            self.assertEqual(share['hcan_fixture'],self.fixture)
            self.assertTrue(share['conditional_hardware_scenario'])
            self.assertFalse(share['reference_lf9veb_scenario'])
            baseline=capture_boot_baseline(image,max_steps=1,nmi_high=True,hcan_fixture=self.fixture)
            self.assertEqual(baseline['hcan_fixture'],self.fixture)
