import unittest
from ecu_workbench.sci import StoppedSci,BASE
from ecu_workbench.nc_boot import BootStop
from test_sh2_branch import program

class StoppedSciTests(unittest.TestCase):
    def sci(self,power=True):return StoppedSci(power_on=power,trace=[],stop_type=BootStop)

    def test_reset_banks_and_paired_big_endian_word(self):
        s=self.sci()
        for channel in range(5):
            a=BASE+8*channel
            self.assertEqual(s.access(a,2,'read'),255)
            s.access(a,2,'write',0x80A5)
            self.assertEqual(s.access(a,1,'read'),128)
            self.assertEqual(s.access(a+1,1,'read'),165)
            self.assertEqual(s.access(a+2,1,'read'),0)
        s.access(BASE,1,'write',0xFF)
        self.assertEqual(s.access(BASE+8,1,'read'),128)

    def test_manual_reset_retention_and_explicit_disable(self):
        s=self.sci(False)
        for offset in range(3):
            with self.assertRaises(BootStop):s.access(BASE+offset,1,'read')
        with self.assertRaises(BootStop):s.access(BASE,1,'write',128)
        s.access(BASE+2,1,'write',0)
        with self.assertRaises(BootStop):s.access(BASE,1,'read')
        s.access(BASE,2,'write',0x8000)
        self.assertEqual(s.access(BASE,2,'read'),0x8000)

    def test_enabled_modes_and_bad_width_rejected_atomically(self):
        s=self.sci()
        for value in (1,2,4,8,16,32,64,128,255):
            with self.assertRaises(BootStop):s.access(BASE+2,1,'write',value)
            self.assertEqual(s.values[0],[0,255,0])
        for offset,width in ((0,4),(1,2),(2,2)):
            with self.assertRaises(BootStop):s.access(BASE+offset,width,'write',0)
        self.assertFalse(s.handles(BASE+7));self.assertFalse(s.handles(BASE+40))

    def test_cpu_byte_write_and_readback(self):
        c=program(0x2340,0x6530);c.r[3]=BASE;c.r[4]=128
        r=c.run(2)
        self.assertEqual(r['completed_instructions'],2)
        self.assertEqual(c.r[5],0xFFFFFF80)
        self.assertEqual(r['interrupt_entries'],0)
