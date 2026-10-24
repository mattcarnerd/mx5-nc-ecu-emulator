import unittest
from test_sh2_branch import program
from test_sh2_compare import cpu
from ecu_workbench.nc_boot import BootStop
from ecu_workbench.virtual_clock import InstructionClock

class ClockTests(unittest.TestCase):
    def test_completed_and_attempted_counts_are_distinct(self):
        d=program(0x0009,0xFFFF);r=d.run(10)
        self.assertEqual((r['executed_instructions'],r['completed_instructions']),(2,1))
        self.assertIsNone(r['virtual_time']['cpu_cycles']);self.assertIsNone(r['virtual_time']['seconds'])
        self.assertFalse(r['virtual_time']['cycle_accurate'])

    def test_failed_fetch_does_not_advance_clock(self):
        d=cpu(0x0009);d.pc=0x200000;r=d.run(1)
        self.assertEqual(d.clock.ticks,0);self.assertEqual(r['executed_instructions'],0)

    def test_delay_slot_resume_has_one_tick_per_completion(self):
        d=program(0xA000,0xE107);d.run(1)
        self.assertEqual(d.clock.ticks,1);self.assertIsNone(d.r[1])
        d.run(2);self.assertEqual(d.clock.ticks,2);self.assertEqual(d.r[1],7)

    def test_event_order_and_tick_zero(self):
        d=program(0x0009,0x0009);events=[]
        for tick,label in ((1,'a'),(0,'start'),(1,'b'),(2,'end')):
            d.clock.schedule(tick,lambda label=label:events.append((label,d.clock.ticks)))
        d.run(2);self.assertEqual(events,[('start',0),('a',1),('b',1),('end',2)])
        self.assertEqual(d.clock.report()['pending_events'],0)

    def test_clock_validation_and_determinism(self):
        clock=InstructionClock();clock.completed_instruction()
        for tick in (-1,0,True,1.5):
            with self.assertRaises(ValueError):clock.schedule(tick,lambda:None)
        with self.assertRaises(TypeError):clock.schedule(2,None)
        reports=[]
        for _ in range(2):reports.append(program(0xA000,0x0009).run(2))
        self.assertEqual(reports[0],reports[1])

    def test_failed_instruction_does_not_trigger_future_event(self):
        d=cpu(0xFFFF);events=[];d.clock.schedule(1,lambda:events.append(True))
        with self.assertRaises(BootStop):d.execute()
        self.assertEqual(events,[]);self.assertEqual(d.clock.ticks,0)
