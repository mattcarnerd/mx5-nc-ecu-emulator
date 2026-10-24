import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import BootStop

class MailboxModeAuditTests(unittest.TestCase):
    def test_documented_instruction_sequence_independently_forms_2308(self):
        # Independent arithmetic expectation; generated documented opcodes, no OEM bytes.
        d=program(0xE503,0xE608,0x605C,0x4018,0x666C,0x306C,0x303C,0x81C2)
        d.r[3]=0x2000;d.r[12]=0xFFFFD100
        result=d.run(8)
        expected=0x2000+3*256+8
        self.assertEqual(d.r[0],expected)
        self.assertEqual(result['stop']['reason'],'invalid_peripheral_write')
        self.assertEqual(result['stop']['address'],'0xFFFFD104')
        self.assertEqual(result['stop']['value'],'0x00002308')
        self.assertEqual(d.clock.ticks,7)
        self.assertEqual(d.bus.hcan.mailbox_writes,{})

    def test_prohibited_modes_all_channels_and_mailboxes_are_atomic(self):
        b=program(0x0009).bus
        for base in (0xFFFFD100,0xFFFFD900):
            for mailbox in range(32):
                a=base+32*mailbox+4
                b.write(a,2,0x700)
                for value in (0x300,0x2308,0x600,0x2608):
                    with self.assertRaises(BootStop) as caught:b.write(a,2,value)
                    self.assertEqual(caught.exception.kind,'invalid_peripheral_write')
                    self.assertEqual(b.hcan.mailbox_writes[a],0x700)

    def test_identifier_field_decoding_is_command_evidence_only(self):
        b=program(0x0009).bus;b.write(0xFFFFD100,2,0x37)
        fields=b.peripheral_trace[-1]['identifier_fields']
        self.assertEqual(fields,{'standard_id':3,'rtr':False,'extended_format':True,'extended_id_high2':3})
        self.assertEqual(b.hcan.release_requests,[False,False])

    def test_private_literal_mode_and_fixture_variants(self):
        import os
        from ecu_workbench.core import ROMImage
        from ecu_workbench.nc_boot import NCBootDiagnostic
        from ecu_workbench.trace_review import LF9VEB_SHA256
        source=os.environ.get('MX5_NC_TEST_ROM')
        if not source:self.skipTest('Optional original-hash local regression')
        image=ROMImage.from_file(source)
        if image.sha256!=LF9VEB_SHA256:self.skipTest('Original hash required')
        for hudi in ('trst-reset','transfer-complete'):
            for delay in (64,256):
                d=NCBootDiagnostic(image,nmi_high=True,hudi_scenario=hudi,phi_cycles_per_instruction=1,
                    experimental_mcr_bit6=0,hcan_fixture={'reset_completion_ticks':1,'recessive_bus_ticks':delay})
                r=d.run(100000)
                self.assertEqual(r['executed_instructions'],1057)
                self.assertEqual(r['completed_instructions'],1056)
                self.assertEqual(r['next_dependency']['instruction_pc'],'0x00000E70')
                self.assertEqual(r['stop']['reason'],'invalid_peripheral_write')
                self.assertEqual(r['stop']['value'],'0x00002308')
                self.assertNotEqual(d.bus.hcan.mailbox_writes[0xFFFFD104],0x2308)
                self.assertEqual(r['interrupt_entries'],0)
