"""Explicit hypotheses for investigation, separate from reset baselines.

Prior RAM is supplied by the caller, never inferred from power reset. CAN
command recording and reset-status isolation do not model prohibited modes.
"""
from collections import Counter
from .nc_boot import NCBootDiagnostic
from .share_report import make_shareable_blocker_report

TAIL_WORD=0xFFFFBFFC

def explore_startup(rom, *, prior_ram_word, phi_cycles_per_instruction,
                    max_steps=100000, port_b_pins=None):
    if type(phi_cycles_per_instruction) is not int or not 1<=phi_cycles_per_instruction<=1000000:
        raise ValueError('Explicit artificial phi ratio must be1..1000000')
    if type(prior_ram_word) is not int or not 0<=prior_ram_word<=0xFFFFFFFF:
        raise ValueError('Explicit prior RAM word must be an unsigned32-bit integer')
    if port_b_pins is not None and (type(port_b_pins) is not int or not 0<=port_b_pins<=0xFFFF):
        raise ValueError('Port B hypothesis must be an unsigned16-bit integer')
    fixture={'reset_completion_ticks':1,'recessive_bus_ticks':64,
             'defer_mailbox_effects':True,'preserve_supplied_reset_status':True}
    cpu=NCBootDiagnostic(rom,nmi_high=True,hudi_scenario='trst-reset',
        phi_cycles_per_instruction=phi_cycles_per_instruction,
        experimental_mcr_bit6=0,hcan_fixture=fixture,port_b_pin_values=port_b_pins)
    cpu.bus.write(TAIL_WORD,4,prior_ram_word)
    result=cpu.run(max_steps)
    settings={'reset':'power','nmi':'high','max_steps':max_steps,
        'explicit_pin_values':port_b_pins is not None,'hudi_scenario':'trst-reset',
        'phi_cycles_per_instruction':phi_cycles_per_instruction,
        'experimental_mcr_bit6':0,'hcan_fixture':fixture}
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
            'nmi_high':True,'hudi_scenario':'trst-reset',
            'phi_cycles_per_instruction':phi_cycles_per_instruction,
            'experimental_mcr_bit6':0,'hcan_fixture':fixture},
        'interrupt_entries':result['interrupt_entries'],
        'watchdog_overflows':cpu.bus.watchdog.overflow_count,
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
    parser.add_argument('--report',required=True)
    args=parser.parse_args(argv)
    try:
        result=explore_startup(ROMImage.from_file(args.rom),prior_ram_word=args.prior_ram_word,
            phi_cycles_per_instruction=args.phi_cycles_per_instruction,max_steps=args.steps,
            port_b_pins=args.port_b_pins)
    except ValueError as error:parser.error(str(error))
    Path(args.report).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
