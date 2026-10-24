import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootBus,BootStop,NCBootDiagnostic
from ecu_workbench.hcan import MCR_ADDRESSES,BCR_MASKS

class HcanConfigurationTests(unittest.TestCase):
    def test_latches_masks_constraints_and_channel_isolation(self):
        b=program(0x0009).bus
        for channel,base in enumerate(MCR_ADDRESSES):
            b.write(base+4,2,0xE320);b.write(base+6,2,1)
            self.assertEqual(b.read_cpu_word(base+4).value,0xE320)
            self.assertEqual(b.read_cpu_word(base+4).mask,0xF733)
            self.assertEqual(b.read_cpu_word(base+6).mask,255)
            config=b.hcan.bit_configuration(channel)
            self.assertTrue(config['valid_constraints'])
            self.assertEqual(config['segment1_quanta'],15)
            self.assertEqual(config['segment2_quanta'],4)
            self.assertEqual(config['sjw_quanta'],3)
            self.assertIsNone(config['baud_hz'])
            with self.assertRaises(BootStop):b.read(base+4,2)
        b.write(MCR_ADDRESSES[0]+4,2,0x4130)
        self.assertFalse(b.hcan.bit_configuration(0)['valid_constraints'])
        self.assertTrue(b.hcan.bit_configuration(1)['valid_constraints'])

    def test_bad_sizes_reserved_and_prohibited_fields_atomic(self):
        b=program(0x0009).bus
        before=dict(b.hcan.bcr)
        for a in BCR_MASKS:
            for width in (1,4):
                with self.assertRaises(BootStop):b.write(a,width,0)
            with self.assertRaises(BootStop):b.write(a+1,1,0)
            with self.assertRaises(BootStop):b.write(a,2,0x800 if a&7==4 else 256)
            self.assertEqual(b.hcan.bcr,before)
        for value in (0,0x1200,0xE000):
            with self.assertRaises(BootStop):b.write(MCR_ADDRESSES[0]+4,2,value)

    def test_reset_completion_is_explicit_and_configuration_window_matters(self):
        image=program(0x0009).bus.image
        b=BootBus(image,power_on=False)
        with self.assertRaises(BootStop):b.write(MCR_ADDRESSES[0]+4,2,0xE320)
        d=NCBootDiagnostic(image,hcan_fixture={'reset_completion_ticks':1,'recessive_bus_ticks':4})
        b=d.bus;b.write(MCR_ADDRESSES[0]+4,2,0xE320);b.write(MCR_ADDRESSES[0],2,1)
        self.assertEqual(b.read_cpu_word(MCR_ADDRESSES[0]+4).mask,0)
        d.clock.completed_instruction()
        self.assertEqual(b.read_cpu_word(MCR_ADDRESSES[0]+4).value,0)
        self.assertEqual(b.read_cpu_word(MCR_ADDRESSES[0]+4).mask,0xF733)
        b.write(MCR_ADDRESSES[0],2,0)
        b.write(MCR_ADDRESSES[0]+4,2,0xE320)
        for _ in range(4):d.clock.completed_instruction()
        with self.assertRaises(BootStop):b.write(MCR_ADDRESSES[0]+6,2,1)
