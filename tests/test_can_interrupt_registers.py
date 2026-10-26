import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootBus,BootStop,NCBootDiagnostic
from ecu_workbench.known_bits import KnownBits
from ecu_workbench.hcan import IRR_ADDRESSES,IMR_ADDRESSES,IRR_WRITABLE,IRR_DERIVED,STATUS_FIXED,MCR_ADDRESSES

class CanInterruptRegisterTests(unittest.TestCase):
    def test_reset_mutable_w1c_and_mask_independence(self):
        b=program(0x0009).bus
        for ch,a in enumerate(IRR_ADDRESSES):
            self.assertEqual(b.read(a,2),1)
            self.assertEqual(b.read(IMR_ADDRESSES[ch],2),0xFFFF)
            b.write(a,2,0);self.assertEqual(b.read(a,2),1)
            b.write(a,2,0xFFFE);self.assertEqual(b.read(a,2),1)
            b.write(IMR_ADDRESSES[ch],2,0);self.assertEqual(b.read(a,2),1)
            b.write(a,2,1);self.assertEqual(b.read(a,2),0)
            b.write(IMR_ADDRESSES[ch],2,0xA5A5)
            self.assertEqual(b.read(IMR_ADDRESSES[ch],2),0xA5A5)
            self.assertEqual(b.read(a,2),0)

    def test_read_only_derived_flags_clear_only_with_proven_source_bank_clears(self):
        b=program(0x0009).bus
        b.hcan.irr[0]=KnownBits(0xFFFF,0xFFFF)
        for offset in (0x40,0x48,0x30,0x58):
            b.hcan.mailbox_flags[0xFFFFD000+offset]=KnownBits(1,0xFFFF)
        b.write(IRR_ADDRESSES[0],2,0xFFFF)
        self.assertEqual(b.read(IRR_ADDRESSES[0],2),IRR_DERIVED)
        for a in STATUS_FIXED:
            if a<0xFFFFD800:b.write(a,2,0xFFFF)
        self.assertEqual(b.read(IRR_ADDRESSES[0],2),0)
        self.assertEqual(b.read(IRR_ADDRESSES[1],2),1)

    def test_unknown_manual_and_clear_knowledge_no_event_selection(self):
        b=BootBus(program(0x0009).bus.image,power_on=False)
        b.write(IRR_ADDRESSES[0],2,0xFFFF)
        self.assertEqual(b.read_cpu_word(IRR_ADDRESSES[0]).mask,IRR_WRITABLE)
        with self.assertRaises(BootStop):b.read(IRR_ADDRESSES[0],2)
        with self.assertRaises(BootStop):b.read(IMR_ADDRESSES[0],2)
        for a in STATUS_FIXED:
            if a<0xFFFFD800:b.write(a,2,0xFFFF)
        self.assertEqual(b.read(IRR_ADDRESSES[0],2),0)
        b.write(IMR_ADDRESSES[0],2,0x1234)
        self.assertEqual(b.read(IMR_ADDRESSES[0],2),0x1234)

    def test_word_guard_and_explicit_reset_completion(self):
        image=program(0x0009).bus.image
        d=NCBootDiagnostic(image,hcan_fixture={'reset_completion_ticks':1,'recessive_bus_ticks':None})
        for a in IRR_ADDRESSES+IMR_ADDRESSES:
            for w in (1,4):
                with self.assertRaises(BootStop):d.bus.write(a,w,0)
            with self.assertRaises(BootStop):d.bus.read(a+1,1)
        d.bus.write(IRR_ADDRESSES[0],2,0xFFFF);d.bus.write(IMR_ADDRESSES[0],2,0)
        d.bus.write(MCR_ADDRESSES[0],2,1)
        with self.assertRaises(BootStop):d.bus.read(IRR_ADDRESSES[0],2)
        d.clock.completed_instruction()
        self.assertEqual(d.bus.read(IRR_ADDRESSES[0],2),1)
        self.assertEqual(d.bus.read(IMR_ADDRESSES[0],2),0xFFFF)
