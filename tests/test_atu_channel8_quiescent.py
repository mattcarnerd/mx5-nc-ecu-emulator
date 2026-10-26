import unittest
from ecu_workbench.atu import Atu1A,TCNR,OTR,TRGMDR,DSTR
from ecu_workbench.nc_boot import BootStop

class Channel8QuiescentConfigurationTests(unittest.TestCase):
    def test_connections_do_not_start_zero_downcounters(self):
        a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
        a.write(TCNR,2,0xFFEF);a.write(OTR,2,0xFFFF);a.write(TRGMDR,1,0x80)
        self.assertEqual(a.read(TCNR,2),0xFFEF)
        self.assertEqual(a.read(OTR,2),0xFFFF)
        self.assertEqual(a.regs[DSTR],0);self.assertEqual(a.channel8_counters,[0]*16)
        self.assertEqual(a.events,[])

    def test_unknown_running_nonzero_or_available_reload_guard(self):
        for mutation in ('unknown','counter','running','reload'):
            a=Atu1A(power_on=True,trace=[],stop_type=BootStop)
            if mutation=='unknown':a.channel8_counters[0]=None
            if mutation=='counter':a.channel8_counters[0]=1
            if mutation=='running':a.regs[DSTR]=1
            if mutation=='reload':a.channel8_reload_enabled=True;a.channel8_reload_value=1
            before=dict(a.regs)
            for address,width,value in ((TCNR,2,0xFFEF),(OTR,2,0xFFFF),(TRGMDR,1,0x80)):
                with self.assertRaises(BootStop):a.write(address,width,value)
            self.assertEqual(a.regs,before)
        m=Atu1A(power_on=False,trace=[],stop_type=BootStop)
        with self.assertRaises(BootStop):m.write(TCNR,2,0xFFEF)
