import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootStop,NCBootDiagnostic
from ecu_workbench.hcan import MCR_ADDRESSES

class MailboxDataTests(unittest.TestCase):
    def test_bytes_words_overlap_endianness_all_mailboxes_and_channels(self):
        b=program(0x0009).bus
        for base in (0xFFFFD100,0xFFFFD900):
            for mailbox in range(32):
                a=base+32*mailbox+8
                b.write(a,2,0x1234);b.write(a+1,1,0xAB)
                self.assertEqual([b.hcan.mailbox_data_writes[a+i] for i in range(2)],[0x12,0xAB])
                for i in range(8):b.write(a+i,1,0x80+i)
                self.assertEqual([b.hcan.mailbox_data_writes[a+i] for i in range(8)],list(range(0x80,0x88)))
                with self.assertRaises(BootStop):b.read(a,2)
        self.assertEqual(len(b.hcan.mailbox_data_writes),512)
        self.assertEqual(b.hcan.release_requests,[False,False])

    def test_data_writes_do_not_broaden_control_timestamp_gaps_or_long_access(self):
        b=program(0x0009).bus
        for a,w in ((0xFFFFD104,1),(0xFFFFD106,1),(0xFFFFD108,4),(0xFFFFD10F,2),
                    (0xFFFFD110,1),(0xFFFFD114,2)):
            with self.assertRaises(BootStop):b.write(a,w,0)
        self.assertEqual(b.hcan.mailbox_data_writes,{})
        d=NCBootDiagnostic(b.image,hcan_fixture={'reset_completion_ticks':1,'recessive_bus_ticks':None})
        d.bus.write(0xFFFFD108,1,0xAB);d.bus.write(MCR_ADDRESSES[0],2,1);d.clock.completed_instruction()
        self.assertEqual(d.bus.hcan.mailbox_data_writes[0xFFFFD108],0xAB)
