import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootBus,BootStop,NCBootDiagnostic
from ecu_workbench.core import ROMImage
from ecu_workbench.hcan import MCR_ADDRESSES

class HcanCommandTests(unittest.TestCase):
    def test_both_reset_release_commands_record_requests_only(self):
        b=BootBus(program(0x0009).bus.image)
        self.assertEqual(b.hcan.commands,[1,1])
        for channel,address in enumerate(MCR_ADDRESSES):
            b.write(address,2,0)
            self.assertEqual(b.hcan.commands[channel],0);self.assertTrue(b.hcan.release_requests[channel])
            event=b.peripheral_trace[-1]
            self.assertEqual(event['register'],f'MCR_{channel}')
            self.assertEqual(event['bus_synchronization'],'unknown')
        with self.assertRaises(BootStop) as c:b.read(MCR_ADDRESSES[0]+2,2)
        self.assertEqual(c.exception.kind,'unmodelled_peripheral')

    def test_manual_prior_state_and_readback_are_not_invented(self):
        b=BootBus(program(0x0009).bus.image,power_on=False)
        self.assertEqual(b.hcan.commands,[None,None])
        b.write(MCR_ADDRESSES[0],2,0);self.assertEqual(b.hcan.commands,[0,None])
        with self.assertRaises(BootStop) as c:b.read(MCR_ADDRESSES[0],2)
        self.assertEqual(c.exception.kind,'unknown_peripheral_reset_state')
        self.assertIn('bit6',str(c.exception))

    def test_bad_width_and_unimplemented_modes_are_atomic(self):
        b=BootBus(program(0x0009).bus.image)
        for address in MCR_ADDRESSES:
            for width,value in ((1,0),(4,0),(2,1),(2,2),(2,0xFFFF)):
                with self.assertRaises(BootStop):b.write(address,width,value)
                self.assertEqual(b.hcan.commands,[1,1]);self.assertEqual(b.peripheral_trace,[])
            with self.assertRaises(BootStop):b.write(address+1,2,0)

    def test_observed_opcode_2341_store(self):
        d=program(0xD303,0xE400,0x2341,0x0009);data=bytearray(d.bus.image.data)
        data[0x110:0x114]=MCR_ADDRESSES[0].to_bytes(4,'big')
        d=NCBootDiagnostic(ROMImage('synthetic',bytes(data)));r=d.run(4)
        self.assertTrue(d.bus.hcan.release_requests[0]);self.assertEqual(r['stop']['reason'],'instruction_limit')
        self.assertFalse(r['boot_complete'])

    def test_mailbox_zero_initialization_all_documented_words(self):
        b=BootBus(program(0x0009).bus.image)
        self.assertEqual(b.hcan.mailbox_writes,{})
        for base in (0xFFFFD100,0xFFFFD900):
            for mailbox in range(32):
                for offset in range(0,20,2):
                    address=base+mailbox*32+offset
                    b.write(address,2,0)
                    self.assertEqual(b.hcan.mailbox_writes[address],0)
        self.assertEqual(len(b.hcan.mailbox_writes),640)
        self.assertEqual(len(b.peripheral_trace),640)
        with self.assertRaises(BootStop):b.read(0xFFFFD100,2)

    def test_mailbox_gaps_width_values_and_isolation(self):
        b=BootBus(program(0x0009).bus.image,power_on=False)
        for address,width,value in ((0xFFFFD114,2,0),(0xFFFFD11E,2,0),
                                    (0xFFFFD101,2,0),(0xFFFFD100,4,0),
                                    (0xFFFFD108,1,0),(0xFFFFD100,2,1)):
            with self.assertRaises(BootStop):b.write(address,width,value)
            self.assertEqual(b.hcan.mailbox_writes,{})
        b.write(0xFFFFD100,2,0)
        self.assertNotIn(0xFFFFD900,b.hcan.mailbox_writes)
        self.assertEqual(BootBus(program(0x0009).bus.image).hcan.mailbox_writes,{})
