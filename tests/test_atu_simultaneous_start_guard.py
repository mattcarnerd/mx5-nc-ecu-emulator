import unittest
from test_sh2_branch import program
from ecu_workbench.atu import TSTR

class SimultaneousTimerStartGuardTests(unittest.TestCase):
    def test_original_ff_command_is_explicit_and_atomic(self):
        c=program(0x2340);c.r[3]=TSTR;c.r[4]=0xFF
        before=dict(c.bus.atu.regs);r=c.run(1)
        self.assertEqual(r['stop']['reason'],'unsupported_peripheral_mode')
        self.assertEqual(r['stop']['address'],'0xFFFFF401')
        self.assertEqual(r['stop']['value'],'0x000000FF')
        self.assertEqual(r['completed_instructions'],0)
        self.assertEqual(c.clock.ticks,0)
        self.assertEqual(c.bus.atu.regs,before);self.assertEqual(c.bus.atu.events,[])
        self.assertFalse(r['boot_complete']);self.assertEqual(r['interrupt_entries'],0)
