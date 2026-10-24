"""Generated synthetic firmware exercising IMI1A/ADI0 and raw GPIO commands.

No manufacturer ROM, NC tooth pattern, board clock or engine behavior used.
"""
import argparse
import json
from .core import ROMImage
from .nc_boot import NCBootDiagnostic,ROM_LIMIT,PCDR_ADDRESS,PCIOR_ADDRESS
from .atu import TSTR,TIOR,TIER,TSR,GR
from .adc import ADCSR0,ADCR0,ADDR0
from .interrupts import IPRD_ADDRESS,IPRJ_ADDRESS,IMI1A_VECTOR,ADI0_VECTOR
from .sensor_fixture import adc_fields

class SyntheticProgram:
    """Small internal encoder; PC-relative constants are entirely synthetic."""
    def __init__(self,origin):self.origin=origin;self.words=[];self.literals=[]
    def emit(self,*words):self.words.extend(words)
    def constant(self,n,value):
        self.literals.append((len(self.words),n,value));self.words.append(0)
    def write(self,address,width,value):
        self.constant(1,address)
        if 0<=value<128:self.emit(0xE000|value)
        else:self.constant(0,value)
        self.emit({1:0x2100,2:0x2101,4:0x2102}[width])
    def install(self,data):
        pool=(self.origin+2*len(self.words)+3)&~3
        for i,n,value in self.literals:
            pc=self.origin+2*i;disp=(pool-((pc+4)&~3))//4
            if not 0<=disp<=255:raise ValueError('Synthetic literal out of range')
            self.words[i]=0xD000|(n<<8)|disp
            data[pool:pool+4]=value.to_bytes(4,'big');pool+=4
        for i,op in enumerate(self.words):
            data[self.origin+2*i:self.origin+2*i+2]=op.to_bytes(2,'big')


def build_integration_rom():
    data=bytearray(ROM_LIMIT)
    for offset,value in ((0,0x800),(4,0xFFFFBFA0),(8,0x800),(12,0xFFFFBFA0),
                         (4*IMI1A_VECTOR,0x1000),(4*ADI0_VECTOR,0x1100)):
        data[offset:offset+4]=value.to_bytes(4,'big')
    p=SyntheticProgram(0x800)
    p.constant(0,0xF0);p.emit(0x400E,0xE800,0xE900)
    for a,w,v in ((IPRD_ADDRESS,2,0x50),(IPRJ_ADDRESS,2,0x600),(PCIOR_ADDRESS,2,31),
                  (PCDR_ADDRESS,2,0),(TIOR,1,5),(TIER,2,1),(TSTR,1,2),(ADCSR0,1,64)):
        p.write(a,w,v)
    p.emit(0xE000,0x400E)
    p.write(ADCR0,1,47)
    p.emit(0xAFFE,0x0009)  # explicit bounded idle fixture, not an ECU main-loop claim
    p.install(data)
    p=SyntheticProgram(0x1000)
    p.emit(0x2F06,0x2F16)  # preserve scratch registers for nested ADC interrupt
    p.constant(1,GR);p.emit(0x6A11)
    p.constant(1,TSR);p.emit(0x6011,0xE000,0x2101)
    p.write(PCDR_ADDRESS,2,1);p.emit(0x7801,0x61F6,0x60F6,0x002B,0x0009)
    p.install(data)
    p=SyntheticProgram(0x1100)
    p.emit(0x2F06,0x2F16)
    p.constant(1,ADDR0);p.emit(0x6B11,0x60B3,0x4019,0xC91F)
    p.constant(1,PCDR_ADDRESS);p.emit(0x2101)
    p.constant(1,ADCSR0);p.emit(0x6010,0xE040,0x2100,0x7901)
    p.emit(0x61F6,0x60F6,0x002B,0x0009);p.install(data)
    return ROMImage('generated synthetic interrupt fixture',bytes(data))


def run_integration_fixture(*,voltage,reference,adc_delay,capture_delay,capture_counter_ticks,max_steps=160):
    fixture=adc_fields(voltage,reference,adc_delay)
    if fixture is None:raise ValueError('Explicit voltage, reference and ADC delay required')
    if type(capture_delay) is not int or not 1<=capture_delay<=1000000:
        raise ValueError('Explicit capture delay must be1..1000000 completed instructions')
    if type(capture_counter_ticks) is not int or not 0<=capture_counter_ticks<=1000000:
        raise ValueError('Explicit selected counter packet must be0..1000000 ticks')
    if type(max_steps) is not int or not 1<=max_steps<=10000:raise ValueError('Fixture budget must be1..10000')
    cpu=NCBootDiagnostic(build_integration_rom(),nmi_high=True,adc_fixture=fixture)
    cpu.scheduled_peripheral_events=1  # declared even when startup/budget prevents scheduling/firing
    timeline=[];total=0;stack=[]
    def emit(payload):
        nonlocal total
        payload=dict(payload);kind=payload.pop('kind');payload.pop('tick',None)
        source_unit=payload.pop('time_unit',None)
        if source_unit:payload['source_time_unit']=source_unit
        if kind=='exception_entry':stack.append(payload['source'])
        timeline.append({'sequence':total,'kind':kind,'tick':cpu.clock.ticks,
                         'time_unit':'completed_instruction_ticks','active_source':stack[-1] if stack else None,**payload})
        total+=1
        if len(timeline)>256:del timeline[0]
        if kind=='exception_return' and stack:stack.pop()
    cpu.event_sink=emit;cpu.bus.event_sink=emit;cpu.bus.adc.event_sink=emit
    def capture_event(event):
        event=dict(event);event['counter_tick']=event.pop('tick')
        event['counter_time_unit']=event.pop('time_unit');emit(event)
    cpu.bus.atu.event_sink=capture_event
    original_start=cpu.bus.adc.on_start
    def on_start(generation):
        original_start(generation)
        def supply_capture():
            emit({'kind':'explicit_capture_fixture','selected_counter_packet':capture_counter_ticks})
            cpu.bus.atu.advance_ticks(capture_counter_ticks)
            cpu.bus.atu.set_pin(False);cpu.bus.atu.set_pin(True)
        cpu.clock.schedule(cpu.clock.ticks+capture_delay,supply_capture)
    cpu.bus.adc.on_start=on_start
    sp=cpu.r[15];result=cpu.run(max_steps)
    counts={'IMI1A':cpu.r[8],'ADI0':cpu.r[9]}
    passed=(result['stop']['reason']=='instruction_limit' and counts=={'IMI1A':1,'ADI0':1}
            and cpu.r[15]==sp and 0x800<=cpu.pc<0x1000
            and not cpu.bus.atu.interrupt_pending and not cpu.bus.adc.interrupt_pending)
    return {'kind':'synthetic_interrupt_integration','manufacturer_firmware_used':False,
        'fixture_passed':passed,'boot_complete':False,'validated_NC_pattern':False,
        'inputs':{'adc_fixture':fixture,'capture_delay_completed_instructions':capture_delay,
                  'explicit_selected_counter_ticks':capture_counter_ticks,'max_steps':max_steps},
        'attempted_instructions':result['executed_instructions'],'completed_instructions':result['completed_instructions'],
        'handler_counts':counts,'capture_word':None if cpu.r[10] is None else cpu.r[10]&0xFFFF,
        'adc_word':None if cpu.r[11] is None else cpu.r[11]&0xFFFF,
        'stack_restored':cpu.r[15]==sp,'returned_to_main_fixture':0x800<=cpu.pc<0x1000,'interrupt_entries':result['interrupt_entries'],
        'explicit_peripheral_inputs':result['explicit_peripheral_inputs'],
        'scheduled_peripheral_events':result['scheduled_peripheral_events'],
        'stop':result['stop'],'timeline':timeline,'timeline_events_dropped':max(0,total-256),
        'raw_gpio_commands':result['raw_gpio_commands'],
        'note':'Generated firmware and explicit input/clock/completion fixtures; not original-ROM boot or engine operation.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Run generated capture/ADC/GPIO interrupt fixture')
    parser.add_argument('--voltage',required=True);parser.add_argument('--reference',required=True)
    parser.add_argument('--adc-delay',type=int,required=True);parser.add_argument('--capture-delay',type=int,required=True)
    parser.add_argument('--capture-counter-ticks',type=int,required=True);parser.add_argument('--steps',type=int,default=160)
    a=parser.parse_args(argv)
    try:report=run_integration_fixture(voltage=a.voltage,reference=a.reference,adc_delay=a.adc_delay,
        capture_delay=a.capture_delay,capture_counter_ticks=a.capture_counter_ticks,max_steps=a.steps)
    except ValueError as error:parser.error(str(error))
    print(json.dumps(report,indent=2))
    return 0 if report['fixture_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
