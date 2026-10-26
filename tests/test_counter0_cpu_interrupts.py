import unittest
from test_interrupts import irq_cpu
from ecu_workbench.core import ROMImage
from ecu_workbench.atu import TSTR,ITVRR,TCNT0,TSR0,TIER0
from ecu_workbench.sh2_control import load_sr,read_sr

IPRC=0xFFFFED04
IPRD=0xFFFFED06

def counter_cpu(*words):
    c=irq_cpu(*(words or (0xAFFE,0x0009)))
    data=bytearray(c.bus.image.data)
    data[80*4:80*4+4]=(0x600).to_bytes(4,'big')
    data[92*4:92*4+4]=(0x700).to_bytes(4,'big')
    # Shared interval ISR clears all observed TSR0 flags, counts entry and RTE.
    for base,ops in ((0x600,(0x6041,0xE000,0x2401,0x7801,0x002B,0x0009)),
                     (0x700,(0x6041,0xE0E0,0x600C,0x2401,0x7901,0x002B,0x0009))):
        for i,op in enumerate(ops):data[base+2*i:base+2*i+2]=op.to_bytes(2,'big')
    c.bus.image=ROMImage('synthetic',bytes(data))
    c.r[4]=TSR0;c.r[8]=0;c.r[9]=0
    c.bus.write(IPRC,2,0x50);c.bus.write(IPRD,2,0x600)
    a=c.bus.atu;a.begin_counter0_clock_fixture(phase=0)
    a.write(ITVRR[0],1,1);a.write(TSTR,1,1)
    return c

class Counter0CpuInterruptTests(unittest.TestCase):
    def test_repeated_interval_isr_ack_return_and_stack_sr_restoration(self):
        c=counter_cpu();a=c.bus.atu;sp=c.r[15]
        for n,packet in enumerate((64,128,128),1):
            a.advance_phi_cycles(packet);r=c.run(c.executed+6)
            self.assertEqual(r['interrupt_entries'],n);self.assertEqual(c.r[8],n)
            self.assertEqual(c.pc,0x100);self.assertEqual(c.r[15],sp)
            self.assertEqual(read_sr(c),0);self.assertFalse(a.counter0.interval_pending)
            self.assertEqual(c.exception_events[-2]['vector'],80)
            self.assertEqual(c.exception_events[-2]['source'],'ATU0_interval')
        self.assertFalse(r['boot_complete'])

    def test_overflow_priority_then_shared_interval_group(self):
        c=counter_cpu();a=c.bus.atu;a.write(TSTR,1,0)
        for address in ITVRR:a.write(address,1,1)
        a.write(TIER0,2,0x10);a.write(TCNT0,4,0xFFFFFFF0);a.write(TSTR,1,1)
        a.advance_phi_cycles(1040);sp=c.r[15];c.run(7)
        self.assertEqual(c.exception_events[0]['vector'],92);self.assertEqual(c.r[9],1)
        self.assertFalse(a.counter0.overflow_pending);self.assertTrue(a.counter0.interval_pending)
        c.run(13);self.assertEqual(c.r[8],1);self.assertEqual(c.interrupt_entries,2)
        self.assertEqual(c.exception_events[2]['vector'],80);self.assertEqual(c.r[15],sp)
        self.assertFalse(a.counter0.interval_pending)

    def test_priority_mask_disable_held_and_delay_slot(self):
        for priority,mask,entries in ((0,0,0),(5,5,0),(5,6,0),(7,6,1)):
            c=counter_cpu();c.bus.write(IPRC,2,priority<<4);load_sr(c,mask<<4)
            c.bus.atu.advance_phi_cycles(64);c.run(1)
            self.assertEqual(c.interrupt_entries,entries)
        c=counter_cpu();a=c.bus.atu
        data=bytearray(c.bus.image.data);data[0x600:0x604]=bytes.fromhex('002B0009')
        c.bus.image=ROMImage('synthetic',bytes(data));a.advance_phi_cycles(64);c.run(3)
        self.assertEqual(c.interrupt_entries,2);self.assertTrue(a.counter0.interval_pending)
        c=counter_cpu();c.clock.schedule(1,lambda:c.bus.atu.advance_phi_cycles(64));c.run(3)
        self.assertEqual(c.trace[1]['pc'],'0x00000102');self.assertTrue(c.trace[1]['delay_slot'])
        self.assertEqual(c.exception_events[0]['saved_pc'],'0x00000100')
        c=counter_cpu();a=c.bus.atu;a.regs[TSR0]=0x10;a.write(TIER0,2,0)
        c.run(1);self.assertEqual(c.interrupt_entries,0)

    def test_unknown_priority_or_sr_never_fabricates_frame(self):
        for unknown in ('priority','sr'):
            c=counter_cpu();c.bus.atu.advance_phi_cycles(64);sp=c.r[15]
            if unknown=='priority':c.bus.ipr[IPRC]=None
            else:c.t=None
            r=c.run(1)
            self.assertIn(r['stop']['reason'],('unknown_peripheral_reset_state','unknown_status'))
            self.assertEqual(c.r[15],sp);self.assertEqual(c.interrupt_entries,0)
