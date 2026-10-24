import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootStop

class MailboxIdentifierTests(unittest.TestCase):
    def test_identifier_words_all_mailboxes_channels_and_reserved(self):
        b=program(0x0009).bus
        for base in (0xFFFFD100,0xFFFFD900):
            for mailbox in range(32):
                a=base+32*mailbox
                for value in (0,0x37,0x7FFF):
                    b.write(a,2,value);self.assertEqual(b.hcan.mailbox_writes[a],value)
                for value in (0,0x1234,0xFFFF):
                    b.write(a+2,2,value);self.assertEqual(b.hcan.mailbox_writes[a+2],value)
                before=dict(b.hcan.mailbox_writes)
                with self.assertRaises(BootStop):b.write(a,2,0x8000)
                self.assertEqual(b.hcan.mailbox_writes,before)
                with self.assertRaises(BootStop):b.read(a,2)
        self.assertEqual(len(b.hcan.mailbox_writes),128)

    def test_gaps_width_and_non_identifier_data_not_broadened(self):
        b=program(0x0009).bus
        for a,w,v in ((0xFFFFD100,4,0x37),(0xFFFFD101,2,0x37),
                      (0xFFFFD114,2,0),(0xFFFFD108,2,1)):
            with self.assertRaises(BootStop):b.write(a,w,v)
        self.assertEqual(b.hcan.mailbox_writes,{})
