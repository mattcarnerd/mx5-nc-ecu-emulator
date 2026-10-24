import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootBus,BootStop,NCBootDiagnostic
from ecu_workbench.known_bits import KnownBits
from ecu_workbench.hcan import ACK_FIXED,MCR_ADDRESSES

class CanAckStatusTests(unittest.TestCase):
    def test_reset_w1c_truth_and_fixed_receive_only_mailbox_bit(self):
        b=program(0x0009).bus
        for a,fixed in ACK_FIXED.items():
            self.assertEqual(b.read(a,2),0)
            for bit in range(16):
                original=0xA5A5&~fixed
                b.hcan.ack[a]=KnownBits(original,0xFFFF)
                b.write(a,2,1<<bit)
                self.assertEqual(b.read(a,2),original & ~(1<<bit))
            b.write(a,2,0)
            self.assertEqual(b.read(a,2)&fixed,0)
        self.assertEqual(b.hcan.release_requests,[False,False])

    def test_unknown_bits_clear_to_known_without_selecting_other_values(self):
        b=BootBus(program(0x0009).bus.image,power_on=False)
        for a,fixed in ACK_FIXED.items():
            self.assertEqual(b.read_cpu_word(a).mask,fixed)
            with self.assertRaises(BootStop):b.read(a,2)
            b.write(a,2,0);self.assertEqual(b.read_cpu_word(a).mask,fixed)
            b.write(a,2,0xFFFE);self.assertEqual(b.read_cpu_word(a).mask,0xFFFE|fixed)
            b.write(a,2,1);self.assertEqual(b.read(a,2),0)

    def test_width_guard_reset_phase_and_no_synthetic_success_flags(self):
        image=program(0x0009).bus.image
        d=NCBootDiagnostic(image,hcan_fixture={'reset_completion_ticks':1,'recessive_bus_ticks':None})
        for a in ACK_FIXED:
            for width in (1,4):
                with self.assertRaises(BootStop):d.bus.write(a,width,0)
            with self.assertRaises(BootStop):d.bus.read(a+1,1)
        d.bus.write(MCR_ADDRESSES[0],2,1)
        self.assertEqual(d.bus.read_cpu_word(0xFFFFD032).mask,1)
        d.clock.completed_instruction()
        self.assertEqual(d.bus.read(0xFFFFD032,2),0)
        self.assertTrue(all(bits.value==0 for bits in d.bus.hcan.ack.values()))
