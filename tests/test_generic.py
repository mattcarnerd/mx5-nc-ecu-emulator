import unittest
from ecu_workbench.core import ROMImage, compare
from ecu_workbench.sh2 import SH2Subset

class GenericROMTests(unittest.TestCase):
    def test_any_size_rom(self):
        r=ROMImage("unknown",b"any firmware bytes")
        self.assertEqual(r.inspect()["program_architecture"],"unknown")
        self.assertEqual(r.size,18)
        self.assertEqual(len(r.sha256),64)
    def test_hexdump(self):
        self.assertIn("00000000",ROMImage("s",b"abc").hexdump())
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):ROMImage("s",b"abc").hexdump(-1)
    def test_compare_different_sizes(self):
        d=compare(ROMImage("a",b"\x00\x01\x02"),ROMImage("b",b"\x00\x04\x02\x06"))
        self.assertEqual(d["changed_bytes"],2)
        self.assertEqual(d["changed_regions"],2)
    def test_same(self):
        r=ROMImage("a",b"ABC")
        self.assertEqual(compare(r,r)["changed_bytes"],0)
    def test_sh2_subset(self):
        r=ROMImage("test",bytes.fromhex("E005 7001 0009"))
        result=SH2Subset(r,0x8000,0x8000).run(3)
        self.assertEqual(result["registers"]["R0"],"0x00000006")
    def test_unknown_opcode_stops(self):
        result=SH2Subset(ROMImage("test",b"\xff\xff"),0).run()
        self.assertEqual(result["status"],"unsupported/unmapped")
    def test_delay_slot(self):
        code=ROMImage("test",bytes.fromhex("A001 E001 E002 0009"))
        result=SH2Subset(code,0).run(3)
        self.assertEqual(result["registers"]["R0"],"0x00000001")

if __name__=="__main__":unittest.main()
