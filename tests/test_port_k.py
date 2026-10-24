"""B37: PKDR SH7058 Port K fail-closed regression tests."""
import unittest

from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, ROM_LIMIT
from ecu_workbench.port_k import PKDR_ADDRESS, PKIOR_ADDRESS


def image(code=b"\x00\x09"):
    data=bytearray(ROM_LIMIT)
    for idx,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        data[idx*4:idx*4+4]=v.to_bytes(4,"big")
    data[0x100:0x100+len(code)]=code
    return ROMImage("synthetic",bytes(data))


class PortKTests(unittest.TestCase):
    def test_word_write_latch_and_missing_pins(self):
        b=BootBus(image())
        b.write(PKDR_ADDRESS,2,0xFFFF)
        self.assertEqual(b.port_k.data,0xFFFF)
        self.assertEqual(b.port_k.pin_known_mask,0)
        self.assertEqual(b.peripheral_trace[-1]["register"],"PKDR")
        self.assertEqual(b.peripheral_trace[-1]["scope"],"output_latch_only")
        with self.assertRaises(BootStop) as caught:
            b.read(PKDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,"missing_input")
        b.write(PKIOR_ADDRESS,2,0xFFFF)
        self.assertEqual(b.read(PKDR_ADDRESS,2),0xFFFF)

    def test_big_endian_byte_latches(self):
        b=BootBus(image())
        b.write(PKIOR_ADDRESS,2,0xFFFF)
        b.write(PKDR_ADDRESS,1,0x12)
        b.write(PKDR_ADDRESS+1,1,0x34)
        self.assertEqual(b.read(PKDR_ADDRESS,2),0x1234)
        self.assertEqual(b.read(PKDR_ADDRESS,1),0x12)
        self.assertEqual(b.read(PKDR_ADDRESS+1,1),0x34)

    def test_explicit_input_and_mixed_direction(self):
        b=BootBus(image(),port_k_pin_values=0xA5A5,port_k_pin_known_mask=0xFFFF)
        b.write(PKDR_ADDRESS,2,0xFFFF)
        self.assertEqual(b.read(PKDR_ADDRESS,2),0xA5A5)
        b.write(PKIOR_ADDRESS,2,0x00FF)
        self.assertEqual(b.read(PKDR_ADDRESS,2),0xA5FF)
        self.assertEqual(b.peripheral_trace[-1]["physical_input_mask"],"0xFF00")

    def test_partial_input_mask(self):
        b=BootBus(image(),port_k_pin_values=0x00A5,port_k_pin_known_mask=0x00FF)
        self.assertEqual(b.read(PKDR_ADDRESS+1,1),0xA5)
        with self.assertRaises(BootStop) as caught:
            b.read(PKDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,"missing_input")
        b.write(PKIOR_ADDRESS,2,0xFF00)
        self.assertEqual(b.read(PKDR_ADDRESS,2),0x00A5)

    def test_manual_reset_undefined_state(self):
        b=BootBus(image(),power_on=False)
        b.write(PKDR_ADDRESS,1,0xAB)
        with self.assertRaises(BootStop) as caught:
            b.read(PKDR_ADDRESS,1)
        self.assertEqual(caught.exception.kind,"unknown_peripheral_reset_state")
        b.write(PKIOR_ADDRESS,2,0xFFFF)
        self.assertEqual(b.read(PKDR_ADDRESS,1),0xAB)
        with self.assertRaises(BootStop) as caught:
            b.read(PKDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,"unknown_peripheral_reset_state")

    def test_access_size_alignment_and_pin_validation(self):
        b=BootBus(image())
        for fn in (lambda: b.read(PKDR_ADDRESS,4),
                   lambda: b.write(PKDR_ADDRESS,4,0)):
            with self.assertRaises(BootStop) as caught:
                fn()
            self.assertEqual(caught.exception.kind,"unsupported_access_size")
        with self.assertRaises(BootStop) as caught:
            b.read(PKDR_ADDRESS+1,2)
        self.assertEqual(caught.exception.kind,"unaligned_access")
        for value,mask in ((-1,0xFFFF),(0x10000,0xFFFF),(True,0xFFFF),
                           (0,0x10000),(0,True)):
            with self.subTest(value=value,mask=mask),self.assertRaises(ValueError):
                b.port_k.set_pins(value,mask)

    def test_observed_opcode_2151_word_store(self):
        # MOV.L @(disp,PC),R1; MOV #-1,R5; MOV.W R5,@R1
        data=bytearray(image(bytes.fromhex("D102 E5FF 2151 0009")).data)
        data[0x10C:0x110]=PKDR_ADDRESS.to_bytes(4,"big")
        d=NCBootDiagnostic(ROMImage("synthetic",bytes(data)))
        result=d.run(4)
        self.assertEqual(d.bus.port_k.data,0xFFFF)
        self.assertEqual(result["stop"]["reason"],"instruction_limit")
        self.assertTrue(any(x.get("register")=="PKDR" and x.get("access")=="write"
                            and x.get("width")==2 and x.get("value")==0xFFFF
                            for x in result["modelled_peripheral_accesses"]))
        self.assertFalse(result["boot_complete"])
