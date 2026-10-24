import unittest
from test_sh2_compare import cpu
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootStop


def program(*words):
    d=cpu(words[0]);data=bytearray(d.bus.image.data)
    for i,word in enumerate(words):data[0x100+2*i:0x102+2*i]=word.to_bytes(2,'big')
    d.bus.image=ROMImage('synthetic',bytes(data));return d

class BranchTests(unittest.TestCase):
    def test_conditional_targets_and_slot_side_effects(self):
        for op,t,taken in ((0x8D02,True,True),(0x8D02,False,False),
                           (0x8F02,False,True),(0x8F02,True,False)):
            d=program(op,0xE107);d.t=t;r=d.run(2)
            self.assertEqual(d.pc,0x108 if taken else 0x104)
            self.assertEqual(d.r[1],7);self.assertEqual(d.executed,2)
            self.assertEqual(d.trace[-1]['delay_slot'],taken)
            self.assertFalse(r['boot_complete'])

    def test_not_taken_next_instruction_is_not_a_slot(self):
        d=program(0x8D01,0xA000,0xE109);d.t=False;d.run(3)
        self.assertEqual(d.pc,0x106);self.assertEqual(d.r[1],9)
        self.assertFalse(d.trace[1]['delay_slot']);self.assertTrue(d.trace[2]['delay_slot'])

    def test_register_target_captured_before_slot_and_pr(self):
        for op,link in ((0x0123,False),(0x0103,True)):
            d=program(op,0xE104);d.r[1]=0x10;d.pr=0x200;d.run(2)
            self.assertEqual(d.pc,0x114);self.assertEqual(d.r[1],4)
            self.assertEqual(d.pr,0x104 if link else 0x200)

    def test_negative_displacements_and_wrap(self):
        for op in (0x8DFE,0x8FFE):
            d=cpu(op);d.t=op==0x8DFE
            self.assertEqual(d.execute(),0x100)
        for op in (0x0123,0x0103):
            d=cpu(op);d.r[1]=0xFFFFFFFC
            self.assertEqual(d.execute(),0x100)
        d=cpu(0x0103);d.pc=0xFFFFFFFC;d.r[1]=8
        d.bus.read=lambda a,w:0x0103
        self.assertEqual(d.execute(),8);self.assertEqual(d.pr,0)

    def test_step_limit_preserves_pending_branch_across_runs(self):
        d=program(0x8D02,0xE107);d.t=True
        r=d.run(1);self.assertEqual(d.pc,0x102);self.assertIsNone(d.r[1])
        self.assertIn('delay slot',r['stop']['detail'])
        d.run(2);self.assertEqual(d.pc,0x108);self.assertEqual(d.r[1],7)
        self.assertEqual(d.executed,2);self.assertTrue(d.trace[-1]['delay_slot'])

    def test_illegal_slot_rejected_before_link_mutation(self):
        for op in (0x8D00,0x8F00,0x0103,0x0123):
            d=program(0xA000,op);d.t=False;d.r[1]=4;d.pr=0x200
            r=d.run(2)
            self.assertEqual(r['stop']['reason'],'illegal_delay_slot')
            self.assertEqual(d.pr,0x200)

    def test_unknown_condition_and_register(self):
        for op in (0x8D00,0x8F00,0x0103,0x0123):
            d=cpu(op)
            with self.assertRaises(BootStop):d.execute()
            self.assertIsNone(d.pr)
