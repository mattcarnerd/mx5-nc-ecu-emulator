"""B33: SH7058 PFDR register simulation and real SH-2 word-store opcode tests."""
import unittest

from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, ROM_LIMIT
from ecu_workbench.port_f import PortF, PFDR_ADDRESS, PFIOR_ADDRESS


def image(code=b"\x00\x09"):
    data = bytearray(ROM_LIMIT)
    for i, v in enumerate((0x100, 0xFFFFBFA0, 0x100, 0xFFFFBFA0)):
        data[i * 4:i * 4 + 4] = v.to_bytes(4, "big")
    data[0x100:0x100 + len(code)] = code
    return ROMImage("synthetic", bytes(data))


class PortFTests(unittest.TestCase):
    def test_word_write_does_not_invent_pin_levels(self):
        bus = BootBus(image())
        self.assertEqual(bus.port_f.data, 0)
        self.assertEqual(bus.port_f.known_mask, 0xFFFF)
        bus.write(PFDR_ADDRESS, 2, 0xFFFF)
        self.assertEqual(bus.port_f.data, 0xFFFF)
        self.assertEqual(bus.peripheral_trace[-1]["register"], "PFDR")
        self.assertEqual(bus.peripheral_trace[-1]["scope"], "output_latch_only")
        self.assertEqual(bus.port_f.pin_known_mask, 0)
        with self.assertRaises(BootStop) as cm:
            bus.read(PFDR_ADDRESS, 2)
        self.assertEqual(cm.exception.kind, "missing_input")
        bus.write(PFIOR_ADDRESS, 2, 0xFFFF)
        self.assertEqual(bus.read(PFDR_ADDRESS, 2), 0xFFFF)

    def test_big_endian_bytes(self):
        bus = BootBus(image())
        bus.write(PFIOR_ADDRESS, 2, 0xFFFF)
        bus.write(PFDR_ADDRESS, 1, 0x12)
        bus.write(PFDR_ADDRESS + 1, 1, 0x34)
        self.assertEqual(bus.read(PFDR_ADDRESS, 2), 0x1234)
        self.assertEqual(bus.read(PFDR_ADDRESS, 1), 0x12)
        self.assertEqual(bus.read(PFDR_ADDRESS + 1, 1), 0x34)

    def test_external_input_and_mixed_directions(self):
        bus = BootBus(image(), port_f_pin_values=0xA5A5, port_f_pin_known_mask=0xFFFF)
        bus.write(PFDR_ADDRESS, 2, 0xFFFF)
        self.assertEqual(bus.read(PFDR_ADDRESS, 2), 0xA5A5)
        bus.write(PFIOR_ADDRESS, 2, 0x00FF)
        self.assertEqual(bus.read(PFDR_ADDRESS, 2), 0xA5FF)
        self.assertEqual(bus.peripheral_trace[-1]["physical_input_mask"], "0xFF00")

    def test_partial_known_pin_mask(self):
        bus = BootBus(image(), port_f_pin_values=0x00AB, port_f_pin_known_mask=0x00FF)
        self.assertEqual(bus.read(PFDR_ADDRESS + 1, 1), 0xAB)
        with self.assertRaises(BootStop) as cm:
            bus.read(PFDR_ADDRESS, 2)
        self.assertEqual(cm.exception.kind, "missing_input")
        bus.write(PFIOR_ADDRESS, 2, 0xFF00)
        self.assertEqual(bus.read(PFDR_ADDRESS, 2), 0x00AB)

    def test_manual_reset_preserves_unknown_direction_and_latch(self):
        bus = BootBus(image(), power_on=False)
        bus.write(PFDR_ADDRESS, 1, 0x12)
        with self.assertRaises(BootStop) as cm:
            bus.read(PFDR_ADDRESS, 1)
        self.assertEqual(cm.exception.kind, "unknown_peripheral_reset_state")
        bus.write(PFIOR_ADDRESS, 2, 0xFFFF)
        self.assertEqual(bus.read(PFDR_ADDRESS, 1), 0x12)
        with self.assertRaises(BootStop) as cm:
            bus.read(PFDR_ADDRESS, 2)
        self.assertEqual(cm.exception.kind, "unknown_peripheral_reset_state")

    def test_width_alignment_and_bad_explicit_pins(self):
        bus = BootBus(image())
        for f in (lambda: bus.read(PFDR_ADDRESS, 4),
                  lambda: bus.write(PFDR_ADDRESS, 4, 0)):
            with self.assertRaises(BootStop) as cm:
                f()
            self.assertEqual(cm.exception.kind, "unsupported_access_size")
        with self.assertRaises(BootStop) as cm:
            bus.read(PFDR_ADDRESS + 1, 2)
        self.assertEqual(cm.exception.kind, "unaligned_access")
        for value, mask in ((-1, 0xFFFF), (0x10000, 0xFFFF), (True, 0xFFFF),
                            (0, 0x10000), (0, True)):
            with self.subTest(value=value, mask=mask), self.assertRaises(ValueError):
                bus.port_f.set_pins(value, mask)

    def test_observed_sh2_opcode_2351_stores_ffff(self):
        # MOV.L @(disp,PC),R3; MOV #-1,R5; MOV.W R5,@R3 (0x2351)
        data = bytearray(image(bytes.fromhex("D302 E5FF 2351 0009")).data)
        data[0x10C:0x110] = PFDR_ADDRESS.to_bytes(4, "big")
        diag = NCBootDiagnostic(ROMImage("synthetic", bytes(data)))
        result = diag.run(4)
        self.assertEqual(diag.bus.port_f.data, 0xFFFF)
        self.assertTrue(any(a.get("register") == "PFDR" and
                            a.get("value") == 0xFFFF and a.get("width") == 2
                            for a in result["modelled_peripheral_accesses"]))
        self.assertEqual(result["stop"]["reason"], "instruction_limit")
        self.assertFalse(result["boot_complete"])
