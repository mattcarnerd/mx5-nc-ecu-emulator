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

    def test_raw_moves_all_bits_memory_and_indexing(self):
        for bits in (0,0x80000000,0x7FC12345,0xFFFFFFFF,0x00000001):
            d=program(0xF10C,0xF21B,0xF329,0xF31D,0xF40D)
            d.fpu.fr[0]=bits;d.r[2]=0xFFFF0010;d.run(5)
            self.assertEqual(d.fpu.fr[4],bits);self.assertEqual(d.r[2],0xFFFF0010)
            self.assertEqual(d.bus.read(0xFFFF000C,4),bits)
        d=program(0xF21A);d.r[2]=0xFFFF0001;d.fpu.fr[1]=1;d.run(1)
        self.assertEqual(d.r[2],0xFFFF0001)

    def test_conversions_fixed_toward_zero_and_dn(self):
        for integer,bits in ((0,0),(-1,0xBF800000),(16777217,0x4B800000),(-2147483648,0xCF000000)):
            d=program(0xF02D);d.fpu.fpul=integer&0xFFFFFFFF;d.run(1)
            self.assertEqual(d.fpu.fr[0],bits)
        for bits,integer in ((0x3FE00000,1),(0xBFE00000,-1),(1,0),(0x80000001,0)):
            d=program(0xF03D);d.fpu.fr[0]=bits;d.run(1)
            self.assertEqual(d.fpu.fpul,integer&0xFFFFFFFF)
        for bits in (0x7F800000,0x7FC00000,0x4F000000):
            d=program(0xF03D);d.fpu.fr[0]=bits;d.fpu.fpul=99;r=d.run(1)
            self.assertEqual(r['stop']['reason'],'unsupported_fpu_mode');self.assertEqual(d.fpu.fpul,99)

    def test_immediates_unknown_and_index_forms(self):
        d=program(0xF08D,0xF19D);d.run(2)
        self.assertEqual(d.fpu.fr[:2],[0,0x3F800000])
        d=program(0xF10C);r=d.run(1);self.assertEqual(r['stop']['reason'],'unknown_register')
        d=program(0xF217,0xF326);d.r[0]=4;d.r[2]=0xFFFF0000;d.fpu.fr[1]=0xAABBCCDD;d.run(2)
        self.assertEqual(d.fpu.fr[3],0xAABBCCDD)
