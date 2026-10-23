"""B05: power/manual reset, all NMI levels and headless GUI status checks."""
from __future__ import annotations

import json
import os
from pathlib import Path
import unittest

from ecu_workbench.core import ROMImage
from ecu_workbench.boot_baseline import capture_boot_baseline
from ecu_workbench.boot_presenter import present_reset_diagnostic
from ecu_workbench.nc_boot import ROM_LIMIT, BootBus, BootStop, diagnose_nc_reset

LF9VEB_SHA256 = "bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf"


def reset_rom(read_icr=True) -> ROMImage:
    """Synthetic ROM with independent reset PCs/stacks and ICR read instruction."""
    data = bytearray(ROM_LIMIT)
    for i, value in enumerate((0x100, 0xFFFFBFA0, 0x180, 0xFFFFBF00)):
        data[4*i:4*i+4] = value.to_bytes(4, "big")
    code = bytes.fromhex("D102 6011 0009") if read_icr else bytes.fromhex("E005 7001 0009")
    for addr in (0x100, 0x180):
        data[addr:addr+len(code)] = code
        if read_icr:
            data[addr+12:addr+16] = (0xFFFFED18).to_bytes(4, "big")
    return ROMImage("synthetic.bin", bytes(data))


class ResetNMIMatrixTests(unittest.TestCase):
    def test_power_and_manual_by_all_nmi_states_are_deterministic(self):
        rom = reset_rom()
        for reset in ("power", "manual"):
            for nmi in (None, True, False):
                with self.subTest(reset=reset, nmi=nmi):
                    first = capture_boot_baseline(rom, reset=reset, nmi_high=nmi, max_steps=3)
                    second = capture_boot_baseline(rom, reset=reset, nmi_high=nmi, max_steps=3)
                    self.assertEqual(json.dumps(first,sort_keys=True), json.dumps(second,sort_keys=True))
                    self.assertEqual(first["inputs"]["nmi"],
                                     "unknown" if nmi is None else ("high" if nmi else "low"))
                    result = first["result"]
                    self.assertFalse(result["boot_complete"])
                    self.assertEqual(result["reset_vectors"][f"{reset}_pc"],
                                     "0x00000100" if reset == "power" else "0x00000180")
                    self.assertEqual(result["initial_sp"],
                                     "0xFFFFBFA0" if reset == "power" else "0xFFFFBF00")
                    if reset == "manual":
                        self.assertEqual(result["stop"]["reason"], "unknown_peripheral_reset_state")
                        self.assertEqual(result["next_dependency"]["category"], "unknown_hardware_state")
                    elif nmi is None:
                        self.assertEqual(result["stop"]["reason"], "missing_input")
                        self.assertEqual(result["next_dependency"]["category"], "missing_external_input")
                    else:
                        self.assertEqual(result["stop"]["reason"], "instruction_limit")
                        self.assertFalse(result["next_dependency"]["is_dependency_blocker"])
                    attempted = 3 if result["stop"]["reason"] == "instruction_limit" else 2
                    self.assertEqual(result["executed_instructions"], attempted)
                    self.assertEqual(result["trace_tail"][0]["pc"],
                                     "0x00000100" if reset == "power" else "0x00000180")

    def test_known_manual_nmi_does_not_imply_known_control_state(self):
        for nmi in (None, False, True):
            bus = BootBus(reset_rom(), power_on=False, nmi_high=nmi)
            with self.subTest(nmi=nmi), self.assertRaises(BootStop) as caught:
                bus.read(0xFFFFED18, 2)
            self.assertEqual(caught.exception.kind, "unknown_peripheral_reset_state")
            self.assertIsNone(bus.icr_control)
            self.assertIsNone(bus.bsc[0xFFFFEC20])
            self.assertIsNone(bus.pfc[0xFFFFF730])
        powered = BootBus(reset_rom(), power_on=True, nmi_high=None)
        with self.assertRaises(BootStop) as caught:
            powered.read(0xFFFFED18, 2)
        self.assertEqual(caught.exception.kind, "missing_input")

    def test_manual_reset_can_execute_code_not_needing_unknown_peripherals(self):
        result = diagnose_nc_reset(reset_rom(read_icr=False), reset="manual",
                                   nmi_high=None, max_steps=3)
        self.assertEqual(result["executed_instructions"], 3)
        self.assertEqual(result["stop"]["reason"], "instruction_limit")
        self.assertEqual(result["initial_sp"], "0xFFFFBF00")
        self.assertFalse(result["boot_complete"])

    def test_headless_presenter_all_matrix_results_and_invalid_roms(self):
        rom = reset_rom()
        runs = [diagnose_nc_reset(rom, reset=r, nmi_high=n, max_steps=3)
                for r in ("power", "manual") for n in (None, True, False)]
        runs += [diagnose_nc_reset(ROMImage("invalid", b"short"), max_steps=3),
                 diagnose_nc_reset(reset_rom(read_icr=False), max_steps=3)]
        for result in runs:
            with self.subTest(reason=result["stop"]["reason"]):
                view = present_reset_diagnostic(result)
                self.assertFalse(view["summary"]["boot_complete"])
                self.assertEqual(view["summary"]["phase"], "reset_diagnostic_only")
                self.assertIn("NOT verified", view["status"])
                self.assertEqual(view["summary"]["stop_reason"], result["stop"])
                self.assertEqual(view["summary"]["next_dependency"], result.get("next_dependency"))
                self.assertEqual(view["summary"]["attempted_instructions"],
                                 result.get("executed_instructions", 0))
                self.assertIsInstance(view["trace_text"], str)
                self.assertEqual(view["dependency_title"].startswith("Instruction budget"),
                                 result["stop"]["reason"] == "instruction_limit")
                self.assertEqual(json.dumps(view,sort_keys=True),
                                 json.dumps(present_reset_diagnostic(result),sort_keys=True))

    def test_presenter_never_confuses_partial_execution_with_verified_boot(self):
        fabricated = {"boot_complete": True, "executed_instructions": 100000,
                      "stop": {"reason": "instruction_limit"}, "trace": []}
        view = present_reset_diagnostic(fabricated)
        self.assertFalse(view["summary"]["boot_complete"])
        self.assertIn("NOT verified", view["status"])
        self.assertIn("Instruction budget", view["dependency_title"])

    def test_optional_unmodified_lf9veb_regressions(self):
        path = os.environ.get("MX5_NC_TEST_ROM")
        if not path:
            self.skipTest("Set MX5_NC_TEST_ROM for optional local-ROM check; never commit OEM firmware")
        rom = ROMImage("locally_supplied.bin", Path(path).read_bytes())
        if rom.sha256 != LF9VEB_SHA256:
            self.skipTest("Provided ROM is not original LF9VEB; synthetic matrix still tested")
        observed = {}
        for nmi, label in ((None, "unknown"), (True, "high"), (False, "low")):
            result = diagnose_nc_reset(rom, reset="power", nmi_high=nmi, max_steps=300)
            self.assertFalse(result["boot_complete"])
            observed[label] = (result["executed_instructions"], result["stop"]["reason"])
        self.assertEqual(observed["unknown"], (23, "missing_input"))
        self.assertEqual(observed["low"], (300, "instruction_limit"))
        self.assertGreater(observed["high"][0], 76)
        high = diagnose_nc_reset(rom, reset="power", nmi_high=True, max_steps=300)
        self.assertTrue(any(x.get("register") == "PEDR" and
                            x.get("access") == "write" and x.get("value") == 0xFFFF
                            for x in high["modelled_peripheral_accesses"]))
        manual = diagnose_nc_reset(rom, reset="manual", nmi_high=True, max_steps=300)
        self.assertFalse(manual["boot_complete"])
