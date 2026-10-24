import unittest
from test_sh2_branch import program
from ecu_workbench.core import ROMImage
from ecu_workbench.sh2_control import load_sr,read_sr
from ecu_workbench.share_report import make_shareable_blocker_report
from test_share_report import detailed
from ecu_workbench.interrupts import IPRL_ADDRESS


def irq_cpu(*words):
    d=program(*(words or (0xE109,0x0009,0x0009)))
    data=bytearray(d.bus.image.data);data[0x380:0x384]=(0x400).to_bytes(4,'big')
    data[0x400:0x406]=bytes.fromhex('0009 002B E307')
    d.bus.image=ROMImage('synthetic',bytes(data));d.bus.write(IPRL_ADDRESS,2,0x50)
    load_sr(d,0);return d

class InterruptTests(unittest.TestCase):
    def test_priority_vector_frame_and_held_source(self):
        d=irq_cpu();sp=d.reg(15);d.set_interval_request(True);r=d.run(1)
        self.assertEqual(d.interrupt_entries,1);self.assertEqual(d.pc,0x402)
        self.assertEqual(d.bus.read(sp-8,4),0x100);self.assertEqual(d.bus.read(sp-4,4),0)
        self.assertEqual(read_sr(d),0x50);self.assertTrue(d.interval_request)
        self.assertIsNone(d.r[1]);self.assertEqual(d.clock.ticks,1)
        d.set_interval_request(False);d.run(4)
        self.assertEqual(d.r[1],9);self.assertEqual(d.r[3],7);self.assertEqual(d.r[15],sp)
        self.assertEqual(d.interrupt_entries,1);self.assertFalse(r['boot_complete'])

    def test_zero_equal_lower_and_higher_priority(self):
        for priority,mask,expected in ((0,0,0),(5,5,0),(5,6,0),(7,6,1)):
            d=irq_cpu();d.bus.write(IPRL_ADDRESS,2,priority<<4);load_sr(d,mask<<4)
            d.set_interval_request(True);d.run(1)
            self.assertEqual(d.interrupt_entries,expected)
            self.assertTrue(d.interval_request)

    def test_no_acceptance_between_branch_and_slot(self):
        d=irq_cpu(0xA002,0xE207);d.clock.schedule(1,lambda:d.set_interval_request(True))
        d.run(3)
        self.assertEqual(d.r[2],7);self.assertTrue(d.trace[1]['delay_slot'])
        self.assertEqual(d.exception_events[0]['saved_pc'],'0x00000108')
        self.assertEqual(d.trace[2]['pc'],'0x00000400')

    def test_transfer_inhibition_allows_one_following_instruction(self):
        d=irq_cpu(0x410E,0xE207,0x0009);load_sr(d,0xF0);d.r[1]=0
        d.set_interval_request(True);d.run(3)
        self.assertEqual(d.r[2],7);self.assertEqual(d.interrupt_entries,1)
        self.assertEqual(d.exception_events[0]['saved_pc'],'0x00000104')

    def test_explicit_tick_zero_request_arrives_before_instruction(self):
        d=irq_cpu();d.clock.schedule(0,lambda:d.set_interval_request(True));d.run(1)
        self.assertIsNone(d.r[1]);self.assertEqual(d.interrupt_entries,1)
        self.assertEqual(d.exception_events[0]['tick'],0)

    def test_unknown_sr_and_priority_stop_without_fabricated_frame(self):
        d=irq_cpu();d.t=None;sp=d.reg(15);d.set_interval_request(True)
        r=d.run(1);self.assertEqual(r['stop']['reason'],'unknown_status')
        self.assertEqual(d.r[15],sp);self.assertEqual(d.executed,0)
        self.assertIsNone(r['next_dependency']['opcode'])
        d=irq_cpu();d.bus.ipr[IPRL_ADDRESS]=None;d.set_interval_request(True)
        self.assertEqual(d.run(1)['stop']['reason'],'unknown_peripheral_reset_state')

    def test_no_source_is_generated_automatically(self):
        d=irq_cpu();r=d.run(1)
        self.assertEqual(r['interrupt_entries'],0);self.assertEqual(r['explicit_interrupt_requests'],0)
        self.assertEqual(d.r[1],9)
        for bad in (None,1,'true'):
            with self.assertRaises(ValueError):d.set_interval_request(bad)

    def test_shareable_injection_cannot_be_reference_evidence(self):
        d=detailed();d['nc_boot']['explicit_interrupt_requests']=2
        r=make_shareable_blocker_report(d)
        self.assertFalse(r['reference_lf9veb_scenario']);self.assertTrue(r['injected_interrupt_scenario'])
        self.assertEqual(r['explicit_interrupt_requests'],2)
        d['nc_boot']['explicit_interrupt_requests']=True
        with self.assertRaises(ValueError):make_shareable_blocker_report(d)
