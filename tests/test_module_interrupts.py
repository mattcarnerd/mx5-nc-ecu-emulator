import unittest
from test_interrupts import irq_cpu
from ecu_workbench.core import ROMImage
from ecu_workbench.sh2_control import load_sr,read_sr
from ecu_workbench.atu import TSR,TIER,TIOR,TSTR,GR
from ecu_workbench.interrupts import IPRD_ADDRESS,IPRL_ADDRESS,IPRJ_ADDRESS
from ecu_workbench.adc import ADCSR0,ADCR0,ADDR0
from ecu_workbench.nc_boot import NCBootDiagnostic
from test_sensor_fixture import sensor_rom
from ecu_workbench.sensor_fixture import adc_fields


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

    def test_atu_slot_inhibition_and_unknown(self):
        d=module_cpu(0xA002,0xE207);d.clock.schedule(1,lambda:capture_request(d));d.run(3)
        self.assertEqual(d.r[2],7);self.assertEqual(d.exception_events[0]['saved_pc'],'0x00000108')
        d=module_cpu(0x410E,0xE207,0x0009);load_sr(d,0xF0);d.r[1]=0;capture_request(d);d.run(3)
        self.assertEqual(d.r[2],7);self.assertEqual(d.exception_events[0]['saved_pc'],'0x00000104')
        d=module_cpu();d.bus.atu.regs[TSR]=None;d.bus.atu.write(TIER,2,1);sp=d.r[15]
        r=d.run(1);self.assertEqual(r['stop']['reason'],'unknown_peripheral_reset_state');self.assertEqual(d.r[15],sp)

    def test_atu_held_source_reenters_unless_firmware_acknowledges(self):
        d=module_cpu();capture_request(d)
        data=bytearray(d.bus.image.data);data[0x500:0x504]=bytes.fromhex('002B0009')
        d.bus.image=ROMImage('synthetic',bytes(data));d.run(3)
        self.assertEqual(d.interrupt_entries,2);self.assertTrue(d.bus.atu.interrupt_pending)

    def test_adc_actual_firmware_start_completion_isr_read_and_return(self):
        for voltage,count in ((1,204),(4,819)):
            d=NCBootDiagnostic(sensor_rom(),adc_fixture=adc_fields(voltage,5,2))
            data=bytearray(d.bus.image.data);data[0x2F8:0x2FC]=(0x600).to_bytes(4,'big')
            for i,op in enumerate((0x6761,0x6050,0xE040,0x2500,0x7901,0x002B,0x0009)):
                data[0x600+2*i:0x602+2*i]=op.to_bytes(2,'big')
            d.bus.image=ROMImage('synthetic',bytes(data));d.r[5]=ADCSR0;d.r[6]=ADDR0;d.r[9]=0
            d.bus.write(IPRJ_ADDRESS,2,0x600);d.bus.write(ADCSR0,1,64);load_sr(d,0);sp=d.r[15]
            result=d.run(13)
            self.assertEqual(result['stop']['reason'],'instruction_limit')
            self.assertEqual(d.r[7]&0xFFFF,count<<6);self.assertEqual(d.r[3]&0xFFFF,count<<6)
            self.assertEqual(d.r[9],1);self.assertEqual(d.r[15],sp)
            self.assertEqual(d.exception_events[0]['vector'],190)
            self.assertEqual(d.exception_events[0]['saved_pc'],'0x00000108')
            self.assertEqual(d.exception_events[0]['source'],'ADI0')
            self.assertFalse(d.bus.adc.interrupt_pending)

    def test_adc_mask_disable_unknown_and_arbitration(self):
        for priority,mask,enable,expected in ((0,0,True,0),(5,5,True,0),(6,5,True,1),(6,0,False,0)):
            d=module_cpu();d.bus.adc.csr=0xC0 if enable else 0x80
            d.bus.write(IPRJ_ADDRESS,2,priority<<8);load_sr(d,mask<<4)
            data=bytearray(d.bus.image.data);data[0x2F8:0x2FC]=(0x400).to_bytes(4,'big')
            d.bus.image=ROMImage('synthetic',bytes(data));d.run(1)
            self.assertEqual(d.interrupt_entries,expected)
        d=module_cpu();capture_request(d);d.bus.adc.csr=0xC0;d.bus.write(IPRJ_ADDRESS,2,0x500)
        d.set_interval_request(True);d.run(1)
        self.assertEqual(d.exception_events[0]['source'],'IMI1A')
        d=module_cpu();d.bus.adc.csr=None;d.bus.write(IPRJ_ADDRESS,2,0x500);sp=d.r[15]
        self.assertEqual(d.run(1)['stop']['reason'],'unknown_peripheral_reset_state');self.assertEqual(d.r[15],sp)

    def test_adc_request_clear_by_enable_and_adf_read_before_write(self):
        d=module_cpu();d.bus.adc.csr=0xC0
        d.bus.adc.write(ADCSR0,1,64);self.assertTrue(d.bus.adc.interrupt_pending)
        d.bus.adc.read(ADCSR0,1);d.bus.adc.write(ADCSR0,1,64)
        self.assertFalse(d.bus.adc.interrupt_pending)
        d.bus.adc.csr=0xC0;d.bus.adc.write(ADCSR0,1,0)
        self.assertFalse(d.bus.adc.interrupt_pending);self.assertEqual(d.bus.adc.csr,128)

    def test_second_capture_vector_read_ack_and_return(self):
        from ecu_workbench.atu import GRB
        d=module_cpu();data=bytearray(d.bus.image.data)
        data[0x184:0x188]=(0x600).to_bytes(4,'big')
        for i,op in enumerate((0x6A51,0x6041,0xE000,0x2401,0x7901,0x002B,0x0009)):
            data[0x600+2*i:0x602+2*i]=op.to_bytes(2,'big')
        d.bus.image=ROMImage('synthetic',bytes(data));d.r[5]=GRB;d.r[9]=0;sp=d.r[15]
        t=d.bus.atu;t.write(TIOR,1,0x50);t.write(TIER,2,2);t.write(TSTR,1,2)
        t.advance_ticks(41);t.set_pin(False,'B');t.set_pin(True,'B');d.run(8)
        self.assertEqual(d.r[10],41);self.assertEqual(d.r[9],1);self.assertEqual(d.r[15],sp)
        self.assertEqual(d.exception_events[0]['vector'],97);self.assertFalse(t.interrupt_pending)

    def test_dual_capture_order_and_independent_ack(self):
        d=module_cpu();t=d.bus.atu;t.regs[TSR]=3;t.write(TIER,2,3)
        d.run(1);self.assertEqual(d.exception_events[0]['source'],'IMI1A')
        t.read(TSR,2);t.write(TSR,2,2)
        self.assertEqual(t.regs[TSR],2);self.assertTrue(t.interrupt_pending)
        load_sr(d,0);d.pc=0x100;d.run(2)
        self.assertEqual(d.exception_events[-1]['source'],'IMI1B')
        t.write(TIER,2,1);self.assertFalse(t.interrupt_pending)
