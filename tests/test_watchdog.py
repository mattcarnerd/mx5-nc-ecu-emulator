import unittest
from test_port_l import image
from ecu_workbench.nc_boot import BootBus,BootStop

class WatchdogTests(unittest.TestCase):
    def test_observed_control_and_counter_writes(self):
        b=BootBus(image()); self.assertEqual(b.read(0xFFFFEC13,1),0x1F)
        b.write(0xFFFFEC12,2,0x5A1F)
        b.write(0xFFFFEC10,2,0x5A00)
        self.assertEqual(b.read(0xFFFFEC11,1),0)
        b.write(0xFFFFEC10,2,0xA51F)
        self.assertEqual(b.read(0xFFFFEC10,1),0x1F)
        self.assertEqual(b.peripheral_trace[-2]['register'],'TCSR')

    def test_reset_controls_preserve_flag_and_reserved_ones(self):
        b=BootBus(image()); b.rstcsr.value=0x9F
        b.write(0xFFFFEC12,2,0x5A7F)
        self.assertEqual(b.read(0xFFFFEC13,1),0xFF)
        b.write(0xFFFFEC12,2,0xA500)
        self.assertEqual(b.read(0xFFFFEC13,1),0x7F)
        b.write(0xFFFFEC12,2,0x5A1F)
        self.assertEqual(b.read(0xFFFFEC13,1),0x1F)

    def test_flag_clear_requires_read_and_zero_cannot_set_flag(self):
        b=BootBus(image()); b.rstcsr.value=0x9F
        b.write(0xFFFFEC12,2,0xA500)
        self.assertEqual(b.rstcsr.value,0x9F)
        b.read(0xFFFFEC13,1); b.write(0xFFFFEC12,2,0xA500)
        self.assertEqual(b.rstcsr.value,0x1F)
        b.watchdog.tcsr=0x98
        b.write(0xFFFFEC10,2,0xA518)
        self.assertEqual(b.watchdog.tcsr,0x98)
        b.read(0xFFFFEC10,1); b.write(0xFFFFEC10,2,0xA518)
        self.assertEqual(b.watchdog.tcsr,0x18)
        b.write(0xFFFFEC10,2,0xA598)
        self.assertEqual(b.watchdog.tcsr,0x18)

    def test_invalid_keys_widths_reserved_and_running_fail_closed(self):
        b=BootBus(image())
        for a,w,v in ((0xFFFFEC12,2,0),(0xFFFFEC12,2,0x5A00),
                      (0xFFFFEC12,2,0xA580),(0xFFFFEC10,2,0xA500),
                      (0xFFFFEC10,2,0xA538),(0xFFFFEC10,1,0),
                      (0xFFFFEC11,2,0),(0xFFFFEC12,4,0)):
            before=(b.rstcsr.value,b.watchdog.tcsr,b.watchdog.tcnt,len(b.peripheral_trace))
            with self.subTest(a=a,w=w,v=v),self.assertRaises(BootStop): b.write(a,w,v)
            self.assertEqual(before,(b.rstcsr.value,b.watchdog.tcsr,b.watchdog.tcnt,len(b.peripheral_trace)))
        for a,w in ((0xFFFFEC12,1),(0xFFFFEC12,2),(0xFFFFEC13,2),(0xFFFFEC10,2)):
            with self.assertRaises(BootStop): b.read(a,w)

    def test_disabled_counter_read_write_and_stop_initialization(self):
        b=BootBus(image()); b.write(0xFFFFEC10,2,0x5AFE)
        self.assertEqual(b.read(0xFFFFEC11,1),0xFE)
        b.write(0xFFFFEC10,2,0xA51A)
        self.assertEqual(b.read(0xFFFFEC11,1),0)
        self.assertEqual(b.read(0xFFFFEC10,1),0x1A)

    def test_manual_reset_retained_state_is_unknown(self):
        b=BootBus(image(),power_on=False)
        with self.assertRaises(BootStop): b.read(0xFFFFEC13,1)
        b.write(0xFFFFEC12,2,0x5A1F)
        self.assertEqual(b.rstcsr.known_mask,0x7F)
        with self.assertRaises(BootStop): b.read(0xFFFFEC13,1)
        with self.assertRaises(BootStop): b.read(0xFFFFEC11,1)
