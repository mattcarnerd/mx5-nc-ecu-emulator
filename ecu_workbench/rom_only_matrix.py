"""Read-only scenario matrix; explicitly hypothetical inputs, never a hardware profile."""
import argparse
import json
from pathlib import Path
from .core import ROMImage
from .hudi import HUDI_SCENARIOS
from .nc_boot import diagnose_nc_reset
from .share_report import make_shareable_blocker_report

def run_rom_only_matrix(rom,*,max_steps,nmi_high):
    if type(max_steps) is not int or not 1<=max_steps<=100000:
        raise ValueError('Explicit budget must be1..100000')
    if nmi_high is not None and type(nmi_high) is not bool:
        raise ValueError('NMI must be explicitly True, False or unknown')
    cases=[('strict-reference-settings','unknown',None,None,300)]
    cases.extend((f'{hudi}-phi{phi}-bit{bit}',hudi,phi,bit,max_steps)
                 for hudi in HUDI_SCENARIOS for phi in (None,1) for bit in (None,0,1))
    rows=[]
    for name,hudi,phi,bit,budget in cases:
        settings={'reset':'power','nmi':'unknown' if nmi_high is None else 'high' if nmi_high else 'low',
                  'max_steps':budget,'explicit_pin_values':False,'hudi_scenario':hudi,
                  'phi_cycles_per_instruction':phi,'experimental_mcr_bit6':bit}
        boot=diagnose_nc_reset(rom,max_steps=budget,nmi_high=nmi_high,hudi_scenario=hudi,
                              phi_cycles_per_instruction=phi,experimental_mcr_bit6=bit)
        report=make_shareable_blocker_report({'image':{'sha256':rom.sha256},
                                            'diagnostic_settings':settings,'nc_boot':boot})
        rows.append({'case_id':name,'report':report})
    return {'schema_version':1,'kind':'rom_only_scenario_matrix','rom_sha256':rom.sha256,
            'max_steps_for_experiments':max_steps,'nmi':settings['nmi'],'cases':rows,
            'boot_complete':False,'hardware_profile_verified':False,
            'note':'Strict settings use budget300. Other cases use the declared budget; phi1 is an artificial completed-instruction ratio. All bit/H-UDI choices are hypothetical inputs, not board observations.'}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',required=True,type=Path)
    parser.add_argument('--steps',required=True,type=int)
    parser.add_argument('--nmi',required=True,choices=('high','low','unknown'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    try:
        result=run_rom_only_matrix(ROMImage.from_file(args.rom),max_steps=args.steps,
                                  nmi_high={'high':True,'low':False,'unknown':None}[args.nmi])
        output=json.dumps(result,indent=2)+'\n'
        if args.output:args.output.write_text(output,encoding='utf-8')
        else:print(output,end='')
    except (ValueError,OSError) as error:parser.error(str(error))
    return 0

if __name__=='__main__':raise SystemExit(main())
