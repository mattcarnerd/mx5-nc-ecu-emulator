"""Generated timer rollover firmware; explicit test clocks, no physical timing claims."""
import argparse
import json
from .core import ROMImage
from .nc_boot import NCBootDiagnostic, ROM_LIMIT
from .integration_fixture import SyntheticProgram
from .atu import PSCR, TCR, TCNT, TIOR, TIER, TSTR, TSR, GR, GRB
from .interrupts import IPRD_ADDRESS, IPRE_ADDRESS

def build_rom(clock_source):
    data=bytearray(ROM_LIMIT)
    for offset,value in ((0,0x800),(4,0xFFFFBFA0),(8,0x800),(12,0xFFFFBFA0),
                         (96*4,0x1000),(97*4,0x1100),(104*4,0x1200)):
        data[offset:offset+4]=value.to_bytes(4,'big')
    p=SyntheticProgram(0x800)
    p.constant(0,0xF0);p.emit(0x400E,0xE800,0xE900,0xEA00)
    for a,w,v in ((IPRD_ADDRESS,2,0x50),(IPRE_ADDRESS,2,0x6000),
                  (PSCR,1,1),(TCR,1,1 if clock_source=='internal' else 6),
                  (TCNT,2,0xFFFE),(TIOR,1,0x55),(TIER,2,0x103),(TSTR,1,2)):
        p.write(a,w,v)
    p.emit(0xE000,0x400E,0xAFFE,0x0009);p.install(data)
    for origin,capture,register,count,clear in (
            (0x1000,GR,11,8,0x102),(0x1100,GRB,12,9,0x101),
            (0x1200,None,0,10,3)):
        p=SyntheticProgram(origin);p.emit(0x2F06,0x2F16)
        if capture is not None:p.constant(1,capture);p.emit(0x6001|(register<<8)|0x10)
        p.constant(1,TSR);p.emit(0x6011)
        p.write(TSR,2,clear)
        p.emit(0x7001|(count<<8),0x61F6,0x60F6,0x002B,0x0009);p.install(data)
    return ROMImage('generated dual capture rollover fixture',bytes(data))

def run_dual_capture_fixture(*,clock_source,max_steps=280):
    if clock_source not in ('internal','external'):raise ValueError('Select internal or external clock fixture')
    if type(max_steps) is not int or not 1<=max_steps<=10000:raise ValueError('Budget must be1..10000')
    cpu=NCBootDiagnostic(build_rom(clock_source),nmi_high=True)
    cpu.scheduled_peripheral_events=2
    timeline=[]
    def emit(payload):
        timeline.append(dict(payload))
    cpu.event_sink=emit
    cpu.bus.atu.event_sink=emit
    t=cpu.bus.atu
    def supply(count):
        emit({'kind':'explicit_clock_packet','source':clock_source,
              'supplied_phi_cycles':count*4 if clock_source=='internal' else None,
              'rising_edges':count if clock_source=='external' else None,
              'completed_instruction_tick':cpu.clock.ticks})
        if clock_source=='internal':t.advance_phi_cycles(count*4)
        else:
            for _ in range(count):t.set_clock_pin('A',False);t.set_clock_pin('A',True)
    def first():
        if clock_source=='internal':t.begin_clock_fixture(phase=0)
        else:t.begin_external_clock_fixture();t.set_clock_pin('A',False)
        t.set_pin(False,'A');t.set_pin(False,'B')
        supply(1);t.set_pin(True,'A')
    def second():
        supply(2);t.set_pin(True,'B')
    cpu.clock.schedule(100,first);cpu.clock.schedule(180,second)
    sp=cpu.r[15];result=cpu.run(max_steps)
    counts={'IMI1A':cpu.r[8],'IMI1B':cpu.r[9],'OVI1A':cpu.r[10]}
    captures=[None if cpu.r[n] is None else cpu.r[n]&0xFFFF for n in (11,12)]
    vectors=[e['vector'] for e in timeline if e.get('kind')=='exception_entry']
    passed=(counts=={'IMI1A':1,'IMI1B':1,'OVI1A':1} and captures==[65535,1]
            and vectors==[96,104,97] and cpu.r[15]==sp and 0x800<=cpu.pc<0x1000
            and t.regs[TSR]==0 and result['stop']['reason']=='instruction_limit')
    return {'kind':'synthetic_dual_capture_rollover','fixture_passed':passed,
            'manufacturer_firmware_used':False,'boot_complete':False,'physical_timing_verified':False,
            'inputs':{'clock_source':clock_source,'PSCR1':1,'TCR1A':1 if clock_source=='internal' else 6,
                      'initial_counter':65534,'capture_packet_ticks':[1,2],
                      'event_completed_instruction_ticks':[100,180],'max_steps':max_steps},
            'handler_counts':counts,'capture_words':captures,'interrupt_vectors':vectors,
            'status_flags':t.regs[TSR],'stack_restored':cpu.r[15]==sp,
            'returned_to_main_fixture':0x800<=cpu.pc<0x1000,
            'clock_fixture':t.clock_report(),'stop':result['stop'],'timeline':timeline,
            'note':'Explicit generated fixture. No measured oscillator, NC waveform or full ECU boot.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clock-source',required=True,choices=('internal','external'))
    parser.add_argument('--steps',type=int,default=280)
    args=parser.parse_args()
    report=run_dual_capture_fixture(clock_source=args.clock_source,max_steps=args.steps)
    print(json.dumps(report,indent=2))
    return 0 if report['fixture_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
