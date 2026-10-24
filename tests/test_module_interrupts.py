import unittest
from test_interrupts import irq_cpu
from ecu_workbench.core import ROMImage
from ecu_workbench.sh2_control import load_sr,read_sr
from ecu_workbench.atu import TSR,TIER,TIOR,TSTR,GR
from ecu_workbench.interrupts import IPRD_ADDRESS,IPRL_ADDRESS


def module_cpu(*words):
    d=irq_cpu(*(words or (0xE109,0x0009,0x0009)))
    data=bytearray(d.bus.image.data);data[0x180:0x184]=(0x500).to_bytes(4,'big')
    # ISR reads and clears TSR1A, increments R8, then RTE and its slot.
    for i,op in enumerate((0x6041,0xE000,0x2401,0x7801,0x002B,0x0009)):
        data[0x500+2*i:0x502+2*i]=op.to_bytes(2,'big')
    d.bus.image=ROMImage('synthetic',bytes(data));d.r[4]=TSR;d.r[8]=0
    d.bus.write(IPRD_ADDRESS,2,0x50)
    return d


def capture_request(d):
    t=d.bus.atu;t.write(TIOR,1,5);t.write(TIER,2,1);t.write(TSTR,1,2)
    t.advance_ticks(17);t.set_pin(False);t.set_pin(True)

class ModuleInterruptTests(unittest.TestCase):
    def test_atu_actual_capture_isr_acknowledge_return(self):
        d=module_cpu();sp=d.r[15];capture_request(d);r=d.run(8)
        self.assertEqual(d.r[8],1);self.assertEqual(d.r[1],9);self.assertEqual(d.r[15],sp)
        self.assertEqual(d.bus.atu.regs[GR],17);self.assertFalse(d.bus.atu.interrupt_pending)
        self.assertEqual(r['interrupt_entries'],1);self.assertEqual(d.exception_events[0]['vector'],96)
        self.assertEqual(d.exception_events[0]['source'],'IMI1A');self.assertEqual(read_sr(d),0)

    def test_priority_mask_enable_held_and_tie_arbitration(self):
        for priority,mask,expected in ((0,0,0),(5,5,0),(5,6,0),(7,6,1)):
            d=module_cpu();capture_request(d);d.bus.write(IPRD_ADDRESS,2,priority<<4);load_sr(d,mask<<4)
            d.run(1);self.assertEqual(d.interrupt_entries,expected)
        d=module_cpu();capture_request(d);d.bus.atu.write(TIER,2,0);d.run(1)
        self.assertEqual(d.interrupt_entries,0)
        d=module_cpu();capture_request(d);d.set_interval_request(True);d.run(1)
        self.assertEqual(d.exception_events[0]['source'],'IMI1A')
        self.assertTrue(d.bus.atu.interrupt_pending);self.assertTrue(d.interval_request)
        d=module_cpu();capture_request(d);d.bus.write(IPRL_ADDRESS,2,0x60);d.set_interval_request(True);d.run(1)
        self.assertEqual(d.exception_events[0]['source'],'ITI')

    def test_atu_slot_inhibition_unknown_and_unrouted_source(self):
        d=module_cpu(0xA002,0xE207);d.clock.schedule(1,lambda:capture_request(d));d.run(3)
        self.assertEqual(d.r[2],7);self.assertEqual(d.exception_events[0]['saved_pc'],'0x00000108')
        d=module_cpu(0x410E,0xE207,0x0009);load_sr(d,0xF0);d.r[1]=0;capture_request(d);d.run(3)
        self.assertEqual(d.r[2],7);self.assertEqual(d.exception_events[0]['saved_pc'],'0x00000104')
        d=module_cpu();d.bus.atu.regs[TSR]=None;d.bus.atu.write(TIER,2,1);sp=d.r[15]
        r=d.run(1);self.assertEqual(r['stop']['reason'],'unknown_peripheral_reset_state');self.assertEqual(d.r[15],sp)
        d=module_cpu();d.bus.atu.regs[TSR]=2;d.bus.atu.write(TIER,2,2)
        self.assertEqual(d.run(1)['stop']['reason'],'unsupported_interrupt_source')

    def test_atu_held_source_reenters_unless_firmware_acknowledges(self):
        d=module_cpu();capture_request(d)
        data=bytearray(d.bus.image.data);data[0x500:0x504]=bytes.fromhex('002B0009')
        d.bus.image=ROMImage('synthetic',bytes(data));d.run(3)
        self.assertEqual(d.interrupt_entries,2);self.assertTrue(d.bus.atu.interrupt_pending)
