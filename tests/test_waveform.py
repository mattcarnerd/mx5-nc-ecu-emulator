import unittest
from test_sh2_branch import program
from ecu_workbench.atu import *
from ecu_workbench.waveform import *

class WaveformTests(unittest.TestCase):
    def test_rpm_phase_reproducibility_and_actual_capture(self):
        f=crank_cam_fixture(rpm=600,tick_hz=10000,teeth=2,cam_phase_degrees=180)
        self.assertFalse(f['validated_NC_pattern']);self.assertEqual(f['duration_ticks'],2000)
        self.assertEqual([e['tick'] for e in f['events'] if e['role']=='cam'],[500,1500])
        self.assertEqual(len([e for e in f['events'] if e['role']=='crank']),8)
        results=[]
        for _ in range(2):
            t=program(0x0009).bus.atu;t.write(TIOR,1,0x77);t.write(TIER,2,3);t.write(TSTR,1,2)
            events=play_fixture(t,f);results.append(events)
            self.assertEqual(t.read(GR,2),1750);self.assertEqual(t.read(GRB,2),1500)
            self.assertEqual(t.read(TSR,2),3);self.assertTrue(t.interrupt_pending)
            self.assertEqual(len(events),10)
        self.assertEqual(*results)

    def test_invalid_inputs_and_resolution(self):
        for update in ({'rpm':0},{'tick_hz':0},{'teeth':0},{'cam_phase_degrees':720},{'tick_hz':1}):
            args=dict(rpm=600,tick_hz=10000,teeth=2,cam_phase_degrees=0);args.update(update)
            with self.assertRaises(ValueError):crank_cam_fixture(**args)
