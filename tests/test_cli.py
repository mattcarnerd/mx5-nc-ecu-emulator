"""CLI only exposes NC startup diagnostics: comparison is deliberately removed."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from ecu_workbench.cli import main

class BootCLITests(unittest.TestCase):
    def test_default_is_boot_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"fixture.bin"
            data = bytearray(0x100000)
            for index, value in enumerate((0x100, 0xFFFFBFA0, 0x100, 0xFFFFBFA0)):
                data[index*4:index*4+4] = value.to_bytes(4, "big")
            data[0x100:0x102] = bytes.fromhex("0009")
            path.write_bytes(data)
            out = StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(["--rom", str(path), "--steps", "1"]), 0)
            report = json.loads(out.getvalue())
            self.assertEqual(report["nc_boot"]["executed_instructions"], 1)
            self.assertFalse(report["nc_boot"]["boot_complete"])
            self.assertNotIn("comparison", report)

    def test_compare_option_no_longer_accepted(self):
        with self.assertRaises(SystemExit) as raised:
            main(["--rom", "test.bin", "--compare", "other.bin"])
        self.assertEqual(raised.exception.code, 2)
