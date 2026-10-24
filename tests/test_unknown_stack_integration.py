import unittest
from ecu_workbench.unknown_stack_fixture import run_unknown_stack_fixture
from ecu_workbench.known_bits import KnownBits
from ecu_workbench.nc_boot import BootStop,RAM_BASE
from test_sh2_branch import program

class UnknownStackIntegrationTests(unittest.TestCase):
    def test_generated_call_save_replace_restore_and_return(self):
        result=run_unknown_stack_fixture()
        self.assertTrue(result['fixture_passed'],result)
        self.assertEqual(result,run_unknown_stack_fixture())
        self.assertEqual(result['handler_count'],1)
        self.assertEqual(result['restored_registers']['R11']['known_mask'],0)
        self.assertFalse(result['manufacturer_firmware_used'])
        self.assertFalse(result['boot_complete'])

    def test_restored_unknown_cannot_select_address_pc_or_peripheral(self):
        for consumer in (0x61B2,0x4B2B,0x4B0E):
            # push R11; replace it; restore it; consume as address/PC/SR.
            d=program(0x2FB6,0xEB55,0x6BF6,consumer)
            sp=d.r[15];r=d.run(4)
            self.assertEqual(r['stop']['reason'],'unknown_register')
            self.assertEqual(d.r[15],sp)
            self.assertEqual(d.r[11],KnownBits(0,0))
            self.assertEqual(d.clock.ticks,3)
            self.assertEqual(d.bus.peripheral_trace,[])
        d=program(0x2FB6,0x6BF6,0x21B1);d.r[1]=0xFFFFD000
        r=d.run(3);self.assertEqual(r['stop']['reason'],'unknown_register')
        self.assertEqual(d.bus.hcan.commands,[1,1])

    def test_unknown_sign_extension_all_sign_states_and_overwrite_resolution(self):
        for width in (1,2):
            sign=1<<(8*width-1);low=(1<<(8*width))-1
            for known in (0,1):
                for value in (0,sign):
                    bits=KnownBits(value,low if known else low^sign)
                    result=bits.sign_extend(width)
                    upper=0xFFFFFFFF^low
                    self.assertEqual(result.mask&upper,upper if known else 0)
                    self.assertEqual(result.value&upper,upper if known and value else 0)
        d=program(0x2FB6,0x6BF6,0x2BBA);d.run(3)
        self.assertEqual(d.r[11],0)  # XOR R11,R11 proves zero without choosing old bits.
        b=d.bus;a=RAM_BASE+128
        b.write_cpu_value(a,4,KnownBits(0,0))
        for i in range(4):b.write(a+i,1,0x11*(i+1))
        self.assertEqual(b.read(a,4),0x11223344)
