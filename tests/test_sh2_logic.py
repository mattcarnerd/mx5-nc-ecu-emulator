"""B08 synthetic SH-2 logical and T-bit tests."""
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import NCBootDiagnostic, BootStop, ROM_LIMIT

def cpu(op):
    data=bytearray(ROM_LIMIT)
    for i,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        data[4*i:4*i+4]=v.to_bytes(4,"big")
    data[0x100:0x102]=op.to_bytes(2,"big")
    return NCBootDiagnostic(ROMImage("synthetic",bytes(data)))

class LogicTests(unittest.TestCase):
    def test_register_operators_and_preserved_t(self):
        for op,left,right,expected in (
            (0x2129,0xF0F0FFFF,0xF00F0F0F,0xF0000F0F),
            (0x212A,0xFFFFFFFF,0x12345678,0xEDCBA987),
            (0x212B,0xF0000000,0x0000000F,0xF000000F),
        ):
            with self.subTest(op=hex(op)):
                d=cpu(op);d.r[1]=left;d.r[2]=right;d.t=True
                d.execute()
                self.assertEqual(d.r[1],expected)
                self.assertEqual(d.r[2],right)
                self.assertIs(d.t,True)

    def test_tst_does_not_modify_any_register(self):
        for op,left,right,expected in (
            (0x2128,0xF000,0x0F00,True),
            (0x2128,0xFFFF,0xF000,False),
        ):
            d=cpu(op);d.r[1]=left;d.r[2]=right;d.t=None
            d.execute();self.assertIs(d.t,expected)
            self.assertEqual(d.r[1],left)
            self.assertEqual(d.r[2],right)

    def test_immediate_logical_zero_extension(self):
        for op,initial,expected in (
            (0xC9F0,0x12345678,0x00000070),
            (0xCAFF,0xFFFFFFFF,0xFFFFFF00),
            (0xCB05,0xFFFFFF00,0xFFFFFF05),
        ):
            with self.subTest(op=hex(op)):
                d=cpu(op);d.r[0]=initial;d.t=None
                d.execute()
                self.assertEqual(d.r[0],expected)
                self.assertIsNone(d.t)

    def test_immediate_tst_sets_t_without_modifying_r0(self):
        for r0,imm,expected in ((0xFF,0x0F,False),(0xF0,0x0F,True),(0,0,True)):
            d=cpu(0xC800|imm);d.r[0]=r0
            d.execute()
            self.assertEqual(d.r[0],r0)
            self.assertIs(d.t,expected)

    def test_unknown_register_does_not_materialize_state(self):
        d=cpu(0x2129);d.r[2]=0x55
        with self.assertRaises(BootStop) as cm:d.execute()
        self.assertEqual(cm.exception.kind,"unknown_register")
        self.assertIsNone(d.r[1])

    def test_unsupported_memory_immediate_stays_fail_closed(self):
        d=cpu(0xCCFF);d.r[0]=0
        with self.assertRaises(BootStop) as cm:d.execute()
        self.assertEqual(cm.exception.kind,"unsupported_opcode")
