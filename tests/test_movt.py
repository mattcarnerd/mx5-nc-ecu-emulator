import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class MoveTTests(unittest.TestCase):
    def test_all_registers_known_t_and_preservation(self):
        for n in range(16):
            for t in (False,True):
                d=program(0x0029|(n<<8));d.t=t;d.r[n]=0xFFFFFFFF;d.execute()
                self.assertEqual(d.r[n],int(t));self.assertIs(d.t,t)

    def test_unknown_t_transports_only_unknown_low_bit(self):
        d=program(0x0029,0xC900);d.t=None;d.execute()
        self.assertEqual(d.r[0],KnownBits(0,0xFFFFFFFE));self.assertIsNone(d.t)
        d.execute();self.assertEqual(d.reg(0),0)
        d=program(0x0029,0x4015);d.t=None;r=d.run(2)
        self.assertEqual(r['stop']['reason'],'unknown_register');self.assertIsNone(d.t)
        self.assertEqual(r['completed_instructions'],1)

    def test_delay_slot(self):
        d=program(0xA001,0x0029,0x0009,0x0009);d.t=True;r=d.run(2)
        self.assertEqual(r['completed_instructions'],2);self.assertEqual(d.r[0],1)
        self.assertTrue(d.t);self.assertEqual(d.pc,0x106)
