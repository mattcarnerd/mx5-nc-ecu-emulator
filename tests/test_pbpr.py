"""SH7058 Rev 3.00 Section 22.3: explicit Port B input levels."""
import unittest
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, ROM_LIMIT, PBDR_ADDRESS, PBIOR_ADDRESS, PBPR_ADDRESS

def synthetic(code=b''):
    data=bytearray(ROM_LIMIT)
    for i,v in enumerate((0x100, 0xFFFFBFA0, 0x100, 0xFFFFBFA0)):
        data[4*i:4*i+4]=v.to_bytes(4,'big')
    data[0x100:0x100+len(code)]=code
    return ROMImage('synthetic.bin',bytes(data))

class ExplicitPinInputs(unittest.TestCase):
    def test_missing_inputs_fail_closed(self):
        bus=BootBus(synthetic())
        for a in (PBDR_ADDRESS,PBPR_ADDRESS):
            with self.subTest(address=a),self.assertRaises(BootStop) as err:
                bus.read(a,2)
            self.assertEqual(err.exception.kind,'missing_input')

    def test_pbpr_is_physical_not_output_latch(self):
        bus=BootBus(synthetic(),port_b_pin_values=0xA55A)
        bus.write(PBIOR_ADDRESS,2,0xFFFF)
        bus.write(PBDR_ADDRESS,2,0xCDEF)
        self.assertEqual(bus.read(PBDR_ADDRESS,2),0xCDEF)
        self.assertEqual(bus.read(PBPR_ADDRESS,2),0xA55A)
        self.assertEqual(bus.read(PBPR_ADDRESS,1),0xA5)
        self.assertEqual(bus.read(PBPR_ADDRESS+1,1),0x5A)

    def test_pbdr_mixes_pin_input_and_latch(self):
        bus=BootBus(synthetic(),port_b_pin_values=0x12A5)
        bus.write(PBIOR_ADDRESS,2,0xF0F0)
        bus.write(PBDR_ADDRESS,2,0x6B4C)
        expected=(0x6B4C & 0xF0F0)|(0x12A5 & 0x0F0F)
        self.assertEqual(bus.read(PBDR_ADDRESS,2),expected)
        self.assertEqual(bus.read(PBDR_ADDRESS,1),expected>>8)
        self.assertEqual(bus.peripheral_trace[-1]['physical_input_mask'],'0x0F00')

    def test_known_mask_and_updating_input(self):
        bus=BootBus(synthetic(),port_b_pin_values=0x00A5,port_b_pin_known_mask=0x00FF)
        bus.write(PBIOR_ADDRESS,2,0xFF00)
        bus.write(PBDR_ADDRESS,2,0xDEAD)
        self.assertEqual(bus.read(PBDR_ADDRESS,2),0xDEA5)
        self.assertEqual(bus.read(PBPR_ADDRESS+1,1),0xA5)
        with self.assertRaises(BootStop) as err:bus.read(PBPR_ADDRESS,2)
        self.assertEqual(err.exception.kind,'missing_input')
        bus.set_port_b_pin_levels(0xBEEF)
        self.assertEqual(bus.read(PBPR_ADDRESS,2),0xBEEF)
        bus.set_port_b_pin_levels(None)
        with self.assertRaises(BootStop):bus.read(PBPR_ADDRESS,1)

    def test_pbpr_is_read_only_and_width_checked(self):
        bus=BootBus(synthetic(),port_b_pin_values=0x1234)
        with self.assertRaises(BootStop) as err:bus.write(PBPR_ADDRESS,2,0xABCD)
        self.assertEqual(err.exception.kind,'read_only_peripheral')
        with self.assertRaises(BootStop) as err:bus.read(PBPR_ADDRESS,4)
        self.assertEqual(err.exception.kind,'unsupported_access_size')
        with self.assertRaises(BootStop) as err:bus.read(PBPR_ADDRESS+1,2)
        self.assertEqual(err.exception.kind,'unaligned_access')

    def test_invalid_explicit_levels(self):
        for kw in ({'port_b_pin_values':-1},{'port_b_pin_values':0x10000},
                   {'port_b_pin_values':True},{'port_b_pin_values':0,'port_b_pin_known_mask':0x10000},
                   {'port_b_pin_values':0,'port_b_pin_known_mask':'all'}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):
                BootBus(synthetic(),**kw)

    def test_actual_firmware_instruction_reads_pbpr(self):
        data=bytearray(synthetic(bytes.fromhex('D102 6011 0009')).data)
        data[0x10C:0x110]=PBPR_ADDRESS.to_bytes(4,'big')
        rom=ROMImage('synthetic.bin',bytes(data))
        self.assertEqual(NCBootDiagnostic(rom).run(2)['stop']['reason'],'missing_input')
        cpu=NCBootDiagnostic(rom,port_b_pin_values=0x9ABC)
        result=cpu.run(3)
        self.assertEqual(cpu.reg(0),0xFFFF9ABC)
        self.assertEqual(result['modelled_peripheral_accesses'][-1]['register'],'PBPR')
        self.assertFalse(result['boot_complete'])
