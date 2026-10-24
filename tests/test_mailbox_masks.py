import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootBus,BootStop,NCBootDiagnostic
from ecu_workbench.hcan import MBIMR_ADDRESSES,MCR_ADDRESSES

class MailboxMaskTests(unittest.TestCase):
    def test_power_reset_rmw_each_bit_and_channel_word_isolation(self):
        b=program(0x0009).bus
        for a in MBIMR_ADDRESSES:
            self.assertEqual(b.read(a,2),0xFFFF)
            for bit in range(16):
                value=0xFFFF^(1<<bit);b.write(a,2,value)
                self.assertEqual(b.read(a,2),value)
            b.write(a,2,0);self.assertEqual(b.read(a,2),0)
        self.assertTrue(all(v==0 for v in b.hcan.mbimr.values()))
        self.assertEqual(b.hcan.mailbox_writes,{})
        self.assertFalse(any(b.hcan.release_requests))

    def test_bad_access_manual_unknown_and_supplied_reset(self):
        image=program(0x0009).bus.image;b=BootBus(image,power_on=False)
        for a in MBIMR_ADDRESSES:
            with self.assertRaises(BootStop):b.read(a,2)
            for width in (1,4):
                with self.assertRaises(BootStop):b.write(a,width,0)
            with self.assertRaises(BootStop):b.read(a+1,1)
            self.assertIsNone(b.hcan.mbimr[a])
        d=NCBootDiagnostic(image,hcan_fixture={'reset_completion_ticks':1,'recessive_bus_ticks':None})
        d.bus.write(MBIMR_ADDRESSES[0],2,0);d.bus.write(MCR_ADDRESSES[0],2,1)
        with self.assertRaises(BootStop):d.bus.read(MBIMR_ADDRESSES[0],2)
        d.clock.completed_instruction()
        self.assertEqual(d.bus.read(MBIMR_ADDRESSES[0],2),0xFFFF)
        self.assertEqual(d.bus.read(MBIMR_ADDRESSES[2],2),0xFFFF)
