import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_rom import assess_nc_rom, STANDARD_USER_FLASH_SIZE

class NCROMAssessmentTests(unittest.TestCase):
    def test_typical_full_flash_is_not_verified(self):
        data = bytearray(STANDARD_USER_FLASH_SIZE)
        data[0:4] = b"SH2E"
        a = assess_nc_rom(ROMImage("test.bin", bytes(data)))
        self.assertEqual(a.status, "plausible_size_only")
        self.assertFalse(a.confirmed_nc_rom)
        self.assertFalse(a.firmware_emulation_supported)

    def test_random_nc_length_not_claimed_valid(self):
        a = assess_nc_rom(ROMImage("random.bin", bytes(range(256))*4096))
        self.assertEqual(a.status, "plausible_size_only")
        self.assertFalse(a.confirmed_nc_rom)

    def test_erased_image_rejected(self):
        for fill in (b"\x00", b"\xff"):
            a=assess_nc_rom(ROMImage("erased.bin", fill * STANDARD_USER_FLASH_SIZE))
            self.assertEqual(a.status, "empty_or_erased")

    def test_partial_or_unknown_length_not_declared_invalid(self):
        a = assess_nc_rom(ROMImage("partial.bin", b"\x01\x02\x03"))
        self.assertEqual(a.status, "unrecognised_layout")
        self.assertFalse(a.confirmed_nc_rom)

    def test_report_serialises(self):
        a = assess_nc_rom(ROMImage("test.bin", b"abc"))
        self.assertIsInstance(a.as_dict(),dict)

if __name__ == "__main__":
    unittest.main()
