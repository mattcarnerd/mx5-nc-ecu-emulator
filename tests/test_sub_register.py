import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class SubRegisterTests(unittest.TestCase):
    def test_modulo_boundaries_aliases_and_t_preservation(self):
        values=(0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF)
        for left in values:
            for right in values:
                for t in (None,False,True):
                    d=program(0x3428);d.r[4]=left;d.r[2]=right;d.t=t
                    d.execute()
                    self.assertEqual(d.r[4],(left-right)&0xFFFFFFFF)
                    self.assertEqual(d.r[2],right);self.assertIs(d.t,t)
            d=program(0x3448);d.r[4]=left;d.execute()
            self.assertEqual(d.r[4],0)

    def test_unknown_operands_fail_without_mutating_destination_or_t(self):
        for index in (2,4):
            for unknown in (None,KnownBits(0,0xFFFFFFFE)):
                d=program(0x3428);d.r[4]=2;d.r[2]=1;d.r[index]=unknown;d.t=True
                before=list(d.r);r=d.run(1)
                self.assertEqual(r['stop']['reason'],'unknown_register')
                self.assertEqual(d.r,before);self.assertTrue(d.t)
                self.assertEqual(d.clock.ticks,0)

    def test_delay_slot(self):
        d=program(0xA001,0x3428,0x0009,0x0009)
        d.r[4]=0;d.r[2]=1;d.t=None;r=d.run(2)
        self.assertEqual(r['completed_instructions'],2)
        self.assertEqual(d.r[4],0xFFFFFFFF);self.assertIsNone(d.t)
        self.assertEqual(d.pc,0x106)
