"""Explicit hypotheses for investigation, separate from reset baselines.

Prior RAM is supplied by the caller, never inferred from power reset. CAN
command recording and reset-status isolation do not model prohibited modes.
"""
from collections import Counter
from .nc_boot import NCBootDiagnostic
from .share_report import make_shareable_blocker_report

TAIL_WORD=0xFFFFBFFC

def explore_startup(rom, *, prior_ram_word, phi_cycles_per_instruction,
                    max_steps=100000, port_b_pins=None, port_c_pins=None, port_d_pins=None, startup_timer_fixture=None, experimental_wdt_ordered_stop=False):
    from .startup_timer_fixture import normalize_startup_timer_fixture,bind_startup_timer_fixture
    if type(experimental_wdt_ordered_stop) is not bool:raise ValueError('WDT ordering hypothesis must be boolean')
    timer_fixture=normalize_startup_timer_fixture(startup_timer_fixture)
    if type(phi_cycles_per_instruction) is not int or not 1<=phi_cycles_per_instruction<=1000000:
        raise ValueError('Explicit artificial phi ratio must be1..1000000')
    if type(prior_ram_word) is not int or not 0<=prior_ram_word<=0xFFFFFFFF:
        raise ValueError('Explicit prior RAM word must be an unsigned32-bit integer')
    if port_b_pins is not None and (type(port_b_pins) is not int or not 0<=port_b_pins<=0xFFFF):
        raise ValueError('Port B hypothesis must be an unsigned16-bit integer')
    for name,value,limit in (('C',port_c_pins,0x1F),('D',port_d_pins,0xFFFF)):
        if value is not None and (type(value) is not int or not 0<=value<=limit):
            raise ValueError(f'Port {name} hypothesis out of range')
    fixture={'reset_completion_ticks':1,'recessive_bus_ticks':64,
             'defer_mailbox_effects':True,'preserve_supplied_reset_status':True}
    cpu=NCBootDiagnostic(rom,nmi_high=True,hudi_scenario='trst-reset',
        phi_cycles_per_instruction=phi_cycles_per_instruction,
        experimental_mcr_bit6=0,hcan_fixture=fixture,port_b_pin_values=port_b_pins,
        port_c_pin_values=port_c_pins,port_d_pin_values=port_d_pins)
    cpu.bus.watchdog.experimental_ordered_stop=experimental_wdt_ordered_stop
    timer_state=bind_startup_timer_fixture(cpu,timer_fixture)
    cpu.bus.write(TAIL_WORD,4,prior_ram_word)
    result=cpu.run(max_steps)
    settings={'reset':'power','nmi':'high','max_steps':max_steps,
        'explicit_pin_values':any(p is not None for p in (port_b_pins,port_c_pins,port_d_pins)),'hudi_scenario':'trst-reset',
        'phi_cycles_per_instruction':phi_cycles_per_instruction,
        'experimental_mcr_bit6':0,'hcan_fixture':fixture,
        'experimental_wdt_ordered_stop':experimental_wdt_ordered_stop}
    reduced=make_shareable_blocker_report({'image':{'sha256':rom.sha256},
        'nc_boot':result,'diagnostic_settings':settings})
    # Deliberately a separate envelope. Do not import as a reset baseline or
    # strip its assumptions when discussing instruction progress.
    return {'schema':'nc-ecu-startup-exploration-v1',
        'evidence_class':'synthetic_hypotheses_no_physical_validation',
        'initialization_verified':False,'recurring_interrupts_verified':False,
        'assumptions':{'prior_ram_words':[{'address':'0xFFFFBFFC','width':4,
            'value':f'0x{prior_ram_word:08X}'}],
            'port_b_pins':None if port_b_pins is None else f'0x{port_b_pins:04X}',
            'port_c_pins':None if port_c_pins is None else f'0x{port_c_pins:04X}',
            'port_d_pins':None if port_d_pins is None else f'0x{port_d_pins:04X}',
            'startup_timer_fixture':timer_fixture,
            'experimental_wdt_ordered_stop':experimental_wdt_ordered_stop,
            'nmi_high':True,'hudi_scenario':'trst-reset',
            'phi_cycles_per_instruction':phi_cycles_per_instruction,
            'experimental_mcr_bit6':0,'hcan_fixture':fixture},
        'startup_timer_binding':timer_state,
        'atu_clock_fixture':result['atu_clock_fixture'],
        'interrupt_entries':result['interrupt_entries'],
        'watchdog_overflows':cpu.bus.watchdog.overflow_count,
        'wdt_ordered_stop_count':cpu.bus.watchdog.ordered_stop_count,
        'recent_pc_frequency':dict(Counter(t['pc'] for t in result['trace'] if 'pc' in t)),
        'diagnostic':reduced}


def main(argv=None):
    import argparse,json
    from pathlib import Path
    from .core import ROMImage
    parser=argparse.ArgumentParser(description='Explicit startup hypotheses; never a hardware/reset baseline')
    parser.add_argument('--rom',required=True)
    parser.add_argument('--prior-ram-word',required=True,type=lambda x:int(x,0))
    parser.add_argument('--phi-cycles-per-instruction',required=True,type=int)
    parser.add_argument('--steps',default=100000,type=int)
    parser.add_argument('--port-b-pins',type=lambda x:int(x,0))
    parser.add_argument('--port-c-pins',type=lambda x:int(x,0))
    parser.add_argument('--port-d-pins',type=lambda x:int(x,0))
    parser.add_argument('--startup-timer-p-phi',type=int)
    parser.add_argument('--channel10-initial-a',type=int,choices=(0,1))
    parser.add_argument('--channel10-initial-c',type=int,choices=(0,1))
    parser.add_argument('--channel10-initial-f',type=int,choices=(0,1))
    parser.add_argument('--experimental-channel10-wrap16',action='store_true')
    parser.add_argument('--experimental-wdt-ordered-stop',action='store_true')
    parser.add_argument('--report',required=True)
    args=parser.parse_args(argv)
    candidates=(args.channel10_initial_a,args.channel10_initial_c,args.channel10_initial_f)
    timer_fixture=None
    if args.startup_timer_p_phi is not None:
        if any(v is None for v in candidates):parser.error('Startup timers require all three channel10 initial candidates')
        timer_fixture={'p_phi_cycles_per_instruction':args.startup_timer_p_phi,
            'channel10_initial_candidates':dict(zip(('A','C','F'),candidates)),
            'zero_reload_policy':'experimental-wrap16' if args.experimental_channel10_wrap16 else None}
    elif any(v is not None for v in candidates) or args.experimental_channel10_wrap16:
        parser.error('Channel10 assumptions require --startup-timer-p-phi')
    try:
        result=explore_startup(ROMImage.from_file(args.rom),prior_ram_word=args.prior_ram_word,
            phi_cycles_per_instruction=args.phi_cycles_per_instruction,max_steps=args.steps,
            port_b_pins=args.port_b_pins,port_c_pins=args.port_c_pins,port_d_pins=args.port_d_pins,startup_timer_fixture=timer_fixture,experimental_wdt_ordered_stop=args.experimental_wdt_ordered_stop)
    except ValueError as error:parser.error(str(error))
    Path(args.report).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
