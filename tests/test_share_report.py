"""B32: headless tests for reduced GUI/CLI blocker export."""
import json
import unittest

from ecu_workbench.share_report import make_shareable_blocker_report
from ecu_workbench.trace_review import LF9VEB_SHA256


def detailed(*, sha=LF9VEB_SHA256, steps=300, port_e=True, count=85,
             stop_addr="0xFFFFF762", filename="PRIVATE-DO-NOT-EXPORT.bin"):
    return {
        "image":{"name":filename, "sha256":sha, "size_bytes":1048576,
                 "private_path":"C:\\secret\\original.bin"},
        "nc_rom_assessment":{"source":"private notes", "untrusted":"test"},
        "diagnostic_settings":{"reset":"power", "nmi":"high",
                               "max_steps":steps, "explicit_pin_values":False},
        "nc_boot":{
            "rom_sha256":sha,"executed_instructions":count,
            "reset":"power","nmi_high":True,"pc_at_stop":"0x00000CC0",
            "stop":{"reason":"unmodelled_peripheral", "address":stop_addr,
                    "access":"write","width":2,"value":"0x00000000",
                    "detail":"Sensitive local path C:\\secret\\original.bin"},
            "next_dependency":{
                "category":"unmodelled_hardware_register",
                "instruction_pc":"0x00000CBE","opcode":"2121",
                "memory_access":{"address":stop_addr,"access":"write",
                                 "width":2,"value":"0x00000000"},
                "prior_instructions":["SECRET-BYTES"],
                "detail":"PRIVATE DETAILS"},
            "trace":[{"opcode":"SECRET-TRACE"}],
            "modelled_peripheral_accesses":
                ([{"register":"PEDR","access":"write","width":2,"value":0xFFFF}]
                 if port_e else []),
            "boot_complete":True,
        }
    }


class ShareReportTests(unittest.TestCase):
    def test_exact_run_reports_port_e_write(self):
        data=detailed()
        share=make_shareable_blocker_report(data)
        self.assertTrue(share["reference_lf9veb_scenario"])
        self.assertTrue(share["pedr_word_write_ffff_in_peripheral_trace"])
        self.assertEqual(share["assessment"],"port_e_write_observed_in_diagnostic")
        self.assertEqual(share["executed_instructions"],85)
        self.assertEqual(share["next_dependency"]["instruction_pc"],"0x00000CBE")
        self.assertFalse(share["boot_complete"])
        self.assertEqual(share,make_shareable_blocker_report(data))

    def test_count_only_does_not_prove_write(self):
        output=make_shareable_blocker_report(detailed(port_e=False,count=150))
        self.assertEqual(output["assessment"],"port_e_write_not_confirmed")
        self.assertFalse(output["pedr_word_write_ffff_in_peripheral_trace"])

    def test_old_failure_still_at_port_e(self):
        output=make_shareable_blocker_report(
            detailed(port_e=False,count=76,stop_addr="0xFFFFF754"))
        self.assertEqual(output["assessment"],"blocked_at_historical_port_e_access")

    def test_different_rom_and_inputs_not_reference(self):
        for change in (
            lambda d: d["image"].update(sha256="a"*64) or d["nc_boot"].update(rom_sha256="a"*64),
            lambda d: d["diagnostic_settings"].update(explicit_pin_values=True),
            lambda d: d["diagnostic_settings"].update(nmi="unknown"),
            lambda d: d["diagnostic_settings"].update(max_steps=500),
        ):
            d=detailed()
            change(d)
            with self.subTest(settings=d["diagnostic_settings"]):
                result=make_shareable_blocker_report(d)
                self.assertEqual(result["assessment"],"not_reference_scenario")

    def test_whitelisted_output_removes_names_paths_rom_bytes_and_traces(self):
        d=detailed()
        d["image"]["data"]="PRIVATE-ROM-BYTES"
        output=json.dumps(make_shareable_blocker_report(d))
        for disallowed in (
            "PRIVATE-DO-NOT-EXPORT", "C:\\secret", "PRIVATE-ROM-BYTES",
            "SECRET-TRACE", "SECRET-BYTES", "PRIVATE DETAILS",
            "Sensitive local path", "private notes",
        ):
            with self.subTest(disallowed=disallowed):
                self.assertNotIn(disallowed,output)

    def test_incomplete_and_forged_hash_mismatch_rejected(self):
        for bad in ({}, {"image":{},"nc_boot":{}}, {"image":{"sha256":"xyz"},"nc_boot":{}},
                    {**detailed(),"nc_boot":{**detailed()["nc_boot"],"rom_sha256":"a"*64}},
                    {**detailed(),"nc_boot":{**detailed()["nc_boot"],"executed_instructions":-1}},
                    {**detailed(),"nc_boot":{**detailed()["nc_boot"],"modelled_peripheral_accesses":{}}},
                    {**detailed(),"nc_boot":{**detailed()["nc_boot"],"stop":{}}}):
            with self.subTest(bad=str(bad)[:70]),self.assertRaises(ValueError):
                make_shareable_blocker_report(bad)

    def test_port_f_write_evidence_comes_from_trace_not_count(self):
        d = detailed(count=200, port_e=True)
        self.assertFalse(make_shareable_blocker_report(d)["pfdr_word_write_ffff_in_peripheral_trace"])
        d["nc_boot"]["modelled_peripheral_accesses"] += [
            {"register":"PFDR","access":"read","width":2,"value":0xFFFF},
            {"register":"PFDR","access":"write","width":1,"value":0xFF},
        ]
        self.assertFalse(make_shareable_blocker_report(d)["pfdr_word_write_ffff_in_peripheral_trace"])
        d["nc_boot"]["modelled_peripheral_accesses"].append(
            {"register":"PFDR","access":"write","width":2,"value":0xFFFF}
        )
        self.assertTrue(make_shareable_blocker_report(d)["pfdr_word_write_ffff_in_peripheral_trace"])

    def test_pgdr_word_write_flag_requires_actual_trace(self):
        d = detailed(count=300)
        self.assertFalse(make_shareable_blocker_report(d)["pgdr_word_write_000f_in_peripheral_trace"])
        d["nc_boot"]["modelled_peripheral_accesses"].extend([
            {"register":"PGDR","access":"read","width":2,"value":15},
            {"register":"PGDR","access":"write","width":1,"value":15},
        ])
        self.assertFalse(make_shareable_blocker_report(d)["pgdr_word_write_000f_in_peripheral_trace"])
        d["nc_boot"]["modelled_peripheral_accesses"].append(
            {"register":"PGDR","access":"write","width":2,"value":15})
        self.assertTrue(make_shareable_blocker_report(d)["pgdr_word_write_000f_in_peripheral_trace"])

    def test_mixed_traces_need_correct_width_value_and_access(self):
        d=detailed(port_e=False)
        d["nc_boot"]["modelled_peripheral_accesses"]=[
            {"register":"PEDR","access":"read","width":2,"value":0xFFFF},
            {"register":"PEDR","access":"write","width":1,"value":0xFF},
            {"register":"PDDR","access":"write","width":2,"value":0xFFFF},
        ]
        self.assertFalse(make_shareable_blocker_report(d)["pedr_word_write_ffff_in_peripheral_trace"])
