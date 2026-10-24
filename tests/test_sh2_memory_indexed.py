"""B06 SH-2E indexed/displacement MOV form tests, synthetic ROM only."""
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import NCBootDiagnostic, BootStop, RAM_BASE, ROM_LIMIT

def cpu(op):
    binary=bytearray(ROM_LIMIT)
    for i,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        binary[i*4:i*4+4]=v.to_bytes(4,"big")
    binary[0x100:0x102]=op.to_bytes(2,"big")
    return NCBootDiagnostic(ROMImage("synthetic",bytes(binary)))

class IndexedMovTests(unittest.TestCase):
    def test_indexed_store_and_sign_extended_load_all_sizes(self):
        for width,store,load,source,expected in (
            (1,0x0124,0x031C,0xFE,0xFFFFFFFE),
            (2,0x0125,0x031D,0xFFFE,0xFFFFFFFE),
            (4,0x0126,0x031E,0x89ABCDEF,0x89ABCDEF),
        ):
            with self.subTest(width=width):
                a=cpu(store);a.r[0]=4;a.r[1]=RAM_BASE+0x100;a.r[2]=source
                a.execute()
                self.assertEqual(a.bus.read(RAM_BASE+0x104,width),source)
                b=cpu(load);b.r[0]=4;b.r[1]=RAM_BASE+0x100
                b.bus.write(RAM_BASE+0x104,width,source)
                b.execute()
                self.assertEqual(b.r[3],expected)

    def test_long_displacement_load_and_store(self):
        a=cpu(0x1122);a.r[1]=RAM_BASE+0x100;a.r[2]=0x9ABCDEF0
        a.execute()
        self.assertEqual(a.bus.read(RAM_BASE+0x108,4),0x9ABCDEF0)
        b=cpu(0x5312);b.r[1]=RAM_BASE+0x100
        b.bus.write(RAM_BASE+0x108,4,0xFEDCBA98)
        b.execute();self.assertEqual(b.r[3],0xFEDCBA98)

    def test_byte_word_short_displacements(self):
        for store,load,width,val,result in (
            (0x8014,0x8414,1,0xFE,0xFFFFFFFE),
            (0x8114,0x8514,2,0xFFFE,0xFFFFFFFE),
        ):
            with self.subTest(store=hex(store)):
                a=cpu(store);a.r[1]=RAM_BASE+0x100;a.r[0]=val;a.execute()
                self.assertEqual(a.bus.read(RAM_BASE+0x100+4*width,width),val)
                b=cpu(load);b.r[1]=RAM_BASE+0x100
                b.bus.write(RAM_BASE+0x100+4*width,width,val)
                b.execute();self.assertEqual(b.r[0],result)

    def test_unmapped_or_misaligned_does_not_commit_destination(self):
        for op,base_reg in ((0x031D,1),(0x5311,1),(0x8414,1)):
            d=cpu(op);d.r[0]=0;d.r[1]=0x100001
            d.r[3]=0xA5A5A5A5
            with self.subTest(op=hex(op)),self.assertRaises(BootStop):
                d.execute()
            self.assertEqual(d.r[3],0xA5A5A5A5)
        d=cpu(0x1120);d.r[1]=0x12345678;d.r[2]=1
        with self.assertRaises(BootStop) as c:d.execute()
        self.assertEqual(c.exception.kind,"unmapped_memory")

    def test_undefined_base_register_stops(self):
        d=cpu(0x0124);d.r[2]=0xAA
        with self.assertRaises(BootStop) as c:d.execute()
        self.assertEqual(c.exception.kind,"unknown_register")
