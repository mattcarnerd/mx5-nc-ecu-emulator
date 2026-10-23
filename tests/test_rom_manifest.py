"""B26 manifest regression tests: no OEM ROMs required."""
import json
import tempfile
import unittest
from pathlib import Path
from ecu_workbench.rom_manifest import inventory

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        (self.base/"test.bin").write_bytes(b"synthetic-not-a-rom")
    def run_inventory(self, entries):
        return inventory({"entries":entries},base=self.base)["entries"]
    def test_missing_file_unknown_hardware(self):
        out=self.run_inventory([{"path":"missing.bin","family":"NC1","hardware_profile":"unknown"}])[0]
        self.assertEqual(out["status"],"not_available")
        self.assertIsNone(out["sha256"])
    def test_candidate_hash_and_no_path_leak(self):
        out=self.run_inventory([{"path":"test.bin","family":"NC3","calibration_id":"LF-TEST"}])
        self.assertEqual(out[0]["status"],"candidate")
        self.assertEqual(len(out[0]["sha256"]),64)
        self.assertIsNone(out[0]["calibration_id"])
        self.assertNotIn("test.bin",json.dumps(out))
        self.assertNotIn(str(self.base),json.dumps(out))
        self.assertEqual(out[0]["hardware_profile"],"unknown")
    def test_verified_requires_evidence(self):
        entry={"path":"test.bin","hardware_profile":"SH7058"}
        self.assertEqual(self.run_inventory([entry])[0]["status"],"candidate")
        entry["hardware_evidence"]="board inspection log"
        self.assertEqual(self.run_inventory([entry])[0]["status"],"verified_profile")
        entry["boot_trace_tested"]=True
        out=self.run_inventory([entry])[0]
        self.assertEqual(out["status"],"boot_trace_tested")
        self.assertFalse(out["boot_complete"])
    def test_duplicate_hash_rejected(self):
        (self.base/"copy.bin").write_bytes((self.base/"test.bin").read_bytes())
        with self.assertRaisesRegex(ValueError,"duplicate ROM"):
            self.run_inventory([{"path":"test.bin"},{"path":"copy.bin"}])
    def test_validation_rejects_false_claims(self):
        invalid=[
            {"path":"test.bin","family":"ND"},
            {"path":"test.bin","boot_trace_tested":True},
            {"path":"missing","hardware_profile":"SH7058",
             "hardware_evidence":"board inspection","boot_trace_tested":True},
            {"path":"test.bin","boot_trace_tested":"true"},
            {"path":"test.bin","hardware_profile":""},
            {"path":123},
        ]
        for entry in invalid:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                self.run_inventory([entry])
    def test_provenance_required_for_calibration_claim(self):
        one=self.run_inventory([{"path":"test.bin","calibration_id":"ID"}])[0]
        self.assertIsNone(one["calibration_id"])
        two=self.run_inventory([{"path":"test.bin","calibration_id":"ID",
                                "provenance":"ECU label photographed"}])[0]
        self.assertEqual(two["calibration_id"],"ID")
