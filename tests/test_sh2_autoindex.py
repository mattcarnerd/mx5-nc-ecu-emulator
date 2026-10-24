"""B07 predecrement/postincrement MOV instructions and aliases."""
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import NCBootDiagnostic, BootStop, RAM_BASE, ROM_LIMIT

def cpu(op):
    b=bytearray(ROM_LIMIT)
    for i,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        b[4*i:4*i+4]=v.to_bytes(4,"big")
    b[0x100:0x102]=op.to_bytes(2,"big")
    return NCBootDiagnostic(ROMImage("synthetic",bytes(b)))

class AutoIndexTests(unittest.TestCase):
    def test_predecrement_store_sizes(self):
        for op,width,value in ((0x2124,1,0xAB),(0x2125,2,0xABCD),(0x2126,4,0x89ABCDEF)):
            with self.subTest(op=hex(op)):
                d=cpu(op);d.r[1]=RAM_BASE+0x100;d.r[2]=value
                d.execute()
                self.assertEqual(d.r[1],RAM_BASE+0x100-width)
                self.assertEqual(d.bus.read(RAM_BASE+0x100-width,width),value)

    def test_postincrement_load_sign_extension_sizes(self):
        for op,width,data,expected in (
            (0x6324,1,0xFE,0xFFFFFFFE),
            (0x6325,2,0xFFFE,0xFFFFFFFE),
            (0x6326,4,0x89ABCDEF,0x89ABCDEF),
        ):
            with self.subTest(op=hex(op)):
                d=cpu(op);d.r[2]=RAM_BASE+0x100
                d.bus.write(RAM_BASE+0x100,width,data)
                d.execute()
                self.assertEqual(d.r[3],expected)
                self.assertEqual(d.r[2],RAM_BASE+0x100+width)

    def test_same_register_store_stores_original_pointer_not_decremented(self):
        d=cpu(0x2116)  # MOV.L R1,@-R1
        d.r[1]=RAM_BASE+0x100
        d.execute()
        self.assertEqual(d.r[1],RAM_BASE+0xFC)
        self.assertEqual(d.bus.read(RAM_BASE+0xFC,4),RAM_BASE+0x100)

    def test_same_register_postincrement_does_not_increment(self):
        d=cpu(0x6116)  # MOV.L @R1+,R1
        d.r[1]=RAM_BASE+0x100
        d.bus.write(RAM_BASE+0x100,4,0x12345678)
        d.execute()
        self.assertEqual(d.r[1],0x12345678)

    def test_postincrement_failed_read_keeps_registers_and_reports_stop(self):
        d=cpu(0x6325);d.r[2]=RAM_BASE+0x100;d.r[3]=0x7777
        with self.assertRaises(BootStop) as caught:d.execute()
        self.assertEqual(caught.exception.kind,"uninitialised_ram")
        self.assertEqual(d.r[2],RAM_BASE+0x100)
        self.assertEqual(d.r[3],0x7777)
        self.assertEqual(d.trace[-1]["opcode"],"6325")

    def test_predecrement_updates_base_before_bus_fault(self):
        d=cpu(0x2126);d.r[1]=RAM_BASE;d.r[2]=1
        with self.assertRaises(BootStop) as caught:d.execute()
        self.assertEqual(caught.exception.kind,"unmapped_memory")
        self.assertEqual(d.r[1],RAM_BASE-4)
        self.assertEqual(d.trace[-1]["opcode"],"2126")
