"""B38: documented PLDR semantics and observed MOV.W R3,@R0 (2031)."""
import hashlib
import os
from pathlib import Path
import unittest

from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, ROM_LIMIT, diagnose_nc_reset
from ecu_workbench.port_l import PLDR_ADDRESS, PLIOR_ADDRESS
from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.trace_review import LF9VEB_SHA256


def image(code=b"\x00\x09"):
    data = bytearray(ROM_LIMIT)
    for i, value in enumerate((0x100, 0xFFFFBFA0, 0x100, 0xFFFFBFA0)):
        data[4*i:4*i+4] = value.to_bytes(4, "big")
    data[0x100:0x100+len(code)] = code
    return ROMImage("synthetic", bytes(data))


class PortLTests(unittest.TestCase):
    def test_power_reset_latch_is_zero_but_pins_unknown(self):
        b = BootBus(image())
        self.assertEqual(b.port_l.known_mask, 0x3FFF)
        with self.assertRaises(BootStop) as cm:
            b.read(PLDR_ADDRESS, 2)
        self.assertEqual(cm.exception.kind, "missing_input")
        b.write(PLIOR_ADDRESS, 2, 0x3FFF)
        self.assertEqual(b.read(PLDR_ADDRESS, 2), 0)
        b.write(PLDR_ADDRESS, 2, 0x3FFF)
        self.assertEqual(b.read(PLDR_ADDRESS, 2), 0x3FFF)
        self.assertEqual(b.port_l.pin_known_mask, 0)

    def test_big_endian_bytes_and_reserved_read_zero(self):
        b = BootBus(image())
        b.write(PLIOR_ADDRESS, 2, 0xFFFF)  # reserved direction bits cannot create data bits
        b.write(PLDR_ADDRESS, 1, 0x12)
        b.write(PLDR_ADDRESS + 1, 1, 0xA5)
        self.assertEqual(b.read(PLDR_ADDRESS, 2), 0x12A5)
        self.assertEqual(b.read(PLDR_ADDRESS, 1), 0x12)
        self.assertEqual(b.read(PLDR_ADDRESS + 1, 1), 0xA5)

    def test_invalid_reserved_writes_are_atomic_and_untraced(self):
        b = BootBus(image(), power_on=False)
        for address, width, value in ((PLDR_ADDRESS, 2, 0x4000),
                                       (PLDR_ADDRESS, 2, 0x8000),
                                       (PLDR_ADDRESS, 2, 0xFFFF),
                                       (PLDR_ADDRESS, 1, 0x40)):
            with self.subTest(value=value), self.assertRaises(BootStop) as cm:
                b.write(address, width, value)
            self.assertEqual(cm.exception.kind, "invalid_peripheral_write")
            self.assertEqual(b.port_l.data, 0)
            self.assertEqual(b.port_l.known_mask, 0)
            self.assertEqual(b.peripheral_trace, [])

    def test_pin_readback_mixed_direction_and_alternate_modes(self):
        b = BootBus(image(), port_l_pin_values=0x25A5)
        b.write(PLDR_ADDRESS, 2, 0x3FFF)
        self.assertEqual(b.read(PLDR_ADDRESS, 2), 0x25A5)
        b.write(PLIOR_ADDRESS, 2, 0x00FF)
        self.assertEqual(b.read(PLDR_ADDRESS, 2), 0x25FF)
        # Table 22.22: alternate functions do not alter direction-selected readback.
        b.write(0xFFFFF758, 2, 0x0ABC)
        b.write(0xFFFFF75A, 2, 0x5555)
        self.assertEqual(b.read(PLDR_ADDRESS, 2), 0x25FF)
        self.assertEqual(b.port_l.pin_values, 0x25A5)

    def test_partial_known_pins(self):
        b = BootBus(image(), port_l_pin_values=0xA5, port_l_pin_known_mask=0xFF)
        self.assertEqual(b.read(PLDR_ADDRESS + 1, 1), 0xA5)
        with self.assertRaises(BootStop) as cm:
            b.read(PLDR_ADDRESS, 2)
        self.assertEqual(cm.exception.kind, "missing_input")
        b.write(PLIOR_ADDRESS, 2, 0x3F00)
        self.assertEqual(b.read(PLDR_ADDRESS, 2), 0xA5)

    def test_manual_reset_partial_latch_remains_unknown(self):
        b = BootBus(image(), power_on=False)
        b.write(PLDR_ADDRESS, 1, 0x3F)
        with self.assertRaises(BootStop) as cm:
            b.read(PLDR_ADDRESS, 1)
        self.assertEqual(cm.exception.kind, "unknown_peripheral_reset_state")
        b.write(PLIOR_ADDRESS, 2, 0x3FFF)
        self.assertEqual(b.read(PLDR_ADDRESS, 1), 0x3F)
        with self.assertRaises(BootStop) as cm:
            b.read(PLDR_ADDRESS, 2)
        self.assertEqual(cm.exception.kind, "unknown_peripheral_reset_state")
        b.write(PLDR_ADDRESS + 1, 1, 0xA5)
        self.assertEqual(b.read(PLDR_ADDRESS, 2), 0x3FA5)

    def test_width_alignment_validation_and_adjacent_addresses(self):
        b = BootBus(image())
        for action in (lambda: b.read(PLDR_ADDRESS, 4),
                       lambda: b.write(PLDR_ADDRESS, 4, 0),
                       lambda: b.read(PLDR_ADDRESS + 1, 2),
                       lambda: b.write(PLDR_ADDRESS + 1, 2, 0)):
            with self.assertRaises(BootStop) as cm:
                action()
            self.assertIn(cm.exception.kind, ("unsupported_access_size", "unaligned_access"))
        for value, mask in ((-1, 0x3FFF), (0x4000, 0x3FFF), (True, 0x3FFF),
                            (0, 0x4000), (0, True)):
            with self.subTest(value=value, mask=mask), self.assertRaises(ValueError):
                b.port_l.set_pins(value, mask)
        with self.assertRaises(BootStop) as cm:
            b.read(0xFFFFF788, 2)  # PLPR remains outside this bounded issue
        self.assertEqual(cm.exception.kind, "unmodelled_peripheral")

    def test_observed_opcode_2031_and_shareable_trace_evidence(self):
        # Synthetic loads of address/value, then the observed MOV.W R3,@R0.
        data = bytearray(image(bytes.fromhex("D003 9304 2031 0009")).data)
        data[0x110:0x114] = PLDR_ADDRESS.to_bytes(4, "big")
        data[0x10E:0x110] = bytes.fromhex("3FFF")
        d = NCBootDiagnostic(ROMImage("synthetic", bytes(data)))
        result = d.run(4)
        self.assertEqual(d.bus.port_l.data, 0x3FFF)
        self.assertEqual(result["stop"]["reason"], "instruction_limit")
        self.assertFalse(result["boot_complete"])
        detail = {"image": {"sha256": result["rom_sha256"]}, "nc_boot": result,
                  "diagnostic_settings": {"reset": "power", "nmi": "high", "max_steps": 4,
                                          "explicit_pin_values": False}}
        flag = "pldr_word_write_3fff_in_peripheral_trace"
        self.assertTrue(make_shareable_blocker_report(detail)[flag])
        accesses = result["modelled_peripheral_accesses"]
        for wrong in ({"register": "PLDR", "access": "read", "width": 2, "value": 0x3FFF},
                      {"register": "PLDR", "access": "write", "width": 1, "value": 0x3FFF},
                      {"register": "PLDR", "access": "write", "width": 2, "value": 0xFFFF}):
            result["modelled_peripheral_accesses"] = [wrong]
            self.assertFalse(make_shareable_blocker_report(detail)[flag])
        result["modelled_peripheral_accesses"] = []
        self.assertFalse(make_shareable_blocker_report(detail)[flag])
        result["modelled_peripheral_accesses"] = accesses

    def test_optional_original_lf9veb_passes_observed_pldr_write(self):
        path = os.environ.get("MX5_NC_TEST_ROM")
        if not path:
            self.skipTest("Set MX5_NC_TEST_ROM to the privately held original LF9VEB ROM")
        data = Path(path).read_bytes()
        if hashlib.sha256(data).hexdigest() != LF9VEB_SHA256:
            self.skipTest("Supplied ROM is not the original LF9VEB SHA-256 reference")
        result = diagnose_nc_reset(ROMImage("private_reference", data), max_steps=300, nmi_high=True)
        self.assertTrue(any(a.get("register") == "PLDR" and a.get("access") == "write"
                            and a.get("width") == 2 and a.get("value") == 0x3FFF
                            for a in result["modelled_peripheral_accesses"]))
        self.assertGreater(result["executed_instructions"], 129)
        self.assertFalse(result["boot_complete"])
