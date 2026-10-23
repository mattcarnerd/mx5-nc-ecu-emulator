"""SH7058 Rev 3.00, section 22.3, tables 22.3/22.4."""
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, ROM_LIMIT, PBDR_ADDRESS, PBIOR_ADDRESS, diagnose_nc_reset


def image():
    return ROMImage('synthetic.bin', bytes(ROM_LIMIT))


class PBDRTests(unittest.TestCase):
    def test_reset_and_no_implicit_pin_outputs(self):
        bus = BootBus(image())
        self.assertEqual(bus.pbdr, 0)
        self.assertEqual(bus.pbdr_known_mask, 0xFFFF)
        self.assertEqual(bus.read(PBIOR_ADDRESS, 2), 0)
        with self.assertRaises(BootStop) as error:
            bus.read(PBDR_ADDRESS, 2)
        self.assertEqual(error.exception.kind, 'missing_input')
        bus.write(PBDR_ADDRESS, 2, 0xA55A)
        self.assertEqual(bus.pbdr, 0xA55A)
        self.assertEqual(bus.peripheral_trace[-1]['scope'], 'output_latch_only')

    def test_word_read_write_and_byte_reads_in_output_mode(self):
        bus = BootBus(image())
        bus.write(PBIOR_ADDRESS, 2, 0xFFFF)
        self.assertEqual(bus.read(PBDR_ADDRESS, 2), 0)
        bus.write(PBDR_ADDRESS, 2, 0xBEEF)
        self.assertEqual(bus.read(PBDR_ADDRESS, 2), 0xBEEF)
        self.assertEqual(bus.read(PBDR_ADDRESS, 1), 0xBE)
        self.assertEqual(bus.read(PBDR_ADDRESS+1, 1), 0xEF)
        self.assertEqual(bus.peripheral_trace[-1]['width'], 1)

    def test_big_endian_byte_writes_preserve_other_bits(self):
        bus = BootBus(image())
        bus.write(PBIOR_ADDRESS, 2, 0xFFFF)
        bus.write(PBDR_ADDRESS, 2, 0x1234)
        bus.write(PBDR_ADDRESS, 1, 0xFE)
        self.assertEqual(bus.pbdr, 0xFE34)
        bus.write(PBDR_ADDRESS+1, 1, 0x56)
        self.assertEqual(bus.read(PBDR_ADDRESS, 2), 0xFE56)

    def test_mixed_output_and_input_read_does_not_invent_pins(self):
        bus = BootBus(image())
        bus.write(PBIOR_ADDRESS, 2, 0xFF00)
        bus.write(PBDR_ADDRESS, 2, 0x1357)
        self.assertEqual(bus.read(PBDR_ADDRESS, 1), 0x13)
        for address, width in ((PBDR_ADDRESS+1, 1), (PBDR_ADDRESS, 2)):
            with self.subTest(address=address, width=width):
                with self.assertRaises(BootStop) as error:
                    bus.read(address, width)
                self.assertEqual(error.exception.kind, 'missing_input')
        self.assertEqual(bus.pbdr, 0x1357)

    def test_manual_reset_unknown_until_each_byte_written(self):
        bus = BootBus(image(), power_on=False)
        self.assertEqual(bus.pbdr_known_mask, 0)
        bus.write(PBIOR_ADDRESS, 2, 0xFFFF)
        with self.assertRaises(BootStop) as error:
            bus.read(PBDR_ADDRESS, 2)
        self.assertEqual(error.exception.kind, 'unknown_peripheral_reset_state')
        bus.write(PBDR_ADDRESS, 1, 0xAA)
        self.assertEqual(bus.read(PBDR_ADDRESS, 1), 0xAA)
        with self.assertRaises(BootStop) as error:
            bus.read(PBDR_ADDRESS+1, 1)
        self.assertEqual(error.exception.kind, 'unknown_peripheral_reset_state')
        bus.write(PBDR_ADDRESS+1, 1, 0xBB)
        self.assertEqual(bus.read(PBDR_ADDRESS, 2), 0xAABB)

    def test_manual_reset_direction_unknown_even_with_known_latch(self):
        bus = BootBus(image(), power_on=False)
        bus.write(PBDR_ADDRESS, 2, 0xABCD)
        with self.assertRaises(BootStop) as error:
            bus.read(PBDR_ADDRESS, 2)
        self.assertEqual(error.exception.kind, 'unknown_peripheral_reset_state')

    def test_invalid_width_and_alignment(self):
        bus = BootBus(image())
        with self.assertRaises(BootStop) as error:
            bus.read(PBDR_ADDRESS, 4)
        self.assertEqual(error.exception.kind, 'unsupported_access_size')
        with self.assertRaises(BootStop) as error:
            bus.write(PBDR_ADDRESS, 4, 0x11223344)
        self.assertEqual(error.exception.kind, 'unsupported_access_size')
        with self.assertRaises(BootStop) as error:
            bus.read(PBDR_ADDRESS+1, 2)
        self.assertEqual(error.exception.kind, 'unaligned_access')

    def test_firmware_instructions_write_pbdr_without_boot_claim(self):
        data = bytearray(ROM_LIMIT)
        for i, v in enumerate((0x100, 0xFFFFBFA0, 0x100, 0xFFFFBFA0)):
            data[4*i:4*i+4] = v.to_bytes(4, 'big')
        data[0x100:0x108] = bytes.fromhex('D102 E255 2121 0009')
        data[0x10C:0x110] = PBDR_ADDRESS.to_bytes(4, 'big')
        result = diagnose_nc_reset(ROMImage('synthetic.bin', bytes(data)), max_steps=4)
        self.assertEqual(result['executed_instructions'], 4)
        self.assertEqual(result['stop']['reason'], 'instruction_limit')
        writes = [p for p in result['modelled_peripheral_accesses'] if p['register']=='PBDR']
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]['value'], 0x55)
        self.assertFalse(result['boot_complete'])
