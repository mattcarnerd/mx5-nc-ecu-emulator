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
        self.assertEqual(c.exception.kind,'unknown_peripheral_reset_state')

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
            for width,value in ((1,0),(4,0),(2,0x40),(2,2),(2,0xFFFF)):
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

    def test_inactive_control_all_mailboxes_without_can_events(self):
        b=BootBus(program(0x0009).bus.image)
        for base in (0xFFFFD100,0xFFFFD900):
            for mailbox in range(32):
                a=base+32*mailbox+4
                for value in (0x700,0x2700):
                    b.write(a,2,value)
                    self.assertEqual(b.hcan.mailbox_writes[a],value)
                    self.assertEqual(b.peripheral_trace[-1]['scope'],'mailbox_inactive_command')
                    self.assertEqual(b.peripheral_trace[-1]['configuration_note'] is not None,value==0x2700)
                for value in (0x300,0x600,0x4700,0xA700,0x2701):
                    with self.assertRaises(BootStop):b.write(a,2,value)
                    self.assertEqual(b.hcan.mailbox_writes[a],0x2700)
        with self.assertRaises(BootStop):b.write(0xFFFFD102,2,0x2700)
        with self.assertRaises(BootStop):b.read(0xFFFFD104,2)

    def test_software_reset_command_channels_history_and_unknown_completion(self):
        for power in (False,True):
            b=BootBus(program(0x0009).bus.image,power_on=power,experimental_mcr_bit6=0)
            b.write(0xFFFFD104,2,0x2700);b.write(0xFFFFD904,2,0x700)
            history=dict(b.hcan.mailbox_writes)
            for channel,address in enumerate(MCR_ADDRESSES):
                b.write(address,2,0);b.write(address,2,1);b.write(address,2,1)
                self.assertTrue(b.hcan.software_reset_requests[channel])
                self.assertFalse(b.hcan.release_requests[channel])
                self.assertEqual(b.read(address,2),1)
                self.assertEqual(b.hcan.mailbox_writes,history)
                event=[x for x in b.peripheral_trace if x.get('scope')=='CAN_software_reset_request_only'][-1]
                self.assertEqual(event['value'],1)
                self.assertEqual(event['reset_processing'],'unknown')
                self.assertEqual(event['bus_synchronization'],'unknown')
                with self.assertRaises(BootStop):b.read(address+2,2)
            b.write(MCR_ADDRESSES[0],2,0)
            self.assertEqual(b.hcan.commands,[0,1])
            self.assertEqual(b.hcan.release_requests,[True,False])
            self.assertEqual(b.hcan.software_reset_requests,[True,True])
            with self.assertRaises(BootStop):b.read(0xFFFFD104,2)
