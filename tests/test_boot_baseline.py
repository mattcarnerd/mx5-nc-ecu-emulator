import json
import os
from pathlib import Path
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import ROM_LIMIT
from ecu_workbench.boot_baseline import capture_boot_baseline


def fixture(instructions: bytes, *, manual_pc=0x180):
    data = bytearray(ROM_LIMIT)
    for i, v in enumerate((0x100, 0xFFFFBFA0, manual_pc, 0xFFFFBF00)):
        data[i * 4:i * 4 + 4] = v.to_bytes(4, "big")
    data[0x100:0x100 + len(instructions)] = instructions
    data[0x180:0x182] = bytes.fromhex("0009")
    return ROMImage("synthetic.bin", bytes(data))


class BaselineTests(unittest.TestCase):
    def test_unmodelled_peripheral_snapshot_and_determinism(self):
        rom = fixture(bytes.fromhex("D102 E205 2121 0009"))
        data = bytearray(rom.data)
        data[0x10C:0x110] = (0xFFFFEC30).to_bytes(4, "big")
        rom = ROMImage("synthetic.bin", bytes(data))
        a = capture_boot_baseline(rom, reset="power", nmi_high=True, max_steps=50)
        b = capture_boot_baseline(rom, reset="power", nmi_high=True, max_steps=50)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual(a["schema_version"], 1)
        self.assertEqual(a["rom"]["sha256"], rom.sha256)
        self.assertEqual(a["result"]["executed_instructions"], 3)
        self.assertEqual(a["result"]["pc_at_stop"], "0x00000106")
        self.assertEqual(a["result"]["stop"]["reason"], "unmodelled_peripheral")
        self.assertEqual(a["result"]["first_unsupported_peripheral"], {
            "address": "0xFFFFEC30", "access": "write", "width": 2,
            "value": "0x00000005", "instruction_pc": "0x00000104", "opcode": "2121",
        })
        self.assertFalse(a["result"]["boot_complete"])

    def test_last_sixteen_instructions_are_bounded(self):
        rom = fixture(bytes.fromhex("0009") * 30)
        report = capture_boot_baseline(rom, max_steps=25)
        self.assertEqual(report["result"]["executed_instructions"], 25)
        self.assertEqual(len(report["result"]["trace_tail"]), 16)
        self.assertEqual(report["result"]["trace_tail"][0]["pc"], "0x00000112")
        self.assertIsNone(report["result"]["first_unsupported_peripheral"])
        self.assertEqual(report["result"]["stop"]["reason"], "instruction_limit")

    def test_manual_reset_and_nmi_levels(self):
        rom = fixture(bytes.fromhex("0009"))
        for nmi, label in ((None, "unknown"), (True, "high"), (False, "low")):
            report = capture_boot_baseline(rom, reset="manual", nmi_high=nmi, max_steps=1)
            self.assertEqual(report["inputs"], {"reset": "manual", "nmi": label, "max_steps": 1})
            self.assertEqual(report["result"]["trace_tail"][0]["pc"], "0x00000180")
            self.assertEqual(report["result"]["initial_sp"], "0xFFFFBF00")

    def test_unrecognised_short_image_has_no_fake_trace(self):
        result = capture_boot_baseline(ROMImage("short", b"AB"), max_steps=10)
        self.assertEqual(result["result"]["executed_instructions"], 0)
        self.assertIsNone(result["result"]["pc_at_stop"])
        self.assertEqual(result["result"]["trace_tail"], [])
        self.assertIsNone(result["result"]["first_unsupported_peripheral"])
        self.assertEqual(result["result"]["stop"]["reason"], "unsupported_image_size")

    def test_bad_inputs_fail(self):
        rom = fixture(b"\x00\x09")
        for args in ({"reset": "no"}, {"max_steps": 0}, {"max_steps": 100001}, {"nmi_high": "high"}):
            with self.assertRaises(ValueError):
                capture_boot_baseline(rom, **args)

    def test_optional_locally_supplied_rom(self):
        source = os.environ.get("MX5_NC_TEST_ROM")
        if not source:
            self.skipTest("Set MX5_NC_TEST_ROM for private-ROM integration test")
        rom = ROMImage("locally-held.bin", Path(source).read_bytes())
        report = capture_boot_baseline(rom, nmi_high=True, max_steps=300)
        self.assertEqual(report["rom"]["sha256"], rom.sha256)
        self.assertFalse(report["result"]["boot_complete"])
        if rom.sha256 == "bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf":
            self.assertEqual(report["result"]["executed_instructions"], 67)
            self.assertEqual(report["result"]["pc_at_stop"], "0x00000C9E")
            self.assertEqual(report["result"]["first_unsupported_peripheral"]["address"], "0xFFFFF746")


if __name__ == "__main__":
    unittest.main()
