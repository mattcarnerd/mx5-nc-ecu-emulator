import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootStop

class DecrementTest(unittest.TestCase):
    def test_all_registers_boundary_results_and_other_status(self):
        for n in range(16):
            for value,result in ((0,0xFFFFFFFF),(1,0),(2,1),(0x80000000,0x7FFFFFFF),(0xFFFFFFFF,0xFFFFFFFE)):
                d=program(0x4010|(n<<8));d.r[n]=value
                d.known_sr_mask=0x3F2;d.known_sr_value=0x3F2;d.t=None
                d.run(1)
                self.assertEqual(d.r[n],result);self.assertEqual(d.t,result==0)
                self.assertEqual((d.known_sr_mask,d.known_sr_value),(0x3F2,0x3F2))
                self.assertEqual(d.pc,0x102);self.assertEqual(d.clock.ticks,1)

    def test_unknown_register_preserves_register_status_and_clock(self):
        d=program(0x4710);d.r[7]=None;d.t=True
        result=d.run(1)
        self.assertEqual(result['stop']['reason'],'unknown_register')
        self.assertIsNone(d.r[7]);self.assertTrue(d.t);self.assertEqual(d.clock.ticks,0)

    def test_loop_and_delay_slot(self):
        d=program(0x4710,0x8BFD,0x0009);d.r[7]=3
        d.run(7)
        self.assertEqual(d.r[7],0);self.assertTrue(d.t);self.assertEqual(d.pc,0x106)
        d=program(0xA001,0x4710,0xE001,0x0009);d.r[7]=1
        d.run(2)
        self.assertEqual(d.pc,0x106);self.assertEqual(d.r[7],0);self.assertTrue(d.t)
        self.assertTrue(d.trace[-1]['delay_slot'])
