import sys, pathlib, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import BootBus, BootStop, NCBootDiagnostic, diagnose_nc_reset, RAM_BASE, ROM_LIMIT

def fake_rom(code:bytes, power_pc=0x100, power_sp=0xFFFFBFA0, manual_pc=0x180, manual_sp=0xFFFFBF00):
    b=bytearray(ROM_LIMIT)
    for idx,v in enumerate((power_pc,power_sp,manual_pc,manual_sp)):
        b[4*idx:4*(idx+1)]=v.to_bytes(4,'big')
    b[0x100:0x100+len(code)]=code
    return ROMImage('synthetic.bin',bytes(b))

class TestHardware(unittest.TestCase):
    def test_reset_vectors_and_sr_known_bits(self):
        diag=NCBootDiagnostic(fake_rom(bytes.fromhex('0009')))
        self.assertEqual(diag.pc,0x100)
        self.assertEqual(diag.r[15],0xFFFFBFA0)
        self.assertIsNone(diag.r[0]);self.assertEqual(diag.known_sr_value,0xF0)
        other=NCBootDiagnostic(fake_rom(bytes.fromhex('0009')),reset='manual')
        self.assertEqual(other.pc,0x180);self.assertEqual(other.r[15],0xFFFFBF00)
    def test_invalid_pc_or_sp_fails_closed(self):
        a=diagnose_nc_reset(fake_rom(b'\x00\x09',power_pc=0x200001))
        self.assertEqual(a['stop']['reason'],'invalid_reset_vector')
        a=diagnose_nc_reset(fake_rom(b'\x00\x09',power_sp=0xFFFFC000))
        self.assertEqual(a['stop']['reason'],'invalid_reset_vector')
    def test_short_image_fails_closed(self):
        self.assertEqual(diagnose_nc_reset(ROMImage('partial',b'AB'))['stop']['reason'],'unsupported_image_size')
    def test_ram_initial_unknown_and_write_then_read(self):
        b=BootBus(fake_rom(b'\x00\x09'))
        with self.assertRaises(BootStop) as err:b.read(RAM_BASE+4,2)
        self.assertEqual(err.exception.kind,'uninitialised_ram')
        b.write(RAM_BASE+4,2,0x1234)
        self.assertEqual(b.read(RAM_BASE+4,2),0x1234)
    def test_unmodelled_peripheral_not_fake_register(self):
        b=BootBus(fake_rom(b'\x00\x09'))
        with self.assertRaises(BootStop) as err:b.write(0xFFFFEC30,2,15)
        self.assertEqual(err.exception.kind,'unmodelled_peripheral')
        self.assertEqual(err.exception.value,15)
    def test_bsc_poweron_defaults_and_write(self):
        b=BootBus(fake_rom(b'\x00\x09'))
        self.assertEqual([b.read(a,2) for a in (0xFFFFEC20,0xFFFFEC22,0xFFFFEC24,0xFFFFEC26)],[0x000F,0xFFFF,0x7777,0])
        b.write(0xFFFFEC20,2,0xA)
        self.assertEqual(b.read(0xFFFFEC20,2),10)
    def test_manual_reset_peripheral_not_invented(self):
        b=BootBus(fake_rom(b'\x00\x09'),power_on=False)
        with self.assertRaises(BootStop) as err:b.read(0xFFFFEC20,2)
        self.assertEqual(err.exception.kind,'unknown_peripheral_reset_state')
    def test_rom_writes_disallowed(self):
        b=BootBus(fake_rom(b'\x00\x09'))
        with self.assertRaises(BootStop) as err:b.write(0x100,2,123)
        self.assertEqual(err.exception.kind,'rom_write')
    def test_bsr_delay_slot_and_rts(self):
        # BSR 0x108, NOP, MOV #1,R0, NOP, MOV #4,R2, RTS, NOP
        b=bytearray(ROM_LIMIT)
        b[0:4]=(0x100).to_bytes(4,'big');b[4:8]=(0xFFFFBFA0).to_bytes(4,'big')
        b[8:12]=(0x100).to_bytes(4,'big');b[12:16]=(0xFFFFBFA0).to_bytes(4,'big')
        b[0x100:0x110]=bytes.fromhex('B002 0009 E001 0009 E204 000B 0009 0009')
        r=NCBootDiagnostic(ROMImage('synthetic.bin',bytes(b))).run(6)
        self.assertEqual(r['executed_instructions'],6)
        self.assertEqual(r['pr_at_stop'],'0x00000104')
        self.assertEqual(r['pc_at_stop'],'0x00000106')
    def test_access_bsc_with_executed_rom(self):
        # BSR +8 -> 0x114, delay-slot NOP; first MOV.W literal 0xEC20
        b=bytearray(ROM_LIMIT)
        for index,value in enumerate([0x100,0xFFFFBFA0,0x100,0xFFFFBFA0]):
            b[index*4:index*4+4]=value.to_bytes(4,'big')
        b[0x100:0x104]=bytes.fromhex('B008 0009')
        b[0x114:0x11A]=bytes.fromhex('9204 E30F 2231')
        # 0x114+4+4*2 = 0x120; 0xEC20 -> FFFFEC20
        b[0x120:0x122]=bytes.fromhex('EC20')
        r=NCBootDiagnostic(ROMImage('synthetic.bin',bytes(b))).run(15)
        self.assertEqual(r['modelled_peripheral_accesses'][0]['register'],'BCR1')
        self.assertEqual(r['modelled_peripheral_accesses'][0]['value'],15)
        self.assertGreaterEqual(r['executed_instructions'],5)

if __name__=='__main__':unittest.main()

class TestResetHardwareExtensions(unittest.TestCase):
    def test_clock_key_enforced(self):
        bus=BootBus(fake_rom(b'\x00\x09'))
        with self.assertRaises(BootStop) as err:
            bus.write(0xFFFFF70A,2,0x1234)
        self.assertEqual(err.exception.kind,'invalid_peripheral_write')
        bus.write(0xFFFFF70A,2,0x3C04)
        self.assertEqual(bus.read(0xFFFFF70B,1),4)

    def test_nmi_read_is_unknown_by_default(self):
        bus=BootBus(fake_rom(b'\x00\x09'))
        bus.write(0xFFFFED18,2,0)
        with self.assertRaises(BootStop) as err:
            bus.read(0xFFFFED18,2)
        self.assertEqual(err.exception.kind,'missing_input')

    def test_explicit_nmi_pin_state(self):
        for high in (True,False):
            bus=BootBus(fake_rom(b'\x00\x09'),nmi_high=high)
            bus.write(0xFFFFED18,2,0)
            self.assertEqual(bus.read(0xFFFFED18,2),0x8000 if high else 0x0000)

    def test_port_latches_no_pin_assumptions(self):
        bus=BootBus(fake_rom(b'\x00\x09'))
        self.assertEqual(bus.read(0xFFFFF720,2),0)
        bus.write(0xFFFFF726,2,0xFFFF)
        self.assertEqual(bus.padr,0xFFFF)
        with self.assertRaises(BootStop) as err:
            bus.read(0xFFFFF726,2)
        self.assertEqual(err.exception.kind,'missing_input')
        bus.write(0xFFFFF720,2,0xFFFF)
        self.assertEqual(bus.read(0xFFFFF726,2),0xFFFF)

    def test_byte_store_and_extu_supported(self):
        # MOV #0x12,R3 ; MOV.L @(disp,PC),R1 ; MOV.B R3,@R1 ; EXTU.W R3,R3
        b=bytearray(ROM_LIMIT)
        for index,value in enumerate([0x100,0xFFFFBFA0,0x100,0xFFFFBFA0]):
            b[index*4:index*4+4]=value.to_bytes(4,'big')
        b[0x100:0x108]=bytes.fromhex('E312 D102 2130 633D')
        b[0x10C:0x110]=(0xFFFF0004).to_bytes(4,'big')
        diag=NCBootDiagnostic(ROMImage('synthetic.bin',bytes(b)))
        result=diag.run(4)
        self.assertEqual(result['stop']['reason'],'instruction_limit')
        self.assertEqual(diag.bus.read(0xFFFF0004,1),0x12)
        self.assertEqual(diag.reg(3),0x12)

    def test_different_roms_same_reset_code(self):
        a=fake_rom(bytes.fromhex('E001 7001 0009'))
        b=ROMImage('different.bin',a.data[:-1]+b'\xaa')
        ra=diagnose_nc_reset(a,max_steps=3)
        rb=diagnose_nc_reset(b,max_steps=3)
        self.assertEqual(ra['pc_at_stop'],rb['pc_at_stop'])
        self.assertNotEqual(ra['rom_sha256'],rb['rom_sha256'])
        self.assertEqual(ra['executed_instructions'],3)

    def test_optional_rom_execution_no_embedded_rom(self):
        import os
        rom_path=os.environ.get('MX5_NC_TEST_ROM')
        if not rom_path:
            self.skipTest('Set MX5_NC_TEST_ROM to a locally held NC ROM for integration test')
        data=pathlib.Path(rom_path).read_bytes()
        result=diagnose_nc_reset(ROMImage('supplied_rom',data),max_steps=300,nmi_high=True)
        self.assertGreater(result.get('executed_instructions',0),0)
        self.assertFalse(result['boot_complete'])
