import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootStop
from ecu_workbench.ubc import UserBreakConfig,BASE

class UserBreakConfigurationTests(unittest.TestCase):
    def test_big_endian_overlapping_accesses_and_reserved_masks(self):
        b=program(0x0009).bus;b.write(0xFFFFF70A,2,0x3C04)
        b.write(BASE,4,0x7FFFFFFF)
        self.assertEqual(b.read(BASE,2),0x7FFF);self.assertEqual(b.read(BASE+1,1),0xFF)
        b.write(BASE+2,1,0x12);self.assertEqual(b.read(BASE,4),0x7FFF12FF)
        b.write(BASE+4,4,0xFFFFFFFF);self.assertEqual(b.read(BASE+4,4),0xFFFFFFFF)
        b.write(BASE+8,4,0x00400007);self.assertEqual(b.read(BASE+8,4),0x00400007)

    def test_active_unknown_reserved_and_badwidth_fail_atomically(self):
        u=UserBreakConfig(power_on=True,trace=[],stop_type=BootStop)
        for address,width,value in ((BASE+8,4,0x00FF0001),(BASE+8,4,0x01000000),
                                    (BASE+10,2,8),(BASE+9,2,0),(BASE+10,4,0)):
            before=(bytes(u.data),bytes(u.valid))
            with self.assertRaises(BootStop):u.access(address,width,'write',value,syscr2=4)
            self.assertEqual((bytes(u.data),bytes(u.valid)),before)
        m=UserBreakConfig(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.access(BASE,4,'write',1,syscr2=4)
        with self.assertRaises(BootStop):m.access(BASE,4,'read',syscr2=None)

    def test_module_stop_reset_and_guard(self):
        b=program(0x0009).bus
        with self.assertRaises(BootStop):b.read(BASE,4)
        b.write(0xFFFFF70A,2,0x3C04);b.write(BASE,4,0x12345678)
        b.write(0xFFFFF70A,2,0x3C05)
        with self.assertRaises(BootStop):b.write(BASE,4,1)
        b.write(0xFFFFF70A,2,0x3C04);self.assertEqual(b.read(BASE,4),0)
