import unittest
from test_sh2_compare import cpu
from ecu_workbench.nc_boot import BootStop

class ShiftTests(unittest.TestCase):
    def test_single_shift_and_rotate_boundaries(self):
        cases=((0x4000,0x80000001,False,2,True),
               (0x4020,0xFFFFFFFF,False,0xFFFFFFFE,True),
               (0x4001,0x80000001,False,0x40000000,True),
               (0x4021,0x80000001,False,0xC0000000,True),
               (0x4021,0x7FFFFFFE,True,0x3FFFFFFF,False),
               (0x4004,0x80000000,False,1,True),
               (0x4005,1,False,0x80000000,True),
               (0x4024,0x80000000,True,1,True),
               (0x4024,0,True,1,False),
               (0x4025,1,True,0x80000000,True),
               (0x4025,0,True,0x80000000,False))
        for op,val,t,out,newt in cases:
            for n in (0,6,15):
                with self.subTest(op=op,n=n):
                    d=cpu(op | n<<8);d.r[n]=val;d.t=t;d.execute()
                    self.assertEqual(d.r[n],out);self.assertIs(d.t,newt)

    def test_multibit_preserves_t_and_wraps(self):
        for op,count,left in ((0x4008,2,True),(0x4018,8,True),(0x4028,16,True),
                              (0x4009,2,False),(0x4019,8,False),(0x4029,16,False)):
            for val in (0,1,0x80000000,0xFFFFFFFF):
                for t in (None,False,True):
                    d=cpu(op|0x600);d.r[6]=val;d.t=t;d.execute()
                    expected=(val*(2**count))%(2**32) if left else val//(2**count)
                    self.assertEqual(d.r[6],expected);self.assertIs(d.t,t)

    def test_unknowns_and_unrecognised_encoding(self):
        for op in (0x4124,0x4125):
            d=cpu(op);d.r[1]=5
            with self.assertRaises(BootStop) as c:d.execute()
            self.assertEqual(c.exception.kind,'unknown_status');self.assertEqual(d.r[1],5)
        d=cpu(0x4100)
        with self.assertRaises(BootStop):d.execute()
        d=cpu(0x4138);d.r[1]=5
        with self.assertRaises(BootStop) as c:d.execute()
        self.assertEqual(c.exception.kind,'unsupported_opcode')
