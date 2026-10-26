import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootBus,BootStop
from ecu_workbench.known_bits import KnownBits
from ecu_workbench.hcan import RECEIVE_FIXED,ACK_FIXED

class CanReceiveStatusTests(unittest.TestCase):
    def test_all_bits_valid_w1c_preserves_other_flags_no_frames(self):
        b=program(0x0009).bus
        for a in RECEIVE_FIXED:
            self.assertEqual(b.read(a,2),0)
            for bit in range(16):
                b.hcan.mailbox_flags[a]=KnownBits(0xFFFF,0xFFFF)
                b.write(a,2,1<<bit)
                self.assertEqual(b.read(a,2),0xFFFF^(1<<bit))
            b.write(a,2,0xFFFF);self.assertEqual(b.read(a,2),0)
        for a,fixed in ACK_FIXED.items():self.assertEqual(b.read(a,2)&fixed,0)
        self.assertEqual(b.hcan.mailbox_writes,{})

    def test_manual_unknown_and_clear_derived_knowledge(self):
        b=BootBus(program(0x0009).bus.image,power_on=False)
        for a in RECEIVE_FIXED:
            self.assertEqual(b.read_cpu_word(a).mask,0)
            with self.assertRaises(BootStop):b.read(a,2)
            b.write(a,2,0);self.assertEqual(b.read_cpu_word(a).mask,0)
            b.write(a,2,1);self.assertEqual(b.read_cpu_word(a).mask,1)
            b.write(a,2,0xFFFE);self.assertEqual(b.read(a,2),0)

    def test_word_only_guards_and_bank_channel_isolation(self):
        b=program(0x0009).bus
        for a in RECEIVE_FIXED:
            for width in (1,4):
                with self.assertRaises(BootStop):b.write(a,width,0)
            with self.assertRaises(BootStop):b.read(a+1,1)
        first=list(RECEIVE_FIXED)[0];b.hcan.mailbox_flags[first]=KnownBits(0x8001,0xFFFF)
        b.write(first,2,1);self.assertEqual(b.read(first,2),0x8000)
        self.assertTrue(all(bits.value==0 for a,bits in b.hcan.mailbox_flags.items() if a!=first))
