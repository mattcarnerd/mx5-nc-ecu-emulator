"""Generated save/restore diagnostic; unknown register bits remain unknown."""
import json
from .core import ROMImage
from .nc_boot import NCBootDiagnostic,ROM_LIMIT
from .integration_fixture import SyntheticProgram

def run_unknown_stack_fixture():
    data=bytearray(ROM_LIMIT)
    for offset,value in ((0,0x800),(4,0xFFFFBFA0),(8,0x800),(12,0xFFFFBFA0)):
        data[offset:offset+4]=value.to_bytes(4,'big')
    p=SyntheticProgram(0x800);p.emit(0xE800);p.constant(1,0x1000)
    p.emit(0x410B,0x0009,0xAFFE,0x0009);p.install(data)
    p=SyntheticProgram(0x1000)
    p.emit(0x2FB6,0x2FA6,0xEB55,0xEA33,0x6AF6,0x6BF6,0x7801,0x000B,0x0009)
    p.install(data)
    cpu=NCBootDiagnostic(ROMImage('generated unknown stack fixture',bytes(data)))
    sp=cpu.r[15];r=cpu.run(80)
    registers={f'R{n}':{'known_value':cpu.transport_bits(n).value,'known_mask':cpu.transport_bits(n).mask}
               for n in (10,11)}
    passed=(cpu.r[8]==1 and cpu.r[15]==sp and 0x800<=cpu.pc<0x1000
            and all(item['known_mask']==0 for item in registers.values())
            and r['stop']['reason']=='instruction_limit')
    return {'kind':'generated_unknown_stack_fixture','fixture_passed':passed,
            'manufacturer_firmware_used':False,'boot_complete':False,
            'stack_restored':cpu.r[15]==sp,'returned_to_main_fixture':0x800<=cpu.pc<0x1000,
            'handler_count':cpu.r[8],'restored_registers':registers,
            'attempted_instructions':r['executed_instructions'],'completed_instructions':r['completed_instructions'],
            'note':'Known value is meaningful only under its known mask; mask0 selects no register value. Generated call/return is not original ECU boot.'}

if __name__=='__main__':print(json.dumps(run_unknown_stack_fixture(),indent=2))
