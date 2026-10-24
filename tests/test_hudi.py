import unittest
from test_port_l import image
from ecu_workbench.nc_boot import BootBus,BootStop

class HudiTests(unittest.TestCase):
    def test_power_and_manual_res_do_not_initialize_hudi(self):
        for power in (True,False):
            b=BootBus(image(),power_on=power)
            self.assertEqual(b.read(0xFFFFF7C2,1),0x0B)
            with self.assertRaises(BootStop) as c:b.read(0xFFFFF7C2,2)
            self.assertEqual(c.exception.kind,'unknown_peripheral_reset_state')
            self.assertIn('TRST',str(c.exception))
            with self.assertRaises(BootStop):b.read(0xFFFFF7C3,1)

    def test_explicit_trst_and_serial_events(self):
        b=BootBus(image());b.hudi.trst_reset()
        self.assertEqual(b.read(0xFFFFF7C2,2),0x0B01)
        self.assertEqual(b.read(0xFFFFF7C3,1),1)
        b.hudi.serial_transfer_completed()
        self.assertEqual(b.read(0xFFFFF7C2,2),0x0B00)
        b.write(0xFFFFF7C3,1,1)
        self.assertEqual(b.read(0xFFFFF7C2,2),0x0B01)
        b.write(0xFFFFF7C2,2,0x0B00)
        self.assertEqual(b.read(0xFFFFF7C2,2),0x0B01)

    def test_byte_writes_and_unknown_flag(self):
        b=BootBus(image());b.write(0xFFFFF7C2,1,0x0B)
        self.assertIsNone(b.hudi.sdtrf)
        b.write(0xFFFFF7C3,1,0);self.assertIsNone(b.hudi.sdtrf)
        b.write(0xFFFFF7C2,2,0x0B01);self.assertIs(b.hudi.sdtrf,True)

    def test_invalid_writes_and_widths_do_not_invent_state(self):
        b=BootBus(image())
        for a,w,v in ((0xFFFFF7C2,2,0),(0xFFFFF7C2,2,0xFFFF),
                      (0xFFFFF7C2,1,0),(0xFFFFF7C3,1,2),
                      (0xFFFFF7C2,4,0x0B01),(0xFFFFF7C3,2,1)):
            with self.assertRaises(BootStop):b.write(a,w,v)
            self.assertIsNone(b.hudi.sdtrf);self.assertEqual(b.peripheral_trace,[])
        with self.assertRaises(BootStop):b.read(0xFFFFF7C2,4)
        with self.assertRaises(BootStop) as c:b.read(0xFFFFF7C0,4)
        self.assertEqual(c.exception.kind,'unmodelled_peripheral')
