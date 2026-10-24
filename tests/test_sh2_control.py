import unittest
from test_sh2_compare import cpu
from ecu_workbench.nc_boot import BootStop
from ecu_workbench.core import ROMImage
from ecu_workbench.sh2_control import load_sr, read_sr


def set_op(d,op):
    data=bytearray(d.bus.image.data); data[0x100:0x102]=op.to_bytes(2,'big')
    d.bus.image=ROMImage('synthetic',bytes(data)); d.pc=0x100

class ControlTests(unittest.TestCase):
    def test_observed_4f22_saves_pr_big_endian(self):
        d=cpu(0x4F22); d.pr=0x12345678; sp=d.reg(15); d.execute()
        self.assertEqual(d.reg(15),sp-4)
        self.assertEqual(d.bus.read(sp-4,4),0x12345678)
        self.assertEqual(d.bus.read(sp-4,1),0x12)

    def test_register_forms_and_reserved_sr_bits(self):
        for load,store,name in ((0x410E,0x0202,'sr'),(0x411E,0x0212,'gbr'),
                                 (0x412E,0x0222,'vbr'),(0x412A,0x022A,'pr')):
            d=cpu(load); d.r[1]=0xFFFFFFFF; d.execute(); set_op(d,store); d.execute()
            self.assertEqual(d.r[2],0x3F3 if name=='sr' else 0xFFFFFFFF)
        self.assertIsNone(d.t)

    def test_memory_forms_round_trip(self):
        for store,load,name in ((0x4103,0x4207,'sr'),(0x4113,0x4217,'gbr'),
                                 (0x4123,0x4227,'vbr'),(0x4122,0x4226,'pr')):
            d=cpu(store); d.r[1]=0xFFFF0104; d.r[2]=0xFFFF0100
            if name=='sr': load_sr(d,0x301)
            else: setattr(d,name,0x12345678)
            d.execute(); self.assertEqual(d.r[1],0xFFFF0100)
            set_op(d,load); d.execute()
            self.assertEqual(d.r[2],0xFFFF0104)
            self.assertEqual(read_sr(d) if name=='sr' else getattr(d,name),
                             0x301 if name=='sr' else 0x12345678)

    def test_unknown_sources_are_not_saved(self):
        for op in (0x4F22,0x4F13,0x4F03):
            d=cpu(op); sp=d.reg(15)
            with self.assertRaises(BootStop): d.execute()
            self.assertEqual(d.reg(15),sp); self.assertFalse(any(d.bus.ram_valid))

    def test_status_read_tracks_t_and_reset_unknowns(self):
        d=cpu(0x0102)
        with self.assertRaises(BootStop) as c: d.execute()
        self.assertEqual(c.exception.kind,'unknown_status')
        load_sr(d,0x3F3); d.t=False
        self.assertEqual(read_sr(d),0x3F2)
        r=d.run(1)
        self.assertEqual(r['sr_known_bits'],{'mask':'0x000003F3','value':'0x000003F2'})

    def test_fault_mutation_order(self):
        d=cpu(0x4122); d.pr=5; d.r[1]=0xFFFF0002
        with self.assertRaises(BootStop): d.execute()
        self.assertEqual(d.r[1],0xFFFEFFFE)
        d=cpu(0x4126); d.r[1]=0xFFFF0100; d.pr=7
        with self.assertRaises(BootStop): d.execute()
        self.assertEqual((d.r[1],d.pr),(0xFFFF0100,7))

    def test_clrt_sett(self):
        for op,t in ((0x0008,False),(0x0018,True)):
            d=cpu(op); d.execute(); self.assertIs(d.t,t)

    def test_optional_original_reference_passes_4f22(self):
        import hashlib,os
        from pathlib import Path
        from ecu_workbench.trace_review import LF9VEB_SHA256
        from ecu_workbench.nc_boot import diagnose_nc_reset
        path=os.environ.get('MX5_NC_TEST_ROM')
        if not path: self.skipTest('Private reference ROM unavailable')
        data=Path(path).read_bytes()
        if hashlib.sha256(data).hexdigest()!=LF9VEB_SHA256: self.skipTest('Not original reference hash')
        r=diagnose_nc_reset(ROMImage('private',data),max_steps=300,nmi_high=True)
        self.assertGreater(r['executed_instructions'],154)
        self.assertFalse(r['boot_complete'])
