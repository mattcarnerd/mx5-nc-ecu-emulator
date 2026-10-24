import unittest
from ecu_workbench.dual_capture_fixture import run_dual_capture_fixture

class DualCaptureFixtureTests(unittest.TestCase):
    def test_both_clock_sources_real_firmware_handlers_and_rollover(self):
        for source in ('internal','external'):
            result=run_dual_capture_fixture(clock_source=source)
            self.assertTrue(result['fixture_passed'],result)
            self.assertEqual(result['capture_words'],[65535,1])
            self.assertEqual(result['interrupt_vectors'],[96,104,97])
            self.assertEqual(result['clock_fixture']['selected_counter_ticks'],3)
            self.assertFalse(result['manufacturer_firmware_used'])
            self.assertFalse(result['boot_complete'])
            self.assertFalse(result['physical_timing_verified'])
            self.assertIsNone(result['clock_fixture']['frequency_hz'])
            self.assertEqual(result,run_dual_capture_fixture(clock_source=source))

    def test_budget_and_required_source(self):
        self.assertFalse(run_dual_capture_fixture(clock_source='internal',max_steps=80)['fixture_passed'])
        for source in ('guess',None):
            with self.assertRaises(ValueError):run_dual_capture_fixture(clock_source=source)
        for budget in (0,10001,True):
            with self.assertRaises(ValueError):run_dual_capture_fixture(clock_source='internal',max_steps=budget)
