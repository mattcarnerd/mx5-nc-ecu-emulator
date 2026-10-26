import importlib.util
import os
import unittest
from tools.audit_sh2_path import SymbolicPath,generated_path_audit,audit_rom_path

HAS_ENGINES=bool(importlib.util.find_spec('pypcode') and importlib.util.find_spec('z3'))
@unittest.skipUnless(HAS_ENGINES,'Optional pinned independent symbolic audit engines')
class SleighPathTests(unittest.TestCase):
    def test_generated_paths_and_negative_controls(self):
        r=generated_path_audit()
        self.assertEqual(r['positive_paths'],3);self.assertEqual(r['negative_paths_rejected'],3)
        self.assertFalse(r['observed_outcomes_forced'])

    def test_unsigned_and_signed_comparisons_are_distinct(self):
        for op,t in ((0x3506,0),(0x3503,1)):
            data=b''.join(x.to_bytes(2,'big') for x in (0xE503,op,0x605C))
            m=SymbolicPath(data,{'r0':0xFFFFFFFF});m.run(0,4)
            self.assertEqual(m.number(m.get(m.context.registers['sr'])&1),t)

    def test_symbolic_mask_zero_cancels_without_selecting_unknown(self):
        m=SymbolicPath(bytes.fromhex('e503e1002019605c'))
        m.run(0,6)
        self.assertEqual(m.number(m.get(m.context.registers['r0'])),0)

    def test_unwritten_ram_stays_symbolic(self):
        m=SymbolicPath(bytes.fromhex('e503'),{'r5':3})
        with self.assertRaises(ValueError):m.number(m.load(0xFFFF8000,2))
        with self.assertRaises(ValueError):m.load(0xFFFFD002,2)

    def test_optional_original_path(self):
        path=os.environ.get('MX5_NC_TEST_ROM')
        if not path:self.skipTest('Optional local original-hash ROM')
        from ecu_workbench.core import ROMImage
        if ROMImage.from_file(path).sha256!='bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf':self.skipTest('Original hash required')
        r=audit_rom_path(path)
        self.assertEqual(r['result']['instruction_events'],57)
        self.assertEqual(r['result']['conditional_decisions'],2)
        self.assertEqual(r['result']['call_targets'],1)
        self.assertFalse(r['branch_choices_forced_from_observation'])
        self.assertFalse(r['full_reset_trace_verified'])
