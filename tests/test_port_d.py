"""B29: SH7058 Port D PDDR and PDPR, manual Rev 3.00 Tables 22.7/22.8."""
import unittest
import os
from pathlib import Path
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, ROM_LIMIT, diagnose_nc_reset
from ecu_workbench.port_d import PortD, PDDR_ADDRESS, PDPR_ADDRESS, PDIOR_ADDRESS, PD_VALID_MASK

def image(code=b'\x00\x09'):
    data=bytearray(ROM_LIMIT)
    for idx,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):
        data[4*idx:4*idx+4]=v.to_bytes(4,'big')
    data[0x100:0x100+len(code)]=code
    return ROMImage('synthetic.bin',bytes(data))

class PortDTests(unittest.TestCase):
    def test_power_reset_and_missing_external_pins(self):
        bus=BootBus(image())
        self.assertEqual(bus.port_d.data,0)
        self.assertEqual(bus.port_d.data_known_mask,PD_VALID_MASK)
        self.assertEqual(bus.read(PDIOR_ADDRESS,2),0)
        with self.assertRaises(BootStop) as caught:
            bus.read(PDDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'missing_input')
        bus.write(PDDR_ADDRESS,2,0x3EFF)
        self.assertEqual(bus.port_d.data,0x3EFF)
        self.assertEqual(bus.peripheral_trace[-1]['scope'],'output_latch_only')
        self.assertEqual(bus.port_d.pin_known_mask,0)

    def test_big_endian_high_low_byte_write_and_read(self):
        bus=BootBus(image())
        bus.write(PDIOR_ADDRESS,2,0x3FFF)
        bus.write(PDDR_ADDRESS,2,0x0123)
        self.assertEqual(bus.read(PDDR_ADDRESS,2),0x0123)
        self.assertEqual(bus.read(PDDR_ADDRESS,1),0x01)
        self.assertEqual(bus.read(PDDR_ADDRESS+1,1),0x23)
        bus.write(PDDR_ADDRESS,1,0x3E)
        self.assertEqual(bus.read(PDDR_ADDRESS,2),0x3E23)
        bus.write(PDDR_ADDRESS+1,1,0xFD)
        self.assertEqual(bus.read(PDDR_ADDRESS,2),0x3EFD)

    def test_reservation_masks_and_atomic_invalid_writes(self):
        bus=BootBus(image())
        for address,width,val in ((PDDR_ADDRESS,2,0x4000),
                                  (PDDR_ADDRESS,1,0x80),
                                  (PDDR_ADDRESS,2,0xFFFF)):
            with self.subTest(address=address,width=width,val=val):
                with self.assertRaises(BootStop) as caught:
                    bus.write(address,width,val)
                self.assertEqual(caught.exception.kind,'invalid_peripheral_write')
                self.assertEqual(bus.port_d.data,0)
        bus.write(PDIOR_ADDRESS,2,0x3FFF)
        self.assertEqual(bus.read(PDDR_ADDRESS,1),0)

    def test_mixed_external_input_and_latch(self):
        bus=BootBus(image(),port_d_pin_values=0x0101,port_d_pin_known_mask=0x0101)
        bus.write(PDIOR_ADDRESS,2,0x3EFE)
        bus.write(PDDR_ADDRESS,2,0x0202)
        self.assertEqual(bus.read(PDDR_ADDRESS,2),0x0303)
        self.assertEqual(bus.peripheral_trace[-1]['physical_input_mask'],'0x0101')
        bus.port_d.set_pins(0x0001,0x0001)
        with self.assertRaises(BootStop) as caught:
            bus.read(PDDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'missing_input')

    def test_manual_reset_unknown_latch_and_direction(self):
        bus=BootBus(image(),power_on=False)
        self.assertEqual(bus.port_d.data_known_mask,0)
        bus.write(PDDR_ADDRESS,1,0x1F)
        self.assertEqual(bus.port_d.data_known_mask,0x3F00)
        with self.assertRaises(BootStop) as caught:
            bus.read(PDDR_ADDRESS,1)
        self.assertEqual(caught.exception.kind,'unknown_peripheral_reset_state')
        bus.write(PDIOR_ADDRESS,2,0x3FFF)
        self.assertEqual(bus.read(PDDR_ADDRESS,1),0x1F)
        with self.assertRaises(BootStop) as caught:
            bus.read(PDDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'unknown_peripheral_reset_state')
        bus.write(PDDR_ADDRESS+1,1,0x55)
        self.assertEqual(bus.read(PDDR_ADDRESS,2),0x1F55)

    def test_pdpr_physical_even_when_output_latch_is_different(self):
        bus=BootBus(image(),port_d_pin_values=0xABCD)
        bus.write(PDIOR_ADDRESS,2,0x3FFF)
        bus.write(PDDR_ADDRESS,2,0x3E00)
        self.assertEqual(bus.read(PDDR_ADDRESS,2),0x3E00)
        self.assertEqual(bus.read(PDPR_ADDRESS,2),0xABCD)
        self.assertEqual(bus.read(PDPR_ADDRESS,1),0xAB)
        self.assertEqual(bus.read(PDPR_ADDRESS+1,1),0xCD)
        with self.assertRaises(BootStop) as caught:
            bus.write(PDPR_ADDRESS,2,0x1234)
        self.assertEqual(caught.exception.kind,'read_only_peripheral')

    def test_pdpr_partial_known_bits_fail_closed(self):
        bus=BootBus(image(),port_d_pin_values=0x0011,port_d_pin_known_mask=0x00FF)
        self.assertEqual(bus.read(PDPR_ADDRESS+1,1),0x11)
        with self.assertRaises(BootStop) as caught:
            bus.read(PDPR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'missing_input')

    def test_alternate_timer_pin_config_does_not_invent_output(self):
        bus=BootBus(image(),port_d_pin_values=0x3FFF)
        bus.write(PDIOR_ADDRESS,2,0)
        bus.write(0xFFFFF742,2,0xFFFF) # PDCRH config latch only
        self.assertEqual(bus.read(PDDR_ADDRESS,2),0x3FFF)
        bus.port_d.set_pins(None)
        with self.assertRaises(BootStop) as caught:
            bus.read(PDDR_ADDRESS,2)
        self.assertEqual(caught.exception.kind,'missing_input')

    def test_width_alignment_pin_validation(self):
        bus=BootBus(image())
        for register in (PDDR_ADDRESS,PDPR_ADDRESS):
            with self.assertRaises(BootStop) as caught:
                bus.read(register,4)
            self.assertEqual(caught.exception.kind,'unsupported_access_size')
            with self.assertRaises(BootStop) as caught:
                bus.write(register,4,0)
            self.assertEqual(caught.exception.kind,'unsupported_access_size')
            with self.assertRaises(BootStop) as caught:
                bus.read(register+1,2)
            self.assertEqual(caught.exception.kind,'unaligned_access')
        for values,mask in ((-1,0xFFFF),(0x10000,0xFFFF),(True,0xFFFF),
                            (0,0x10000),(0,True)):
            with self.subTest(values=values,mask=mask),self.assertRaises(ValueError):
                bus.port_d.set_pins(values,mask)

    def test_cpu_executes_genuine_word_store_to_pddr(self):
        data=bytearray(image(bytes.fromhex('D102 E01F 2101 0009')).data)
        data[0x10C:0x110]=PDDR_ADDRESS.to_bytes(4,'big')
        diag=NCBootDiagnostic(ROMImage('synthetic',bytes(data)))
        result=diag.run(4)
        self.assertEqual(result['stop']['reason'],'instruction_limit')
        self.assertEqual(diag.bus.port_d.data,0x1F)
        self.assertEqual(result['modelled_peripheral_accesses'][-1]['register'],'PDDR')
        self.assertFalse(result['boot_complete'])

    def test_optional_original_lf9veb_after_port_d(self):
        source=os.environ.get('MX5_NC_TEST_ROM')
        if not source:
            self.skipTest('Private ROM supplied locally; no OEM firmware in GitHub')
        rom=ROMImage('original',Path(source).read_bytes())
        if rom.sha256!='bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf':
            self.skipTest('Test ROM is not the original LF9VEB')
        result=diagnose_nc_reset(rom,nmi_high=True,max_steps=300)
        self.assertEqual(result['executed_instructions'],76)
        self.assertEqual(result['next_dependency']['instruction_pc'],'0x00000CAE')
        self.assertEqual(result['next_dependency']['opcode'],'2151')
        self.assertEqual(result['next_dependency']['memory_access']['address'],'0xFFFFF754')
        self.assertEqual(result['next_dependency']['memory_access']['value'],'0x0000FFFF')
        self.assertFalse(result['boot_complete'])
