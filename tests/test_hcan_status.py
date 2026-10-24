import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootBus,BootStop
from ecu_workbench.hcan import GSR_ADDRESSES,MCR_ADDRESSES
from ecu_workbench.known_bits import KnownBits

class HcanStatusTests(unittest.TestCase):
    def test_power_reset_documented_flags_reserved_readback_unknown(self):
        b=program(0x0009).bus
        for address in GSR_ADDRESSES:
            bits=b.read_cpu_word(address)
            self.assertEqual(bits,KnownBits(0xC,0x3F))
            self.assertTrue(bits.bit_and(KnownBits.exact(8)).is_zero() is False)
            self.assertFalse(bool(bits.mask&0xFFC0))
            with self.assertRaises(BootStop):b.read(address,2)

    def test_manual_and_commands_never_invent_status_or_completion(self):
        for power in (False,True):
            b=BootBus(program(0x0009).bus.image,power_on=power)
            if not power:self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
            other=b.read_cpu_word(GSR_ADDRESSES[1])
            for value in (1,0,1):
                b.write(MCR_ADDRESSES[0],2,value)
                for _ in range(4):self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[0]).mask,0)
                self.assertEqual(b.read_cpu_word(GSR_ADDRESSES[1]),other)
            d=program(0x6031,0xC808,0x8900);d.r[3]=GSR_ADDRESSES[0]
            d.bus.write(MCR_ADDRESSES[0],2,1)
            r=d.run(3);self.assertIsNone(d.t)
            self.assertEqual(r['stop']['reason'],'unknown_status')
            self.assertEqual(d.clock.ticks,2)

    def test_gsr_width_write_atomicity_and_unknown_reserved_use(self):
        b=program(0x0009).bus;original=list(b.hcan.gsr)
        for address in GSR_ADDRESSES:
            for width in (1,4):
                with self.assertRaises(BootStop):b.read(address,width)
            with self.assertRaises(BootStop):b.read(address+1,1)
            for value in (0,0xFFFF):
                with self.assertRaises(BootStop) as caught:b.write(address,2,value)
                self.assertEqual(caught.exception.kind,'read_only_peripheral')
            self.assertEqual(b.hcan.gsr,original)
        d=program(0x6031,0x7001);d.r[3]=GSR_ADDRESSES[0]
        r=d.run(2);self.assertEqual(r['stop']['reason'],'unknown_register')
        self.assertEqual(d.transport_bits(0).mask,0x3F)
