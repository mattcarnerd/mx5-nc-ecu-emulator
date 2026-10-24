import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootStop,RAM_BASE,RAM_LIMIT
from ecu_workbench.known_bits import KnownBits

class PartialRamTests(unittest.TestCase):
    def test_partial_big_endian_overlap_and_concrete_overwrite(self):
        b=program(0x0009).bus;a=RAM_BASE+256
        b.write_cpu_value(a,4,KnownBits(0x12345678,0xFF00F00F))
        self.assertEqual(bytes(b.ram_known_mask[256:260]),bytes.fromhex('ff00f00f'))
        for offset,value,mask in ((0,0x12,255),(1,0,0),(2,0x50,0xF0),(3,8,15)):
            r=b.read_cpu_value(a+offset,1)
            self.assertEqual(r.value,value);self.assertEqual(r.mask&255,mask)
        with self.assertRaises(BootStop):b.read(a,4)
        b.write(a+1,1,0xAB);b.write(a+2,2,0xCDEF)
        self.assertEqual(b.read(a,4),0x12ABCDEF)
        b.write_cpu_value(a+1,1,KnownBits(0,0))
        self.assertEqual(b.read_cpu_value(a,4).mask,0xFF00FFFF)
        with self.assertRaises(BootStop):b.read(a,4)

    def test_unwritten_ram_remains_a_stop_and_unknown_store_is_transport(self):
        b=program(0x0009).bus;a=RAM_BASE+32
        with self.assertRaises(BootStop):b.read_cpu_value(a,4)
        b.write_cpu_value(a,4,KnownBits(0,0))
        self.assertEqual(b.read_cpu_value(a,4),KnownBits(0,0))
        self.assertEqual(bytes(b.ram_valid[32:36]),b'\x01'*4)
        with self.assertRaises(BootStop):b.read(a,4)
        b.write(a,4,0xFFFFFFFF);self.assertEqual(b.read(a,4),0xFFFFFFFF)
        self.assertEqual(b.read_cpu_value(a,4).mask,0xFFFFFFFF)

    def test_partial_faults_and_peripheral_guards_are_atomic(self):
        b=program(0x0009).bus;before=bytes(b.ram_valid)
        for address,width in ((RAM_BASE+1,2),(RAM_LIMIT-2,4),(0,4),(0xFFFFD000,2),(0xFFFFF754,2)):
            with self.assertRaises(BootStop):b.write_cpu_value(address,width,KnownBits(0,0))
            self.assertEqual(bytes(b.ram_valid),before)
            self.assertEqual(b.peripheral_trace,[])
        for width in (0,3):
            with self.assertRaises(ValueError):b.write_cpu_value(RAM_BASE,width,KnownBits(0,0))
            with self.assertRaises(ValueError):b.read_cpu_value(RAM_BASE,width)
        with self.assertRaises(BootStop):b.read_cpu_value(RAM_BASE+1,4)

    def test_direct_indexed_displacement_and_copy_preserve_masks(self):
        from ecu_workbench.core import ROMImage
        forms=((0x2120,0x6310,1,0,2),(0x2121,0x6311,2,0,2),(0x2122,0x6312,4,0,2),
               (0x0124,0x031C,1,4,2),(0x0125,0x031D,2,4,2),(0x0126,0x031E,4,4,2),
               (0x1122,0x5312,4,8,2),(0x8014,0x8414,1,4,0),(0x8114,0x8514,2,8,0))
        for store,load,width,offset,source in forms:
            for bits in (KnownBits(0,0),KnownBits(0x81234567,0x7FFF00F7)):
                d=program(store,load);d.r[1]=RAM_BASE+256;d.r[0]=4;d.r[source]=bits
                d.t=True;d.execute()
                self.assertEqual(d.bus.read_cpu_value(RAM_BASE+256+offset,width).value,bits.value&((1<<(8*width))-1))
                d.execute()
                destination=0 if load in (0x8414,0x8514) else 3
                self.assertEqual(d.transport_bits(destination),bits.sign_extend(width))
                self.assertTrue(d.t)
        d=program(0x6103);d.r[0]=None;d.execute()
        self.assertEqual(d.r[1],KnownBits(0,0))

    def test_mov_unknown_addresses_and_partial_peripheral_writes_still_stop(self):
        for op in (0x2122,0x0126,0x1122):
            d=program(op);d.r[1]=KnownBits(RAM_BASE,0xFFFFFFFC);d.r[0]=0;d.r[2]=None
            result=d.run(1)
            self.assertEqual(result['stop']['reason'],'unknown_register')
            self.assertFalse(any(d.bus.ram_valid))
        for op in (0x2121,0x0125,0x1120):
            d=program(op);d.r[1]=0xFFFFD000;d.r[0]=0;d.r[2]=None
            r=d.run(1);self.assertEqual(r['stop']['reason'],'unknown_register')
            self.assertEqual(d.bus.peripheral_trace,[])
