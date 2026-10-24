import os
from pathlib import Path
import unittest
from test_sh2_branch import program
from test_interrupts import irq_cpu
from test_share_report import detailed
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus,BootStop
from ecu_workbench.execution_harness import run_execution_harness
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.trace_review import summarise,LF9VEB_SHA256

class HarnessTests(unittest.TestCase):
    def test_stable_loop_counts_are_deterministic_not_boot(self):
        rom=program(0xAFFE,0x0009).bus.image
        a=run_execution_harness(rom,max_steps=12);b=run_execution_harness(rom,max_steps=12)
        self.assertEqual(a,b);c=a['execution_coverage']
        self.assertEqual(c['unique_instruction_pcs'],2);self.assertEqual(c['repeated_pc_visits'],10)
        self.assertEqual(c['max_pc_visits'],6);self.assertEqual(c['completed_delay_slots'],6)
        self.assertEqual(c['completed_instructions'],12);self.assertFalse(a['boot_complete'])
        self.assertEqual(a['stop']['reason'],'instruction_limit')

    def test_cpu_and_bus_failures_have_distinct_coverage(self):
        d=program(0xFFFF);r=d.run(10);c=r['execution_coverage']
        self.assertEqual((c['fetched_instructions'],c['completed_instructions'],c['bus_failure_count']),(1,0,0))
        d=program(0x2121);d.r[1]=0xFFFFE000;d.r[2]=0x12;r=d.run(10)
        fault=r['execution_coverage']['bus_failures'][0]
        self.assertEqual(fault,{'reason':'unmodelled_peripheral','address':'0xFFFFE000','width':2,
                               'access':'write','value':'0x00000012','instruction_pc':'0x00000100'})
        d=program(0x0009);d.pc=0x200000;r=d.run(1)
        self.assertEqual(r['execution_coverage']['fetched_instructions'],0)
        self.assertEqual(r['execution_coverage']['bus_failure_count'],1)

    def test_host_bus_probe_is_not_attributed_to_last_instruction(self):
        d=program(0x0009);d.run(1)
        with self.assertRaises(BootStop):d.bus.read(0xFFFFE000,2)
        self.assertIsNone(d.coverage.report()['bus_failures'][-1]['instruction_pc'])

    def test_bus_failure_history_is_bounded_without_losing_counts(self):
        b=BootBus(program(0x0009).bus.image)
        for _ in range(103):
            with self.assertRaises(BootStop):b.read(0xFFFFE000,2)
        c=b.coverage.report();self.assertEqual(c['bus_failure_count'],103)
        self.assertEqual(c['unsupported_bus_access_count'],103)
        self.assertEqual(len(c['bus_failures']),100);self.assertEqual(c['bus_failure_events_dropped'],3)
        self.assertEqual(c['bus_failures_by_reason'],{'unmodelled_peripheral':103})

    def test_explicit_events_drive_interrupt_path_and_keep_provenance(self):
        d=irq_cpu(0xE050,0xD207,0x2201,0xE000,0x400E,0x0009,0xE109)
        data=bytearray(d.bus.image.data);data[0x120:0x124]=(0xFFFFED16).to_bytes(4,'big')
        rom=ROMImage('synthetic',bytes(data))
        events=[{'tick':0,'asserted':True},{'tick':7,'asserted':False}]
        a=run_execution_harness(rom,max_steps=10,interval_events=events)
        b=run_execution_harness(rom,max_steps=10,interval_events=events)
        self.assertEqual(a,b);self.assertEqual(a['interrupt_entries'],1)
        self.assertEqual(a['explicit_interrupt_requests'],2);self.assertEqual(a['scheduled_interrupt_events'],2)
        self.assertEqual(a['exception_events'][0]['saved_pc'],'0x0000010C')
        self.assertEqual(a['completed_instructions'],10)
        self.assertEqual(a['execution_coverage']['completed_instructions'],10)

    def test_future_event_is_still_labelled_injected(self):
        r=run_execution_harness(program(0x0009).bus.image,max_steps=1,
                                interval_events=[{'tick':10,'asserted':True}])
        self.assertEqual(r['explicit_interrupt_requests'],0)
        self.assertEqual(r['scheduled_interrupt_events'],1)
        d=detailed();d['nc_boot']['scheduled_interrupt_events']=1
        shared=make_shareable_blocker_report(d)
        self.assertTrue(shared['injected_interrupt_scenario']);self.assertFalse(shared['reference_lf9veb_scenario'])
        base=capture_boot_baseline(program(0x0009).bus.image,nmi_high=True,max_steps=300)
        base['rom']['sha256']=LF9VEB_SHA256;base['result']['scheduled_interrupt_events']=1
        self.assertFalse(summarise(base)['reference_scenario'])

    def test_invalid_events_are_rejected_before_execution(self):
        rom=program(0x0009).bus.image
        for events in (None,{},[{'tick':True,'asserted':True}],[{'tick':-1,'asserted':True}],
                       [{'tick':0,'asserted':1}],[{'tick':0,'asserted':True,'extra':'bad'}]):
            with self.assertRaises(ValueError):run_execution_harness(rom,interval_events=events)
        for count in (0,True,100001):
            with self.assertRaises(ValueError):run_execution_harness(rom,max_steps=count)

    def test_pc_output_cap_does_not_change_unique_count(self):
        rom=program(*([0x0009]*300)).bus.image;r=run_execution_harness(rom,max_steps=300)
        c=r['execution_coverage'];self.assertEqual(c['unique_instruction_pcs'],300)
        self.assertEqual(len(c['pc_visits']),256);self.assertTrue(c['pc_list_truncated'])
        self.assertEqual(c['repeated_pc_visits'],0)

    def test_optional_original_rom_coverage_keeps_actual_stops(self):
        source=os.environ.get('MX5_NC_TEST_ROM')
        if not source:self.skipTest('Private original-reference ROM unavailable')
        rom=ROMImage('private',Path(source).read_bytes())
        if rom.sha256!=LF9VEB_SHA256:self.skipTest('Different private ROM hash')
        for scenario in ('unknown','trst-reset','transfer-complete'):
            r=run_execution_harness(rom,nmi_high=True,hudi_scenario=scenario)
            c=r['execution_coverage']
            self.assertEqual(c['fetched_instructions'],r['executed_instructions'])
            self.assertEqual(c['completed_instructions'],r['completed_instructions'])
            self.assertEqual(r['explicit_interrupt_requests'],0);self.assertFalse(r['boot_complete'])
            self.assertGreaterEqual(r['executed_instructions'],188 if scenario=='unknown' else 225)
            if scenario=='unknown':self.assertEqual(r['stop']['reason'],'unknown_peripheral_reset_state')
            elif r['executed_instructions']==225:self.assertEqual(r['stop']['reason'],'unsupported_peripheral_mode')
