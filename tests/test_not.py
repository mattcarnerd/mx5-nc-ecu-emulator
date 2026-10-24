import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class NotTests(unittest.TestCase):
    def test_complement_alias_and_t_preservation(self):
        for value in (0,1,0x80000000,0xFFFFFFFF):
            for dest in (0,1):
                d=program(0x6007|(dest<<8));d.r[0]=value;d.t=None;d.execute()
                self.assertEqual(d.r[dest],value^0xFFFFFFFF)
                self.assertIsNone(d.t)
                if dest:self.assertEqual(d.r[0],value)

    def test_partial_and_unknown_masks_are_preserved(self):
        for value in (None,KnownBits(0x12345678,0xFF00FF00)):
            d=program(0x6107);d.r[0]=value;d.t=True;d.execute()
            before=KnownBits(0,0) if value is None else value
            self.assertEqual(d.r[1],KnownBits(~before.value,before.mask))
            self.assertTrue(d.t)
