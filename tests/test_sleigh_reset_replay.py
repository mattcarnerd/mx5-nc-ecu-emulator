import importlib.util
import os
import unittest
from tools.audit_sh2_reset import TranscriptPath,generated_reset_audit,audit_rom_reset

ENGINES=bool(importlib.util.find_spec('pypcode') and importlib.util.find_spec('z3'))
@unittest.skipUnless(ENGINES,'Optional pinned independent replay engines')
class ResetReplayTests(unittest.TestCase):
    def test_generated_reset_and_input_transcript_negatives(self):
        r=generated_reset_audit()
        self.assertEqual(r['positive_programs'],3)
        self.assertEqual(r['negative_transcripts_rejected'],4)
        self.assertFalse(r['unknown_input_selected'])

    def test_unsupplied_io_and_wrong_order_fail(self):
        m=TranscriptPath(b'00',{},[])
        with self.assertRaises(ValueError):m.load(0xFFFFD002,2)
        m=TranscriptPath(b'00',{},[{'kind':'write','address':0xFFFFD002,'width':2,'value':0,'mask':65535}])
        with self.assertRaises(ValueError):m.load(0xFFFFD002,2)

    def test_masked_peripheral_input_remains_symbolic(self):
        m=TranscriptPath(b'00',{},[{'kind':'read','address':0xFFFFD002,'width':2,'value':8,'mask':8}])
        v=m.load(0xFFFFD002,2)
        self.assertEqual(m.number(v&8),8)
        with self.assertRaises(ValueError):m.number(v)

    def test_no_rom_or_gap_writes(self):
        m=TranscriptPath(b'00',{},[])
        for address in (0,0x100000):
            with self.assertRaises(ValueError):m.store(address,1,m.z.BitVecVal(0,8))

    def test_optional_original_full_cpu_path(self):
        path=os.environ.get('MX5_NC_TEST_ROM')
        if not path:self.skipTest('Optional local original-hash ROM')
        from ecu_workbench.core import ROMImage
        if ROMImage.from_file(path).sha256!='bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf':self.skipTest('Original hash required')
        r=audit_rom_reset(path)
        self.assertEqual(r['result']['instruction_events'],1057)
        self.assertEqual(r['result']['conditional_decisions'],70)
        self.assertTrue(r['all_instruction_events_matched'])
        self.assertFalse(r['ram_initial_values_selected'])
        self.assertFalse(r['hardware_behavior_verified'])
