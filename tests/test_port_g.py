"""B34: Port G PGDR four-bit SH7058 data register regression tests."""
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, ROM_LIMIT
from ecu_workbench.port_g import PGDR_ADDRESS, PGIOR_ADDRESS


def image(code=b"\x00\x09"):
    data = bytearray(ROM_LIMIT)
    for i, value in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        data[4*i:4*i+4] = value.to_bytes(4, "big")
    data[0x100:0x100+len(code)] = code
    return ROMImage("synthetic", bytes(data))


class PortGTests(unittest.TestCase):
    def test_word_write_records_latch_not_real_pin(self):
        b = BootBus(image())
        b.write(PGDR_ADDRESS,2,0x000F)
        self.assertEqual(b.port_g.data,0x000F)
        self.assertEqual(b.peripheral_trace[-1]["register"],"PGDR")
        self.assertEqual(b.peripheral_trace[-1]["value"],0x000F)
        self.assertEqual(b.port_g.pin_known_mask,0)
        with self.assertRaises(BootStop) as cm:
            b.read(PGDR_ADDRESS,2)
        self.assertEqual(cm.exception.kind,"missing_input")
        b.write(PGIOR_ADDRESS,2,0x000F)
        self.assertEqual(b.read(PGDR_ADDRESS,2),0x000F)

    def test_reserved_bits_zero_or_rejected(self):
        b = BootBus(image())
        for width,address,value in ((2,PGDR_ADDRESS,0x0010),
                                    (2,PGDR_ADDRESS,0xFFFF),
                                    (1,PGDR_ADDRESS,1),
                                    (1,PGDR_ADDRESS+1,0x10)):
            with self.subTest(address=address,width=width,value=value):
                with self.assertRaises(BootStop) as cm:
                    b.write(address,width,value)
                self.assertEqual(cm.exception.kind,"invalid_peripheral_write")
                self.assertEqual(b.port_g.data,0)
        b.write(PGDR_ADDRESS,1,0)
        self.assertEqual(b.read(PGDR_ADDRESS,1),0)

    def test_endian_byte_and_input_readback(self):
        b = BootBus(image(),port_g_pin_values=0xA,port_g_pin_known_mask=0xF)
        b.write(PGDR_ADDRESS+1,1,0x05)
        self.assertEqual(b.read(PGDR_ADDRESS+1,1),0xA)  # direction input
        self.assertEqual(b.read(PGDR_ADDRESS,1),0)  # reserved byte
        self.assertEqual(b.read(PGDR_ADDRESS,2),0xA)
        b.write(PGIOR_ADDRESS,2,0x000F)
        self.assertEqual(b.read(PGDR_ADDRESS+1,1),0x05)
        self.assertEqual(b.read(PGDR_ADDRESS,2),0x05)
        b.write(PGIOR_ADDRESS,2,0x0003)
        self.assertEqual(b.read(PGDR_ADDRESS,2),0x09)  # A on inputs, 1 on outputs

    def test_partial_known_inputs_and_reset(self):
        b = BootBus(image(),port_g_pin_values=0xA,port_g_pin_known_mask=0xA)
        with self.assertRaises(BootStop) as cm:
            b.read(PGDR_ADDRESS+1,1)
        self.assertEqual(cm.exception.kind,"missing_input")
        b.write(PGIOR_ADDRESS,2,0x5)
        self.assertEqual(b.read(PGDR_ADDRESS,2),0xA)
        manual = BootBus(image(),power_on=False)
        self.assertEqual(manual.read(PGDR_ADDRESS,1),0)  # always-zero reserved byte
        with self.assertRaises(BootStop) as cm:
            manual.read(PGDR_ADDRESS,2)
        self.assertEqual(cm.exception.kind,"unknown_peripheral_reset_state")
        manual.write(PGDR_ADDRESS+1,1,0xA)
        manual.write(PGIOR_ADDRESS,2,0xF)
        self.assertEqual(manual.read(PGDR_ADDRESS,2),0xA)

    def test_width_alignment_bad_pin_values(self):
        b = BootBus(image())
        for action in (lambda: b.read(PGDR_ADDRESS,4),
                       lambda: b.write(PGDR_ADDRESS,4,0)):
            with self.assertRaises(BootStop) as cm:
                action()
            self.assertEqual(cm.exception.kind,"unsupported_access_size")
        with self.assertRaises(BootStop) as cm:
            b.read(PGDR_ADDRESS+1,2)
        self.assertEqual(cm.exception.kind,"unaligned_access")
        for v,m in ((-1,0xF),(16,0xF),(True,0xF),(0,0x10),(0,True)):
            with self.subTest(v=v,m=m),self.assertRaises(ValueError):
                b.port_g.set_pins(v,m)

    def test_observed_mov_word_opcode_2131(self):
        # MOV.L @(disp,PC),R1; MOV #15,R3; MOV.W R3,@R1
        data = bytearray(image(bytes.fromhex("D102 E30F 2131 0009")).data)
        data[0x10C:0x110] = PGDR_ADDRESS.to_bytes(4,"big")
        d = NCBootDiagnostic(ROMImage("synthetic",bytes(data)))
        result = d.run(4)
        self.assertEqual(result["executed_instructions"],4)
        self.assertEqual(result["stop"]["reason"],"instruction_limit")
        self.assertEqual(d.bus.port_g.data,0xF)
        self.assertTrue(any(a.get("register")=="PGDR" and a.get("access")=="write" and
                            a.get("width")==2 and a.get("value")==0x000F
                            for a in result["modelled_peripheral_accesses"]))
        self.assertFalse(result["boot_complete"])
