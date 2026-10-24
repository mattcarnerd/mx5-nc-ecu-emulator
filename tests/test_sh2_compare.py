"""B09 compares and carry/borrow with sign and overflow-edge cases."""
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import NCBootDiagnostic, BootStop, ROM_LIMIT

def cpu(op):
    d=bytearray(ROM_LIMIT)
    for i,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        d[i*4:i*4+4]=v.to_bytes(4,"big")
    d[0x100:0x102]=op.to_bytes(2,"big")
    return NCBootDiagnostic(ROMImage("synthetic",bytes(d)))

class CompareTests(unittest.TestCase):
    def test_compare_eq_hs_ge_zero_sign_and_overflow(self):
        cases=(
            (0x3120,0,0,True),(0x3120,0,1,False),
            (0x3120,0xFFFFFFFF,0xFFFFFFFF,True),
            (0x3122,0,0,True),(0x3122,0xFFFFFFFF,0,True),
            (0x3122,0,0xFFFFFFFF,False),
            (0x3123,0,0,True),(0x3123,0xFFFFFFFF,0,False),
            (0x3123,0,0xFFFFFFFF,True),
            (0x3123,0x80000000,0x7FFFFFFF,False),
            (0x3123,0x7FFFFFFF,0x80000000,True),
        )
        for op,left,right,expected in cases:
            with self.subTest(op=hex(op),a=hex(left),b=hex(right)):
                d=cpu(op);d.r[1]=left;d.r[2]=right;d.t=None
                d.execute()
                self.assertIs(d.t,expected)
                self.assertEqual((d.r[1],d.r[2]),(left,right))

    def test_addc_wrap_and_carry_out(self):
        cases=(
            (0,0,False,0,False),
            (0xFFFFFFFF,0,False,0xFFFFFFFF,False),
            (0xFFFFFFFF,0,True,0,True),
            (0x7FFFFFFF,1,False,0x80000000,False),
            (0,0,True,1,False),
            (0xFFFFFFFF,0xFFFFFFFF,True,0xFFFFFFFF,True),
        )
        for left,right,carry,out,t in cases:
            with self.subTest(a=left,b=right,t_in=carry):
                d=cpu(0x312E);d.r[1]=left;d.r[2]=right;d.t=carry
                d.execute()
                self.assertEqual(d.r[1],out)
                self.assertIs(d.t,t)
                self.assertEqual(d.r[2],right)

    def test_subc_borrow_and_wrap(self):
        cases=(
            (0,0,False,0,False),
            (0,1,False,0xFFFFFFFF,True),
            (0,0,True,0xFFFFFFFF,True),
            (0x80000000,1,False,0x7FFFFFFF,False),
            (0xFFFFFFFF,0xFFFFFFFF,False,0,False),
            (0xFFFFFFFF,0,True,0xFFFFFFFE,False),
        )
        for left,right,borrow,out,t in cases:
            with self.subTest(a=left,b=right,t_in=borrow):
                d=cpu(0x312A);d.r[1]=left;d.r[2]=right;d.t=borrow
                d.execute()
                self.assertEqual(d.r[1],out)
                self.assertIs(d.t,t)
                self.assertEqual(d.r[2],right)

    def test_unknown_incoming_t_stops_before_mutation(self):
        for op in (0x312A,0x312E):
            d=cpu(op);d.r[1]=0xFFFFFFFF;d.r[2]=1
            with self.subTest(op=hex(op)),self.assertRaises(BootStop) as caught:
                d.execute()
            self.assertEqual(caught.exception.kind,"unknown_status")
            self.assertEqual(d.r[1],0xFFFFFFFF)
            self.assertEqual(d.trace[-1]["opcode"],f"{op:04X}")

    def test_missing_operand_stops_without_materialisation(self):
        d=cpu(0x3120);d.r[2]=1
        with self.assertRaises(BootStop) as caught:d.execute()
        self.assertEqual(caught.exception.kind,"unknown_register")
        self.assertIsNone(d.r[1])
