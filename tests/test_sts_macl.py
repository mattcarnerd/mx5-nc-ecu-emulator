import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class StsMaclTests(unittest.TestCase):
    def test_product_transfer_all_destinations_without_inhibit(self):
        for n in range(16):
            d=program(0x001A|(n<<8));d.macl=0xFFF00001;d.mach=42;d.t=True
            d.execute()
            self.assertEqual(d.r[n],0xFFF00001)
            self.assertEqual(d.macl,0xFFF00001);self.assertEqual(d.mach,42);self.assertTrue(d.t)
            self.assertEqual(d._interrupt_inhibit,0)
        d=program(0x201E,0x021A);d.r[0]=0xFFFF;d.r[1]=0xFFFF
        d.run(2);self.assertEqual(d.r[2],4294836225)

    def test_reset_undefined_macl_is_not_invented(self):
        d=program(0x001A,0x7001);r=d.run(2)
        self.assertEqual(d.r[0],KnownBits(0,0))
        self.assertIsNone(d.macl)
        self.assertEqual(r['stop']['reason'],'unknown_register')
        self.assertEqual(d.clock.ticks,1)
