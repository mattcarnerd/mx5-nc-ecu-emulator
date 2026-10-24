import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import NCBootDiagnostic,BootStop
from ecu_workbench.hcan import MCR_ADDRESSES,GSR_ADDRESSES,MBIMR_ADDRESSES

class StaticCanLatchTests(unittest.TestCase):
    def cpu(self):
        return NCBootDiagnostic(program(0x0009).bus.image,
            hcan_fixture={'reset_completion_ticks':1,'recessive_bus_ticks':64,'defer_mailbox_effects':True})

    def test_software_mask_retains_only_its_cpu_reset_derived_value(self):
        d=self.cpu();b=d.bus
        b.write(MBIMR_ADDRESSES[0],2,0xFFFE)
        b.write(0xFFFFD104,2,0x2308)
        self.assertEqual(b.read(MBIMR_ADDRESSES[0],2),0xFFFE)
        b.write(MBIMR_ADDRESSES[0],2,0xFFFC)
        self.assertEqual(b.read(MBIMR_ADDRESSES[0],2),0xFFFC)
        self.assertEqual(b.read(MBIMR_ADDRESSES[2],2),0xFFFF)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
        self.assertTrue(b.hcan.effect_unknown_channels[0])
        self.assertEqual(b.hcan.unresolved_command_count,1)
        with self.assertRaises(BootStop):b.read(0xFFFFD104,2)

    def test_pending_reset_mask_is_not_reconstructed_from_constant(self):
        d=self.cpu();b=d.bus
        b.write(MCR_ADDRESSES[0],2,1)
        b.write(0xFFFFD104,2,0x2308)
        with self.assertRaises(BootStop):b.read(MBIMR_ADDRESSES[0],2)
        d.clock.completed_instruction()
        with self.assertRaises(BootStop):b.read(MBIMR_ADDRESSES[0],2)
        b.write(MBIMR_ADDRESSES[0],2,0x1234)
        self.assertEqual(b.read(MBIMR_ADDRESSES[0],2),0x1234)
        self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
