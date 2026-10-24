import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class MuluWordTests(unittest.TestCase):
    def test_unsigned_low_words_product_and_unchanged_state(self):
        values=(0,1,0x7FFF,0x8000,0xFFFF,0xFFFF1234,0x1234FFFF)
        for a in values:
            for b in values:
                d=program(0x201E);d.r[0]=a;d.r[1]=b;d.mach=0xAABBCCDD;d.t=None
                d.execute()
                self.assertEqual(d.macl,(a%65536)*(b%65536))
                self.assertEqual(d.mach,0xAABBCCDD);self.assertIsNone(d.t)
                self.assertEqual(d.r[:2],[a,b])
        d=program(0x200E);d.r[0]=65535;d.execute()
        self.assertEqual(d.macl,4294836225)

    def test_upper_unknown_bits_irrelevant_low_unknown_stops_atomic(self):
        d=program(0x201E);d.r[0]=KnownBits(0x8000,0xFFFF);d.r[1]=KnownBits(0xFFFF,0xFFFF)
        d.execute();self.assertEqual(d.macl,2147450880)
        for value in (None,KnownBits(1,0xFFFFFFFE)):
            d=program(0x201E);d.r[0]=value;d.r[1]=1;d.macl=99;d.t=True
            r=d.run(1)
            self.assertEqual(r['stop']['reason'],'unknown_register')
            self.assertEqual(d.macl,99);self.assertTrue(d.t);self.assertEqual(d.clock.ticks,0)
