import unittest
from ecu_workbench.atu import Atu1A,STOPPED_COUNTERS
from ecu_workbench.nc_boot import BootStop

class StoppedTimerCounterTests(unittest.TestCase):
    def test_documented_resets_widths_and_independent_full_range_storage(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for address,(width,_,_,initial) in STOPPED_COUNTERS.items():
            self.assertEqual(a.read(address,width),initial)
        for address,(width,_,_,_) in STOPPED_COUNTERS.items():
            for value in (0,1,(1<<(width*8))-1):
                before=dict(a.regs);a.write(address,width,value)
                self.assertEqual(a.read(address,width),value)
                for other in before:
                    if other!=address:self.assertEqual(a.regs[other],before[other])
        self.assertEqual(a.events,[]);self.assertEqual(a.ticks,0)

    def test_running_unknown_and_wrong_widths_are_guarded(self):
        for address,(width,start,bit,initial) in STOPPED_COUNTERS.items():
            a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
            a.regs[start]=bit
            with self.assertRaises(BootStop):a.write(address,width,0)
            with self.assertRaises(BootStop):a.read(address,width)
            self.assertEqual(a.regs[address],initial);a.regs[start]=0
            for wrong in (1,2,4):
                if wrong!=width:
                    with self.assertRaises(BootStop):a.write(address,wrong,0)
            m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
            with self.assertRaises(BootStop):m.read(address,width)
            with self.assertRaises(BootStop):m.write(address,width,0)
            m.regs[start]=0;m.write(address,width,0)
            self.assertEqual(m.read(address,width),0)
