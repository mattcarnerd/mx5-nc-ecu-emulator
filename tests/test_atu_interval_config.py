import unittest
from ecu_workbench.atu import Atu1A,ITVRR,TSTR
from ecu_workbench.nc_boot import BootStop

class IntervalTriggerConfigurationTests(unittest.TestCase):
    def test_stopped_configuration_is_readwrite_without_events(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        for address in ITVRR:
            self.assertEqual(a.read(address,1),0)
            for value in (0,1,0x55,0xAA,0xFF):
                a.write(address,1,value);self.assertEqual(a.read(address,1),value)
        self.assertEqual(a.events,[]);self.assertEqual(a.ticks,0)
        self.assertFalse(a.interrupt_pending)

    def test_manual_unknown_zero_disable_and_width_guards(self):
        a=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        for address in ITVRR:
            with self.assertRaises(BootStop):a.read(address,1)
            with self.assertRaises(BootStop):a.write(address,1,1)
            a.write(address,1,0);self.assertEqual(a.read(address,1),0)
            for width in (2,4):
                with self.assertRaises(BootStop):a.write(address,width,0)
        a.write(TSTR,1,0);a.write(ITVRR[0],1,0xFF)
        self.assertEqual(a.read(ITVRR[0],1),0xFF)
