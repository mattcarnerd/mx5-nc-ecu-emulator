import importlib.util
import os
import unittest
from tools.audit_sh2_sleigh import LiftMachine,metadata,synthetic_audit,audit_rom

@unittest.skipUnless(importlib.util.find_spec('pypcode'),'Optional pinned independent audit dependency')
class SleighAuditTests(unittest.TestCase):
    def test_generated_differential_vectors(self):
        r=synthetic_audit()
        self.assertEqual(r['generated_vectors'],864)
        self.assertTrue(r['all_matched'])

    def test_unknown_entry_state_and_unsupported_operations_fail(self):
        with self.assertRaises(ValueError):LiftMachine({}).run(bytes.fromhex('605c'))
        with self.assertRaises(ValueError):LiftMachine({'r0':0}).run(bytes.fromhex('001b'))

    def test_sla_identity_and_concrete_seed_contract(self):
        m=metadata()
        self.assertEqual(m['pypcode_version'],'4.0.1')
        self.assertEqual(m['language'],'SuperH:BE:32:SH-2')
        self.assertEqual(len(m['sla_sha256']),64)
        with self.assertRaises(ValueError):LiftMachine({'r5':None})

    def test_optional_original_rom_window(self):
        source=os.environ.get('MX5_NC_TEST_ROM')
        if not source:self.skipTest('Optional local original-hash ROM')
        from ecu_workbench.core import ROMImage
        if ROMImage.from_file(source).sha256!='bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf':self.skipTest('Original hash required')
        r=audit_rom(source)
        self.assertTrue(r['all_matched']);self.assertEqual(r['mode'],3)
        self.assertEqual(r['store'],{'address':'0xFFFFD104','width':2,'value':'0x2308'})
        self.assertFalse(r['hardware_behavior_verified'])
