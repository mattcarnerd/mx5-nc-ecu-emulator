"""B31 offline baseline review never asserts a completed boot."""
import unittest
from ecu_workbench.trace_review import summarise, LF9VEB_SHA256

def baseline(*, sha=LF9VEB_SHA256, count=76, reason="unmodelled_peripheral",
             addr="0xFFFFF754", nmi="high"):
    return {
        "schema_version":1,"kind":"nc_sh7058_reset_baseline",
        "rom":{"sha256":sha,"size_bytes":1048576},
        "inputs":{"reset":"power","nmi":nmi,"max_steps":300},
        "result":{"executed_instructions":count,"pc_at_stop":"0x00000CB0",
                  "stop":{"reason":reason,"address":addr,"width":2,"access":"write"},
                  "first_unsupported_peripheral":
                  {"address":addr} if reason=="unmodelled_peripheral" else None,
                  "next_dependency":{"memory_access":{"address":addr}},
                  "trace_tail":[],"boot_complete":False}}

class TraceReviewTests(unittest.TestCase):
    def test_pre_b30_stop_is_identified(self):
        r=summarise(baseline())
        self.assertEqual(r["assessment"],"still_blocked_on_port_e")
        self.assertTrue(r["reference_scenario"])
        self.assertFalse(r["boot_complete"])

    def test_new_stop_not_claimed_as_verified_write(self):
        r=summarise(baseline(count=90,addr="0xFFFFF762"))
        self.assertEqual(r["assessment"],"past_previous_instruction_count_only")
        self.assertIn("cannot prove",r["limitations"])

    def test_not_same_conditions(self):
        for doc in (baseline(nmi="unknown"),
                    baseline(sha="a"*64),
                    baseline(count=20,addr="0xFFFFF760")):
            r=summarise(doc)
            self.assertFalse(r["boot_complete"])
        self.assertEqual(summarise(baseline(nmi="unknown"))["assessment"],
                         "different_rom_or_settings")
        self.assertEqual(summarise(baseline(count=20,addr="0xFFFFF760"))["assessment"],
                         "no_proven_progress")

    def test_reject_invalid_or_incomplete_reports(self):
        for report in ({}, {"schema_version":2},
                       {**baseline(), "rom":{"sha256":"oops"}},
                       {**baseline(), "result":{**baseline()["result"],
                                               "executed_instructions":-1}},
                       {**baseline(), "result":{**baseline()["result"],
                                               "stop":{}}}):
            with self.subTest(report=report),self.assertRaises(ValueError):
                summarise(report)
