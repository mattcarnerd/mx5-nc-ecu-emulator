import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class ComparePositiveTests(unittest.TestCase):
    def test_signed_boundaries_and_all_registers_preserve_operand(self):
        for n in range(16):
            for value,expected in ((0,False),(1,True),(0x7FFFFFFF,True),
                                   (0x80000000,False),(0xFFFFFFFF,False)):
                d=program(0x4015|(n<<8));d.r[n]=value;d.t=None
                d.execute()
                self.assertIs(d.t,expected);self.assertEqual(d.r[n],value)

    def test_unknown_operand_stops_before_t_or_clock_change(self):
        for value in (None,KnownBits(1,0x7FFFFFFF)):
            d=program(0x4A15);d.r[10]=value;d.t=True
            r=d.run(1)
            self.assertEqual(r['stop']['reason'],'unknown_register')
            self.assertTrue(d.t);self.assertEqual(d.clock.ticks,0)

    def test_valid_in_branch_delay_slot(self):
        d=program(0xA001,0x4A15,0x0009,0x0009);d.r[10]=1
        r=d.run(2)
        self.assertEqual(r['completed_instructions'],2)
        self.assertTrue(d.t);self.assertEqual(d.pc,0x106)

class CompareNonnegativeTests(unittest.TestCase):
    def test_pz_includes_zero_and_preserves_signed_boundaries(self):
        for n in range(16):
            for value in (0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF):
                d=program(0x4011|(n<<8));d.r[n]=value;d.t=None;d.execute()
                self.assertIs(d.t,value<0x80000000);self.assertEqual(d.r[n],value)

    def test_pz_unknown_and_delay_slot(self):
        for value in (None,KnownBits(0,0xFFFFFFFE)):
            d=program(0x4411);d.r[4]=value;d.t=False;r=d.run(1)
            self.assertEqual(r['stop']['reason'],'unknown_register')
            self.assertFalse(d.t);self.assertEqual(d.clock.ticks,0)
        d=program(0xA001,0x4411,0x0009,0x0009);d.r[4]=0
        r=d.run(2);self.assertEqual(r['completed_instructions'],2)
        self.assertTrue(d.t);self.assertEqual(d.pc,0x106)
