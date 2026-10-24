import unittest
from test_sh2_branch import program
from ecu_workbench.fpu import FpuState,FPSCR_FIXED

class FpuTests(unittest.TestCase):
    def test_reset_and_control_register_masks(self):
        f=FpuState();self.assertEqual(f.fr,[None]*16);self.assertIsNone(f.fpul)
        self.assertEqual(f.fpscr,0x40001)
        d=program(0x416A,0x026A);d.r[1]=0xFFFFFFFF;d.run(2)
        self.assertEqual(d.r[2],0x58C61)
        d=program(0x415A,0x025A);d.r[1]=0xAABBCCDD;d.run(2)
        self.assertEqual(d.r[2],0xAABBCCDD)

    def test_unknown_and_memory_faults_do_not_change_stack(self):
        d=program(0x005A);r=d.run(1);self.assertEqual(r['stop']['reason'],'unknown_register')
        d=program(0x4162);d.r[1]=0xFFFF0001;d.run(1)
        self.assertEqual(d.r[1],0xFFFF0001)
        d=program(0x4166);d.r[1]=0xFFFF0000;d.run(1)
        self.assertEqual(d.r[1],0xFFFF0000);self.assertEqual(d.fpu.fpscr,FPSCR_FIXED)

    def test_memory_save_restore_and_isolation(self):
        d=program(0x4152,0x4256);d.fpu.fpul=0x87654321
        d.r[1]=0xFFFF0010;d.r[2]=0xFFFF000C;d.run(2)
        self.assertEqual(d.fpu.fpul,0x87654321);self.assertEqual(d.r[1],0xFFFF000C)
        self.assertEqual(d.r[2],0xFFFF0010);self.assertIsNone(FpuState().fpul)
