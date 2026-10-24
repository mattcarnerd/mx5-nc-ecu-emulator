import unittest
from test_sh2_compare import cpu
from ecu_workbench.nc_boot import BootStop

class ImmediateCompareTests(unittest.TestCase):
    def test_signed_immediate_equality_and_inequality(self):
        for immediate,matching in ((0,0),(0x7F,127),(0x80,0xFFFFFF80),(0xFF,0xFFFFFFFF),(11,11)):
            for value,expected in ((matching,True),((matching+1)&0xFFFFFFFF,False)):
                d=cpu(0x8800|immediate);d.r[0]=value;d.r[1]=123;d.t=None
                d.execute();self.assertIs(d.t,expected)
                self.assertEqual((d.r[0],d.r[1]),(value,123))
        d=cpu(0x88FF);d.r[0]=255;d.execute();self.assertIs(d.t,False)

    def test_unknown_r0_preserves_flags_and_other_state(self):
        d=cpu(0x880B);d.t=True
        with self.assertRaises(BootStop) as c:d.execute()
        self.assertEqual(c.exception.kind,'unknown_register')
        self.assertIs(d.t,True);self.assertIsNone(d.r[0])

    def test_outgoing_t_feeds_existing_branch(self):
        from test_sh2_branch import program
        d=program(0x880B,0x8901,0xE107,0xE108);d.r[0]=11
        d.run(2);self.assertEqual(d.pc,0x108)
        self.assertIsNone(d.r[1])
