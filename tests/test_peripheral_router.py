"""B17: GPIO routing must not change emulated peripheral semantics."""
import unittest

from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, ROM_LIMIT, PBDR_ADDRESS, PBPR_ADDRESS, PCDR_ADDRESS
from ecu_workbench.port_d import PDDR_ADDRESS, PDPR_ADDRESS, PDIOR_ADDRESS
from ecu_workbench.port_e import PEDR_ADDRESS, PEIOR_ADDRESS
from ecu_workbench.port_f import PFDR_ADDRESS, PFIOR_ADDRESS
from ecu_workbench.port_g import PGDR_ADDRESS, PGIOR_ADDRESS
from ecu_workbench.port_h import PHDR_ADDRESS, PHIOR_ADDRESS
from ecu_workbench.port_j import PJDR_ADDRESS, PJIOR_ADDRESS
from ecu_workbench.peripheral_router import PeripheralRouter


def image():
    return ROMImage("synthetic", bytes(ROM_LIMIT))


class RouterTests(unittest.TestCase):
    def test_reject_duplicate_and_misaligned_routes(self):
        router=PeripheralRouter()
        reader=lambda a,w: 0x33
        writer=lambda a,w,v: None
        router.add_word(name="TEST",base=0x100,read=reader,write=writer)
        for base in (0x100,0x101):
            with self.subTest(base=base), self.assertRaises(ValueError):
                router.add_word(name="OVERLAP",base=base,read=reader,write=writer)
        self.assertIs(router.read(0x102,1),PeripheralRouter.UNHANDLED)
        self.assertIs(router.write(0x102,1,0),PeripheralRouter.UNHANDLED)
        self.assertEqual(router.read(0x101,1),0x33)

    def test_all_data_registers_use_registry(self):
        b=BootBus(image())
        expected={"PBDR":PBDR_ADDRESS,"PBPR":PBPR_ADDRESS,
                  "PCDR":PCDR_ADDRESS,"PDDR":PDDR_ADDRESS,
                  "PDPR":PDPR_ADDRESS,"PEDR":PEDR_ADDRESS,"PFDR":PFDR_ADDRESS,
                  "PGDR":PGDR_ADDRESS,"PHDR":PHDR_ADDRESS,
                  "PJDR":PJDR_ADDRESS}
        self.assertEqual(set(r.name for r in b.port_router._by_base.values()),
                         set(expected))
        for name,base in expected.items():
            self.assertEqual(b.port_router._by_base[base].name,name)
            self.assertIs(b.port_router._by_byte[base],
                          b.port_router._by_byte[base+1])

    def test_access_modes_and_big_endian_latches(self):
        b=BootBus(image())
        directions={0xFFFFF730:0xFFFF,0xFFFFF73A:0x001F,
                    PDIOR_ADDRESS:0x3FFF,PEIOR_ADDRESS:0xFFFF,
                    PFIOR_ADDRESS:0xFFFF,PGIOR_ADDRESS:0x000F,
                    PHIOR_ADDRESS:0xFFFF,PJIOR_ADDRESS:0xFFFF}
        for addr,mode in directions.items():
            b.write(addr,2,mode)
        for addr,value in ((PBDR_ADDRESS,0xD00D),(PCDR_ADDRESS,0x001B),
                           (PDDR_ADDRESS,0x1234),(PEDR_ADDRESS,0xBEEF),
                           (PFDR_ADDRESS,0xCAFE),(PGDR_ADDRESS,0x000A),
                           (PHDR_ADDRESS,0xDADA),(PJDR_ADDRESS,0xBABE)):
            with self.subTest(addr=hex(addr)):
                b.write(addr,2,value)
                self.assertEqual(b.read(addr,2),value)
                self.assertEqual(b.read(addr,1),value >> 8)
                self.assertEqual(b.read(addr+1,1),value & 0xFF)
                b.write(addr+1,1,0x05)
                self.assertEqual(b.read(addr,2),(value & 0xFF00)|0x05)
        self.assertEqual(b.peripheral_trace[-1]["register"],"PJDR")

    def test_32_bit_access_stops_before_unaligned_memory_check(self):
        b=BootBus(image())
        for address in (PBDR_ADDRESS,PBPR_ADDRESS,PCDR_ADDRESS,
                        PDDR_ADDRESS,PDPR_ADDRESS,PEDR_ADDRESS,PFDR_ADDRESS,PGDR_ADDRESS,PHDR_ADDRESS,PJDR_ADDRESS):
            for mode in ("read","write"):
                with self.subTest(address=hex(address),mode=mode):
                    with self.assertRaises(BootStop) as caught:
                        if mode == "read":
                            b.read(address,4)
                        else:
                            b.write(address,4,0)
                    self.assertEqual(caught.exception.kind,"unsupported_access_size")

    def test_unknown_addresses_and_input_levels_never_invented(self):
        b=BootBus(image())
        for addr in (0xFFFFF786,0xFFFFF75E):
            for mode in ("read","write"):
                with self.subTest(addr=hex(addr),mode=mode):
                    with self.assertRaises(BootStop) as caught:
                        b.read(addr,2) if mode=="read" else b.write(addr,2,0)
                    self.assertEqual(caught.exception.kind,"unmodelled_peripheral")
        for addr in (PBDR_ADDRESS,PBPR_ADDRESS,PCDR_ADDRESS,
                     PDDR_ADDRESS,PDPR_ADDRESS,PEDR_ADDRESS,PFDR_ADDRESS,PGDR_ADDRESS,PHDR_ADDRESS,PJDR_ADDRESS):
            with self.subTest(addr=hex(addr)),self.assertRaises(BootStop) as caught:
                b.read(addr,2)
            self.assertEqual(caught.exception.kind,"missing_input")

    def test_invalid_reserved_bits_and_read_only_are_unchanged(self):
        b=BootBus(image())
        for addr,value in ((PCDR_ADDRESS,0x0020),(PDDR_ADDRESS,0x4000)):
            with self.subTest(addr=hex(addr)),self.assertRaises(BootStop) as caught:
                b.write(addr,2,value)
            self.assertEqual(caught.exception.kind,"invalid_peripheral_write")
        for addr in (PBPR_ADDRESS,PDPR_ADDRESS):
            with self.subTest(addr=hex(addr)),self.assertRaises(BootStop) as caught:
                b.write(addr,2,0)
            self.assertEqual(caught.exception.kind,"read_only_peripheral")

    def test_manual_reset_direction_unknown_remains_explicit(self):
        b=BootBus(image(),power_on=False)
        b.write(PEDR_ADDRESS,2,0xFFFF)
        with self.assertRaises(BootStop) as caught:
            b.read(PEDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,"unknown_peripheral_reset_state")
