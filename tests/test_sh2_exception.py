import unittest
from test_sh2_branch import program
from test_sh2_compare import cpu
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootStop
from ecu_workbench.sh2_control import load_sr,read_sr


def trap_cpu():
    d=program(0xC320,0xE107);data=bytearray(d.bus.image.data)
    data[0x80:0x84]=(0x400).to_bytes(4,'big')
    data[0x400:0x404]=bytes.fromhex('002B E209')
    d.bus.image=ROMImage('synthetic',bytes(data));load_sr(d,0x201)
    return d

class ExceptionTests(unittest.TestCase):
    def test_trap_frame_vector_and_return_with_slot(self):
        d=trap_cpu();sp=d.reg(15);d.execute()
        self.assertEqual(d.pc,0x400);self.assertEqual(d.r[15],sp-8)
        self.assertEqual(d.bus.read(sp-8,4),0x102)
        self.assertEqual(d.bus.read(sp-4,4),0x201)
        r=d.run(4)
        self.assertEqual((d.r[1],d.r[2],d.r[15],d.pc),(7,9,sp,0x104))
        self.assertEqual(read_sr(d),0x201);self.assertEqual(r['exception_entries'],1)
        self.assertFalse(r['boot_complete']);self.assertTrue(d.trace[2]['delay_slot'])

    def test_vbr_and_unsigned_vector_index(self):
        d=program(0xC3FF);d.vbr=0x200;load_sr(d,0)
        data=bytearray(d.bus.image.data);data[0x5FC:0x600]=(0x700).to_bytes(4,'big')
        d.bus.image=ROMImage('synthetic',bytes(data));d.execute()
        self.assertEqual(d.pc,0x700)
        self.assertEqual(d.exception_events[-1]['vector'],255)

    def test_rte_restores_sr_before_slot_and_masks_reserved_bits(self):
        d=program(0x002B,0x0008);sp=d.reg(15)
        d.bus.write(sp,4,0x500);d.bus.write(sp+4,4,0xFFFFFFFF)
        d.run(1);self.assertEqual(read_sr(d),0x3F3)
        self.assertEqual(d.r[15],sp+8);self.assertEqual(d.pc,0x102)
        d.run(2);self.assertEqual(d.pc,0x500);self.assertEqual(read_sr(d),0x3F2)

    def test_illegal_slot_has_no_stack_or_sr_mutation(self):
        for op in (0xC320,0x002B):
            d=program(0xA000,op);load_sr(d,0x201);sp=d.reg(15)
            r=d.run(2);self.assertEqual(r['stop']['reason'],'illegal_delay_slot')
            self.assertEqual(d.r[15],sp);self.assertEqual(read_sr(d),0x201)
            self.assertFalse(any(d.bus.ram_valid))

    def test_unknown_sr_stops_before_frame_write(self):
        d=program(0xC320);sp=d.reg(15)
        with self.assertRaises(BootStop) as c:d.execute()
        self.assertEqual(c.exception.kind,'unknown_status')
        self.assertEqual(d.r[15],sp);self.assertFalse(any(d.bus.ram_valid))

    def test_uninitialised_rte_second_word_keeps_partial_sp_progress(self):
        d=program(0x002B);sp=d.reg(15);d.bus.write(sp,4,0x500)
        with self.assertRaises(BootStop) as c:d.execute()
        self.assertEqual(c.exception.kind,'uninitialised_ram')
        self.assertEqual(d.r[15],sp+4);self.assertEqual(d.clock.ticks,0)

    def test_bad_vector_fetch_keeps_documented_frame_writes(self):
        d=trap_cpu();d.vbr=0x200000;sp=d.reg(15)
        with self.assertRaises(BootStop) as c:d.execute()
        self.assertEqual(c.exception.kind,'unmapped_memory')
        self.assertEqual(d.r[15],sp-8);self.assertEqual(d.bus.read(sp-8,4),0x102)
        self.assertEqual(d.exception_entries,0)
