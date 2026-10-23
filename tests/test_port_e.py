"""B30: Port E PEDR fail-closed regression tests."""
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, ROM_LIMIT
from ecu_workbench.port_e import PEDR_ADDRESS, PEIOR_ADDRESS

def image(code=b'\x00\x09'):
    data=bytearray(ROM_LIMIT)
    for idx,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        data[4*idx:4*idx+4]=v.to_bytes(4,'big')
    data[0x100:0x100+len(code)]=code
    return ROMImage('synthetic',bytes(data))

class PortETests(unittest.TestCase):
    def test_latch_and_explicit_input(self):
        b=BootBus(image())
        b.write(PEDR_ADDRESS,2,0xFFFF)
        self.assertEqual(b.port_e.data,0xFFFF)
        self.assertEqual(b.peripheral_trace[-1]['scope'],'output_latch_only')
        with self.assertRaises(BootStop) as cm: b.read(PEDR_ADDRESS,2)
        self.assertEqual(cm.exception.kind,'missing_input')
        b.write(PEIOR_ADDRESS,2,0xFFFF)
        self.assertEqual(b.read(PEDR_ADDRESS,2),0xFFFF)

    def test_big_endian_byte_writes(self):
        b=BootBus(image())
        b.write(PEIOR_ADDRESS,2,0xFFFF)
        b.write(PEDR_ADDRESS,1,0x12)
        b.write(PEDR_ADDRESS+1,1,0x34)
        self.assertEqual(b.read(PEDR_ADDRESS,2),0x1234)
        self.assertEqual(b.read(PEDR_ADDRESS,1),0x12)
        self.assertEqual(b.read(PEDR_ADDRESS+1,1),0x34)

    def test_input_mode_uses_pins_not_latch(self):
        b=BootBus(image(),port_e_pin_values=0xA5A5,port_e_pin_known_mask=0xFFFF)
        b.write(PEDR_ADDRESS,2,0xFFFF)
        self.assertEqual(b.read(PEDR_ADDRESS,2),0xA5A5)
        b.write(PEIOR_ADDRESS,2,0x00FF)
        self.assertEqual(b.read(PEDR_ADDRESS,2),0xA5FF)

    def test_manual_reset_and_unknown_mask(self):
        b=BootBus(image(),power_on=False)
        b.write(PEDR_ADDRESS,1,0xAB)
        with self.assertRaises(BootStop) as cm: b.read(PEDR_ADDRESS,2)
        self.assertEqual(cm.exception.kind,'unknown_peripheral_reset_state')
        b.write(PEIOR_ADDRESS,2,0xFFFF)
        self.assertEqual(b.read(PEDR_ADDRESS,1),0xAB)
        with self.assertRaises(BootStop) as cm: b.read(PEDR_ADDRESS,2)
        self.assertEqual(cm.exception.kind,'unknown_peripheral_reset_state')

    def test_widths_validation_and_partial_levels(self):
        b=BootBus(image(),port_e_pin_values=0xABCD,port_e_pin_known_mask=0x00FF)
        self.assertEqual(b.read(PEDR_ADDRESS+1,1),0xCD)
        with self.assertRaises(BootStop) as cm: b.read(PEDR_ADDRESS,2)
        self.assertEqual(cm.exception.kind,'missing_input')
        for fn in (lambda: b.read(PEDR_ADDRESS,4),lambda: b.write(PEDR_ADDRESS,4,0)):
            with self.assertRaises(BootStop) as cm: fn()
            self.assertEqual(cm.exception.kind,'unsupported_access_size')
        with self.assertRaises(BootStop) as cm: b.read(PEDR_ADDRESS+1,2)
        self.assertEqual(cm.exception.kind,'unaligned_access')
        for v,m in ((-1,0xFFFF),(65536,0xFFFF),(True,0xFFFF),(0,65536)):
            with self.assertRaises(ValueError): b.port_e.set_pins(v,m)

    def test_genuine_store_instruction(self):
        data=bytearray(image(bytes.fromhex('D102 E0FF 2101 0009')).data)
        data[0x10C:0x110]=PEDR_ADDRESS.to_bytes(4,'big')
        d=NCBootDiagnostic(ROMImage('synthetic',bytes(data)))
        result=d.run(4)
        self.assertEqual(d.bus.port_e.data,0x00FF)
        self.assertEqual(result['stop']['reason'],'instruction_limit')
        self.assertFalse(result['boot_complete'])
