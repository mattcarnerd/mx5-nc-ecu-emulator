"""B04: stop classification, precise PC/opcode and preceding instruction context."""
from __future__ import annotations
import json
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import ROM_LIMIT, diagnose_nc_reset
from ecu_workbench.boot_baseline import capture_boot_baseline


def sample(code: bytes, *, pc: int = 0x100, at: int | None = None, value: int | None = None) -> ROMImage:
    raw = bytearray(ROM_LIMIT)
    for index, v in enumerate((pc, 0xFFFFBFA0, pc, 0xFFFFBFA0)):
        raw[index*4:index*4+4] = v.to_bytes(4,"big")
    raw[pc:pc+len(code)] = code
    if at is not None:
        raw[at:at+4] = value.to_bytes(4,"big")
    return ROMImage("synthetic.bin",bytes(raw))


class BootBlockerTests(unittest.TestCase):
    def test_unsupported_opcode_reports_failing_instruction_not_next_pc(self):
        result=diagnose_nc_reset(sample(bytes.fromhex("0009 FFFF")),max_steps=20)
        issue=result["next_dependency"]
        self.assertEqual(issue["category"],"unsupported_cpu_instruction")
        self.assertEqual(issue["instruction_pc"],"0x00000102")
        self.assertEqual(issue["opcode"],"FFFF")
        self.assertEqual(issue["memory_access"],{"access":"fetch","address":"0x00000102","width":2})
        self.assertEqual(result["pc_at_stop"],"0x00000104")
        self.assertEqual([x["pc"] for x in issue["prior_instructions"]],["0x00000100"])

    def test_unmodelled_peripheral_write_reports_sixteen_prior_instructions(self):
        code=bytes.fromhex("0009")*18 + bytes.fromhex("D102 E205 2121")
        rom=sample(code,at=0x130,value=0xFFFFEC30)
        result=diagnose_nc_reset(rom,max_steps=70)
        issue=result["next_dependency"]
        self.assertEqual(issue["category"],"unmodelled_hardware_register")
        self.assertEqual(issue["instruction_pc"],"0x00000128")
        self.assertEqual(issue["opcode"],"2121")
        self.assertEqual(issue["memory_access"],{"access":"write","address":"0xFFFFEC30","width":2,"value":"0x00000005"})
        self.assertEqual(len(issue["prior_instructions"]),16)
        self.assertEqual(issue["prior_instructions"][0]["pc"],"0x00000108")
        self.assertEqual(issue["prior_instructions"][-1]["pc"],"0x00000126")
        self.assertEqual(json.dumps(issue,sort_keys=True),json.dumps(diagnose_nc_reset(rom,max_steps=70)["next_dependency"],sort_keys=True))
        self.assertEqual(capture_boot_baseline(rom,max_steps=70)["result"]["next_dependency"],issue)

    def test_missing_external_input_and_uninitialised_ram_are_distinct(self):
        code=bytes.fromhex("D102 6011 0009")
        cases=((0xFFFFF738,"missing_input","missing_external_input"),
               (0xFFFF0004,"uninitialised_ram","uninitialised_memory"))
        for address, reason, category in cases:
            with self.subTest(address=address):
                issue=diagnose_nc_reset(sample(code,at=0x10C,value=address),max_steps=10)["next_dependency"]
                self.assertEqual(issue["reason"],reason)
                self.assertEqual(issue["category"],category)
                self.assertEqual(issue["instruction_pc"],"0x00000102")
                self.assertEqual(issue["opcode"],"6011")
                self.assertEqual(issue["memory_access"],{"access":"read","address":f"0x{address:08X}","width":2})
                self.assertEqual(len(issue["prior_instructions"]),1)

    def test_instruction_limit_is_not_hardware_blocker(self):
        report=diagnose_nc_reset(sample(bytes.fromhex("0009")*5),max_steps=3)
        issue=report["next_dependency"]
        self.assertEqual(issue["category"],"instruction_limit_reached")
        self.assertFalse(issue["is_dependency_blocker"])
        self.assertIsNone(issue["instruction_pc"])
        self.assertIsNone(issue["opcode"])
        self.assertIsNone(issue["memory_access"])
        self.assertEqual(len(issue["prior_instructions"]),3)
        self.assertFalse(report["boot_complete"])

    def test_invalid_image_is_diagnostic_not_fake_opcode(self):
        issue=diagnose_nc_reset(ROMImage("bad",b"AB"),max_steps=20)["next_dependency"]
        self.assertEqual(issue["category"],"unsupported_rom_image")
        self.assertEqual(issue["prior_instructions"],[])
        self.assertIsNone(issue["instruction_pc"])
        self.assertIsNone(issue["opcode"])

    def test_failed_instruction_fetch_reports_requested_pc_with_no_opcode(self):
        # MOV.L literal -> R1; JMP @R1; NOP delay slot; fetch unmapped 1MiB.
        rom=sample(bytes.fromhex("D101 412B 0009"),at=0x108,value=0x00100000)
        issue=diagnose_nc_reset(rom,max_steps=20)["next_dependency"]
        self.assertEqual(issue["category"],"invalid_memory_access")
        self.assertEqual(issue["instruction_pc"],"0x00100000")
        self.assertIsNone(issue["opcode"])
        self.assertEqual(issue["memory_access"],{"access":"read","address":"0x00100000","width":2})
        self.assertEqual(len(issue["prior_instructions"]),3)
