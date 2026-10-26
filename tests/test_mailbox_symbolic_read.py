import unittest
from ecu_workbench.nc_boot import BootStop
from ecu_workbench.known_bits import KnownBits
from test_sh2_branch import program

class MailboxSymbolicReadTests(unittest.TestCase):
    def test_both_channels_and_all_mailboxes_remain_unknown(self):
        c=program(0x0009)
        for base in (0xFFFFD100,0xFFFFD900):
            for box in range(32):
                address=base+32*box+4
                for offset,width in ((0,2),(0,1),(1,1)):
                    b=c.bus.read_cpu_value(address+offset,width)
                    self.assertEqual(b.mask,0xFFFFFFFF ^ ((1<<(8*width))-1))
                    with self.assertRaises(BootStop):c.bus.read(address+offset,width)

    def test_accepted_and_unresolved_commands_never_become_readback(self):
        c=program(0x0009);h=c.bus.hcan
        h.mailbox_write(0xFFFFD104,2,0x2700)
        self.assertEqual(h.mailbox_control_known(0xFFFFD104,2).mask,0xFFFF0000)
        h.record_unresolved_mailbox(0xFFFFD104,2,0x2308,'invalid_peripheral_write')
        self.assertEqual(h.mailbox_control_known(0xFFFFD104,2).mask,0xFFFF0000)

    def test_cpu_can_discard_unknown_value_but_cannot_store_it(self):
        c=program(0x6231,0xE400,0x2249,0x2521)
        c.r[3]=0xFFFFD104;c.r[5]=0xFFFFD124
        r=c.run(4)
        self.assertEqual(r['completed_instructions'],4)
        self.assertEqual(c.bus.hcan.mailbox_writes[0xFFFFD124],0)
        c=program(0x6231,0x2521);c.r[3]=0xFFFFD104;c.r[5]=0xFFFFD124
        r=c.run(2)
        self.assertEqual(r['completed_instructions'],1)
        self.assertEqual(r['stop']['reason'],'unknown_register')
        self.assertNotIn(0xFFFFD124,c.bus.hcan.mailbox_writes)

    def test_width_and_unrelated_mailbox_reads_still_guarded(self):
        c=program(0x0009)
        for address,width in ((0xFFFFD104,4),(0xFFFFD105,2),(0xFFFFD106,2)):
            with self.assertRaises(BootStop):c.bus.read_cpu_value(address,width)
