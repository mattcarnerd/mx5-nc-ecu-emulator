"""B18: SH7058 port C PCDR read/write and reset contract."""
import unittest
import os
from pathlib import Path
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import (
    BootBus,BootStop,NCBootDiagnostic,ROM_LIMIT,PCDR_ADDRESS,
    PCIOR_ADDRESS,PC_VALID_MASK,diagnose_nc_reset)

def image(code=b'\x00\x09'):
    data=bytearray(ROM_LIMIT)
    for i,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        data[4*i:4*i+4]=v.to_bytes(4,'big')
    data[0x100:0x100+len(code)]=code
    return ROMImage('synthetic',bytes(data))

class PortCTests(unittest.TestCase):
    def test_reset_and_missing_pins(self):
        bus=BootBus(image())
        self.assertEqual(bus.pcdr,0)
        self.assertEqual(bus.pcdr_known_mask,0x1F)
        self.assertEqual(bus.read(PCDR_ADDRESS,1),0)
        with self.assertRaises(BootStop) as caught:bus.read(PCDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'missing_input')
        bus.write(PCDR_ADDRESS,2,0x1F)
        self.assertEqual(bus.pcdr,0x1F)
        self.assertEqual(bus.peripheral_trace[-1]['scope'],'output_latch_only')

    def test_word_and_byte_order(self):
        bus=BootBus(image())
        bus.write(PCIOR_ADDRESS,2,0x1F)
        bus.write(PCDR_ADDRESS,2,0x17)
        self.assertEqual(bus.read(PCDR_ADDRESS,2),0x17)
        self.assertEqual(bus.read(PCDR_ADDRESS,1),0)
        self.assertEqual(bus.read(PCDR_ADDRESS+1,1),0x17)
        bus.write(PCDR_ADDRESS,1,0)
        self.assertEqual(bus.read(PCDR_ADDRESS,2),0x17)
        bus.write(PCDR_ADDRESS+1,1,3)
        self.assertEqual(bus.read(PCDR_ADDRESS,2),3)

    def test_mixed_known_external_pins_and_outputs(self):
        bus=BootBus(image(),port_c_pin_values=5,port_c_pin_known_mask=5)
        bus.write(PCDR_ADDRESS,2,0x1A)
        bus.write(PCIOR_ADDRESS,2,0x1A)
        self.assertEqual(bus.read(PCDR_ADDRESS,2),0x1F)
        self.assertEqual(bus.peripheral_trace[-1]['physical_input_mask'],'0x0005')
        bus.set_port_c_pin_levels(1,1)
        with self.assertRaises(BootStop) as caught:bus.read(PCDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'missing_input')

    def test_reserved_bits_rejected_without_mutation(self):
        bus=BootBus(image())
        for addr,width,value in ((PCDR_ADDRESS,2,0x20),(PCDR_ADDRESS,1,1),(PCDR_ADDRESS+1,1,0xE0)):
            with self.subTest(addr=addr,value=value):
                with self.assertRaises(BootStop) as caught:bus.write(addr,width,value)
                self.assertEqual(caught.exception.kind,'invalid_peripheral_write')
                self.assertEqual(bus.pcdr,0)
        self.assertEqual(bus.read(PCDR_ADDRESS,1),0)

    def test_manual_reset_unknown_until_written(self):
        bus=BootBus(image(),power_on=False)
        self.assertEqual(bus.pcdr_known_mask,0)
        self.assertEqual(bus.read(PCDR_ADDRESS,1),0)
        bus.write(PCIOR_ADDRESS,2,0x1F)
        with self.assertRaises(BootStop) as caught:bus.read(PCDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'unknown_peripheral_reset_state')
        bus.write(PCDR_ADDRESS+1,1,0x1F)
        self.assertEqual(bus.read(PCDR_ADDRESS,2),0x1F)

    def test_unknown_manual_direction(self):
        bus=BootBus(image(),power_on=False)
        bus.write(PCDR_ADDRESS,2,0x15)
        with self.assertRaises(BootStop) as caught:bus.read(PCDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'unknown_peripheral_reset_state')
        bus.write(PCIOR_ADDRESS,2,0x1F)
        self.assertEqual(bus.read(PCDR_ADDRESS,2),0x15)

    def test_alt_function_follows_pcior_read_rule(self):
        bus=BootBus(image(),port_c_pin_values=0x1F)
        bus.write(PCIOR_ADDRESS,2,0x1F)
        bus.write(PCDR_ADDRESS,2,0x15)
        bus.write(0xFFFFF73C,2,0x40)
        self.assertEqual(bus.read(PCDR_ADDRESS,2),0x15)
        bus.write(PCIOR_ADDRESS,2,0)
        self.assertEqual(bus.read(PCDR_ADDRESS,2),0x1F)
        bus.set_port_c_pin_levels(None)
        with self.assertRaises(BootStop) as caught:bus.read(PCDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'missing_input')

    def test_invalid_access_width_and_physical_pin_values(self):
        bus=BootBus(image())
        for method in (lambda:bus.read(PCDR_ADDRESS,4),lambda:bus.write(PCDR_ADDRESS,4,0)):
            with self.assertRaises(BootStop) as caught:method()
            self.assertEqual(caught.exception.kind,'unsupported_access_size')
        with self.assertRaises(BootStop) as caught:bus.read(PCDR_ADDRESS+1,2)
        self.assertEqual(caught.exception.kind,'unaligned_access')
        for value,mask in ((0x20,0x1F),(-1,0x1F),(True,0x1F),(0,0x20)):
            with self.assertRaises(ValueError):bus.set_port_c_pin_levels(value,mask)

    def test_real_sh2_instruction_writes_latch(self):
        data=bytearray(image(bytes.fromhex('D102 E01F 2101 0009')).data)
        data[0x10C:0x110]=PCDR_ADDRESS.to_bytes(4,'big')
        cpu=NCBootDiagnostic(ROMImage('synthetic',bytes(data)))
        result=cpu.run(4)
        self.assertEqual(result['executed_instructions'],4)
        self.assertEqual(cpu.bus.pcdr,0x1F)
        self.assertEqual(cpu.bus.port_c_pin_known_mask,0)
        self.assertFalse(result['boot_complete'])

    def test_optional_original_lf9veb_regression(self):
        p=os.environ.get('MX5_NC_TEST_ROM')
        if not p:self.skipTest('Local original NC ROM optional; no OEM bytes in GitHub')
        rom=ROMImage('local',Path(p).read_bytes())
        if rom.sha256!='bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf':
            self.skipTest('Different original ROM')
        r=diagnose_nc_reset(rom,nmi_high=True,max_steps=300)
        self.assertGreater(r['executed_instructions'],67)
        self.assertTrue(any(x.get('register')=='PCDR' and x.get('access')=='write'
                            and x.get('value')==0x001F
                            for x in r['modelled_peripheral_accesses']))
        self.assertFalse(r['boot_complete'])
