import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootStop
from ecu_workbench.syscr1 import SystemControl1,ADDRESS

class SystemControl1Tests(unittest.TestCase):
    def test_power_and_manual_unknowns_then_observed_write(self):
        c=program(0x0009);b=c.bus
        self.assertEqual(b.read_cpu_value(ADDRESS,1).mask,0xFFFFFF7D)
        b.write(ADDRESS,1,1);v=b.read_cpu_value(ADDRESS,1)
        self.assertEqual((v.value,v.mask),(1,0xFFFFFF7F))
        with self.assertRaises(BootStop):b.read(ADDRESS,1)
        m=SystemControl1(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.access(1,'write',1)
        self.assertEqual(m.state.mask,0x3C)

    def test_unsupported_commands_and_widths_are_atomic(self):
        b=program(0x0009).bus;before=b.syscr1.state
        for value in (0,2,3,4,0x40,0x81,0xFF):
            with self.assertRaises(BootStop):b.write(ADDRESS,1,value)
            self.assertEqual(b.syscr1.state,before)
        for width in (2,4):
            with self.assertRaises(BootStop):b.write(ADDRESS,width,1)
            with self.assertRaises(BootStop):b.read_cpu_value(ADDRESS,width)
            self.assertEqual(b.syscr1.state,before)

    def test_cpu_write_read_and_mask_preserve_unknown_oscillator(self):
        c=program(0x2100,0x6010,0xC901)
        c.r[1]=ADDRESS;c.r[0]=1;r=c.run(3)
        self.assertEqual(r['completed_instructions'],3)
        self.assertEqual(c.reg(0),1)
        self.assertFalse(r['boot_complete'])
