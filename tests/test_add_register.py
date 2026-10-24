import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class AddRegisterTests(unittest.TestCase):
    def test_modulo_boundaries_alias_and_unchanged_t(self):
        values=(0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF)
        for left in values:
            for right in values:
                d=program(0x301C);d.r[0]=left;d.r[1]=right;d.t=None
                d.execute();self.assertEqual(d.r[0],(left+right)%4294967296)
                self.assertEqual(d.r[1],right);self.assertIsNone(d.t)
            d=program(0x300C);d.r[0]=left;d.t=True;d.execute()
            self.assertEqual(d.r[0],(2*left)%4294967296);self.assertTrue(d.t)

    def test_unknown_operand_is_atomic(self):
        for value in (None,KnownBits(0,0xFFFFFFFE)):
            for index in (0,1):
                d=program(0x301C);d.r[0]=5;d.r[1]=6;d.r[index]=value;before=list(d.r);d.t=False
                r=d.run(1);self.assertEqual(r['stop']['reason'],'unknown_register')
                self.assertEqual(d.r,before);self.assertFalse(d.t)
