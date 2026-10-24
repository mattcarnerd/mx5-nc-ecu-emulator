import unittest,os,hashlib,json
from pathlib import Path
from ecu_workbench.core import ROMImage
from ecu_workbench.nc_boot import NCBootDiagnostic
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits
from ecu_workbench.nc_boot import BootStop

class PartialCpuTests(unittest.TestCase):
    def test_mcr_word_load_preserves_unknown_bit_and_sign_extension(self):
        for address in (0xFFFFD000,0xFFFFD800):
            d=program(0x6031);d.r[3]=address;d.bus.write(address,2,0)
            d.run(1)
            self.assertEqual(d.r[0],KnownBits(0,0xFFFFFFBF))
            self.assertEqual(d.clock.ticks,1)
            with self.assertRaises(BootStop):d.reg(0)
            with self.assertRaises(BootStop):d.bus.read(address,2)
            self.assertEqual(d.bus.peripheral_trace[-1]['unknown_mask'],0x40)

    def test_partial_consumers_fail_and_replacement_clears_unknown(self):
        d=program(0x6031,0x7001);d.r[3]=0xFFFFD000
        result=d.run(2)
        self.assertEqual(result['stop']['reason'],'unknown_register')
        self.assertEqual(d.clock.ticks,1)
        self.assertEqual(d.r[0],KnownBits(1,0xFFFFFFBF))
        d=program(0x6031,0xE005);d.r[3]=0xFFFFD000;d.run(2)
        self.assertEqual(d.r[0],5)

    def test_known_memory_and_manual_reset_still_fail_closed(self):
        d=program(0x6031);d.r[3]=0x100;d.run(1)
        self.assertEqual(d.r[0],0x6031)
        d=program(0x6031);d.bus.hcan.commands=[None,None];d.r[3]=0xFFFFD000
        result=d.run(1)
        self.assertEqual(result['stop']['reason'],'unknown_peripheral_reset_state')
        self.assertEqual(d.clock.ticks,0)

    def test_or_and_masking_and_copy_preserve_flags(self):
        d=program(0xCB01,0x6103,0xC9BF);d.r[0]=KnownBits(0,0xFFFFFFBF);d.t=True
        d.run(3)
        self.assertEqual(d.r[1],KnownBits(1,0xFFFFFFBF))
        self.assertEqual(d.r[0],1);self.assertTrue(d.t)

    def test_register_logic_aliasing_and_unrelated_unknowns(self):
        for op,expected in ((0x2019,KnownBits(0,0xFFFFFFFE)),
                            (0x201B,KnownBits(1,0xFFFFFFBF)),
                            (0x201A,KnownBits(1,0xFFFFFFBE))):
            d=program(op);d.r[0]=KnownBits(1,0xFFFFFFBF);d.r[1]=KnownBits(0,0xFFFFFFFE)
            d.run(1);self.assertEqual(d.r[0],expected)
        d=program(0x200A);d.r[0]=KnownBits(0,0);d.run(1)
        self.assertEqual(d.r[0],0)

    def test_tst_proof_and_unknown_branch(self):
        for mask,t in ((0x40,None),(1,True)):
            d=program(0xC800|mask,0x8900);d.r[0]=KnownBits(0,0xFFFFFFBF)
            result=d.run(2);self.assertIs(d.t,t)
            self.assertEqual(result['stop']['reason'],'unknown_status' if t is None else 'instruction_limit')
        d=program(0xC801);d.r[0]=KnownBits(1,1);d.run(1);self.assertFalse(d.t)
        d=program(0xCB01);d.r[0]=None
        result=d.run(1);self.assertEqual(result['stop']['reason'],'unknown_register')

    def test_stores_require_only_written_bits_known(self):
        for op,width,value,mask in ((0x2100,1,0xAB,0xFF),(0x2101,2,0xABCD,0xFFFF),
                                   (0x2102,4,0xABCDEF12,0xFFFFFFFF)):
            d=program(op);d.r[1]=0xFFFF0000;d.r[0]=KnownBits(value,mask)
            result=d.run(1)
            self.assertEqual(result['stop']['reason'],'instruction_limit')
            self.assertEqual(d.bus.read(0xFFFF0000,width),value)
            d=program(op);d.r[1]=0xFFFF0000;d.r[0]=KnownBits(value,mask & ~0x80)
            result=d.run(1)
            self.assertEqual(result['stop']['reason'],'unknown_register')
            self.assertEqual(result['stop']['address'],'0xFFFF0000')
            self.assertEqual(result['stop']['width'],width)
            self.assertNotIn('value',result['stop'])
            self.assertEqual(d.clock.ticks,0)
            self.assertEqual(d.coverage.bus_failure_count,1)
            with self.assertRaises(BootStop):d.bus.read(0xFFFF0000,width)

    def test_mcr_rmw_unknown_reserved_bit_is_not_silently_zeroed(self):
        d=program(0x6031,0xCB01,0x2301);d.r[3]=0xFFFFD000
        d.bus.write(0xFFFFD000,2,0)
        result=d.run(3)
        self.assertEqual(result['stop']['reason'],'unknown_register')
        self.assertEqual(result['stop']['address'],'0xFFFFD000')
        self.assertIn('0x00000040',result['stop']['detail'])
        self.assertEqual(d.bus.hcan.commands,[0,1])
        self.assertEqual(d.clock.ticks,2)
        self.assertEqual(len([e for e in d.bus.peripheral_trace if e['access']=='write']),1)
        self.assertEqual(result['next_dependency']['memory_access']['access'],'write')

    def test_firmware_explicit_mask_resolves_reserved_bit(self):
        d=program(0x6031,0xC9BF,0x2301);d.r[3]=0xFFFFD000
        d.bus.write(0xFFFFD000,2,0);result=d.run(3)
        self.assertEqual(result['stop']['reason'],'instruction_limit')
        self.assertEqual(d.r[0],0);self.assertEqual(d.clock.ticks,3)
        self.assertEqual(len([e for e in d.bus.peripheral_trace if e['access']=='write']),2)

    @unittest.skipUnless(os.environ.get('MX5_NC_TEST_ROM'),'Private ROM supplied locally only')
    def test_private_conditional_reserved_write_regression(self):
        data=Path(os.environ['MX5_NC_TEST_ROM']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),'bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf')
        for scenario in ('trst-reset','transfer-complete'):
            d=NCBootDiagnostic(ROMImage('private',data),nmi_high=True,
                hudi_scenario=scenario,phi_cycles_per_instruction=1)
            result=d.run(10000)
            self.assertEqual(result['executed_instructions'],592)
            self.assertEqual(result['completed_instructions'],591)
            self.assertEqual(result['stop']['reason'],'unknown_register')
            self.assertEqual(result['stop']['address'],'0xFFFFD000')
            self.assertEqual(result['next_dependency']['instruction_pc'],'0x000007B6')
            self.assertEqual(d.r[0],KnownBits(1,0xFFFFFFBF))
            self.assertEqual(d.bus.hcan.commands[0],0)
            self.assertFalse(result['boot_complete']);json.dumps(result)
