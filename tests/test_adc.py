import unittest
from test_sh2_branch import program
from ecu_workbench.adc import *
from ecu_workbench.nc_boot import BootStop

class AdcTests(unittest.TestCase):
    def adc(self):return program(0x0009).bus.adc
    def test_ideal_scaling_and_bytes_and_completion(self):
        for v,count in ((0,0),('0.0048828125',1),('2.5',512),(5,1023)):
            a=self.adc();a.set_input(v,5);a.write(ADCR0,1,0x2F)
            self.assertEqual(a.read(ADCSR0,1),0);self.assertEqual(a.read(ADDR0,2),0)
            a.complete_conversion();self.assertEqual(a.read(ADDR0,2),count<<6)
            self.assertEqual(a.read(ADDR0,1),(count<<6)>>8)
            self.assertEqual(a.read(ADDR0+1,1),(count<<6)&255)
            self.assertEqual(a.read(ADCSR0,2),0x800F)

    def test_interrupt_flag_clear_sampling_and_cancel(self):
        a=self.adc();a.set_input(1,5);a.write(ADCSR0,1,64);a.write(ADCR0,1,47)
        a.set_input(5,5);a.complete_conversion();self.assertEqual(a.data,204<<6)
        self.assertTrue(a.interrupt_pending);a.write(ADCSR0,1,64);self.assertTrue(a.interrupt_pending)
        a.read(ADCSR0,1);a.write(ADCSR0,1,64);self.assertFalse(a.interrupt_pending)
        a.write(ADCR0,1,47);generation=a.generation;a.write(ADCR0,1,15)
        a.complete_conversion(generation);self.assertEqual(a.data,204<<6)

    def test_missing_manual_unsupported_and_validation(self):
        a=self.adc();a.write(ADCR0,1,47)
        with self.assertRaises(BootStop):a.complete_conversion()
        self.assertEqual(a.data,0);self.assertEqual(a.csr,0)
        for v,r in ((-1,5),(6,5),(1,0),(True,5),('nan',5)):
            with self.assertRaises((ValueError,ZeroDivisionError)):a.set_input(v,r)
        for address,width,value in ((ADDR0,2,0),(ADCSR0,1,1),(ADCSR0,1,16),(ADCR0,1,0x6F),(ADCR0,2,0)):
            with self.assertRaises(BootStop):a.write(address,width,value)
        a.data=None
        with self.assertRaises(BootStop):a.read(ADDR0,2)
