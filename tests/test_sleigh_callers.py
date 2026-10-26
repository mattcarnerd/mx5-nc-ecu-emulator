import importlib.util
import os
import unittest
from tools.audit_sh2_callers import prove_mode_path,generated_caller_audit,audit_rom_caller

@unittest.skipUnless(importlib.util.find_spec('pypcode'),'Optional pinned independent audit dependency')
class SleighCallerTests(unittest.TestCase):
    def test_generated_positive_and_negative_paths(self):
        r=generated_caller_audit()
        self.assertEqual(r['positive_paths'],3)
        self.assertEqual(r['negative_paths_rejected'],4)
        self.assertFalse(r['full_control_flow_verified'])

    def test_idempotent_register_write_is_not_mistaken_for_no_writer(self):
        with self.assertRaises(ValueError):
            prove_mode_path(bytes.fromhex('e5036553605c'),[0,2],4)

    def test_branch_delay_slot_writer_is_included_in_lift(self):
        # Even if the supplied address list omits the slot, SLEIGH includes it.
        with self.assertRaises(ValueError):
            prove_mode_path(bytes.fromhex('e503a001e5040009605c'),[0,2],8)

    def test_invalid_path_and_consumer_do_not_create_a_proof(self):
        raw=bytes.fromhex('e5030009605d')
        for path,end in (([],4),([1],4),([0,100],4),([0,2],4)):
            with self.assertRaises(ValueError):prove_mode_path(raw,path,end)

    def test_optional_original_caller(self):
        path=os.environ.get('MX5_NC_TEST_ROM')
        if not path:self.skipTest('Optional local original-hash ROM')
        from ecu_workbench.core import ROMImage
        if ROMImage.from_file(path).sha256!='bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf':self.skipTest('Original hash required')
        r=audit_rom_caller(path);p=r['proof']
        self.assertEqual(r['literal_pc'],'0x000001E2')
        self.assertEqual(p['literal_value'],3)
        self.assertEqual(p['observed_instruction_events'],57)
        self.assertEqual(p['intervening_mode_writes'],0)
        self.assertFalse(p['entry_register_seeds_required'])
        self.assertFalse(p['branch_decisions_independently_verified'])
