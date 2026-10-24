import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class CompareHiTests(unittest.TestCase):
    def test_boundaries_equal_and_alias_preserve_operands(self):
        values=(0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF)
        for left in values:
            for right in values:
                d=program(0x3016);d.r[0]=left;d.r[1]=right;d.t=None
                d.execute();self.assertEqual(d.t,left>right)
                self.assertEqual(d.r[:2],[left,right])
            d=program(0x3006);d.r[0]=left;d.execute();self.assertFalse(d.t)

    def test_unknown_operand_never_selects_a_compare_result(self):
        for unknown in (None,KnownBits(0,0xFFFFFFFE)):
            for index in (0,1):
                d=program(0x3016);d.r[0]=1;d.r[1]=0;d.r[index]=unknown;d.t=True
                r=d.run(1)
                self.assertEqual(r['stop']['reason'],'unknown_register')
                self.assertTrue(d.t);self.assertEqual(d.clock.ticks,0)
