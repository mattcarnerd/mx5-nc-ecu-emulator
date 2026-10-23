import unittest

from ecu_workbench.core import ROMImage
from ecu_workbench.sh2 import SH2Subset


class ROMAndInstructionTests(unittest.TestCase):
    def test_file_metadata(self):
        image = ROMImage("unknown", b"example")
        info = image.inspect()
        self.assertEqual(image.size, 7)
        self.assertEqual(len(image.sha256), 64)
        self.assertFalse(info["firmware_emulated"])
        self.assertFalse(info["format_verified"])

    def test_sh2_subset(self):
        image = ROMImage("synthetic", bytes.fromhex("E005 7001 0009"))
        result = SH2Subset(image, 0x8000, 0x8000).run(3)
        self.assertEqual(result["registers"]["R0"], "0x00000006")

    def test_unknown_opcode_stops(self):
        result = SH2Subset(ROMImage("synthetic", b"\xff\xff"), 0).run()
        self.assertEqual(result["status"], "unsupported/unmapped")

    def test_delay_slot(self):
        image = ROMImage("synthetic", bytes.fromhex("A001 E001 E002 0009"))
        result = SH2Subset(image, 0).run(3)
        self.assertEqual(result["registers"]["R0"], "0x00000001")
