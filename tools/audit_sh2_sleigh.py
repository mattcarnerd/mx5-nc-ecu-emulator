"""Bounded independent SLEIGH audit; not a hardware or full-CPU simulator.

Install requirements-audit.txt. OEM instruction bytes never enter the report.
Only straight-line p-code operations listed below are accepted; missing state
and unsupported operations fail rather than selecting values.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
PIN='4.0.1'
LANGUAGE='SuperH:BE:32:SH-2'

class LiftMachine:
    def __init__(self,registers,rom=b'',context=None):
        import pypcode
        if pypcode.__version__!=PIN:raise ValueError('Audit requires pypcode=='+PIN)
        self.context=context or pypcode.Context(LANGUAGE)
        self.storage={};self.rom=rom;self.writes=[]
        for name,value in registers.items():
            if type(value) is not int:raise ValueError('Only concrete supplied register seeds accepted')
            self.put(self.context.registers[name],value)

    def get(self,node):
        if node.space.name=='const':return node.offset
        try:
            return int.from_bytes(bytes(self.storage[(node.space.name,node.offset+i)] for i in range(node.size)),'big')
        except KeyError:raise ValueError('Independent audit needs an unknown input') from None

    def put(self,node,value):
        value &= (1<<(8*node.size))-1
        for i,b in enumerate(value.to_bytes(node.size,'big')):
            self.storage[(node.space.name,node.offset+i)]=b

    def run(self,code,address=0x100):
        decoded=self.context.disassemble(code,base_address=address)
        if sum(i.length for i in decoded.instructions)!=len(code):raise ValueError('Incomplete independent decode')
        ops=self.context.translate(code,base_address=address).ops
        marks=0
        for op in ops:
            name=op.opcode.name
            if name=='IMARK':marks+=1;continue
            if name in ('LOAD','STORE'):
                if op.inputs[0].getSpaceFromConst().name!='ram':raise ValueError('Unsupported address space')
                where=self.get(op.inputs[1])
                if name=='STORE':
                    self.writes.append({'address':where,'width':op.inputs[2].size,'value':self.get(op.inputs[2])})
                    continue
                size=op.output.size
                if where<0 or where+size>len(self.rom):raise ValueError('Load outside explicitly supplied ROM')
                value=int.from_bytes(self.rom[where:where+size],'big')
            else:
                args=[self.get(v) for v in op.inputs]
                if name in ('COPY','INT_ZEXT'):value=args[0]
                elif name=='INT_SEXT':
                    bits=8*op.inputs[0].size
                    value=args[0]-(1<<bits) if args[0]&(1<<(bits-1)) else args[0]
                elif name=='INT_ADD':value=args[0]+args[1]
                elif name=='INT_LEFT':value=args[0]<<args[1]
                elif name=='INT_AND':value=args[0]&args[1]
                elif name=='INT_OR':value=args[0]|args[1]
                elif name=='INT_XOR':value=args[0]^args[1]
                else:raise ValueError('Unsupported independent p-code operation: '+name)
            self.put(op.output,value)
        if marks!=len(decoded.instructions):raise ValueError('Instruction/lift count differs')
        return {'instructions':marks,'writes':list(self.writes),'r0':self.get(self.context.registers['r0'])}


def metadata():
    import pypcode
    context=pypcode.Context(LANGUAGE)
    return {'engine':'Ghidra SLEIGH via pypcode','pypcode_version':pypcode.__version__,
        'language':LANGUAGE,'sla_sha256':hashlib.sha256(Path(context.language.slafile_path).read_bytes()).hexdigest(),
        'scope':'straight_line_integer_lift_with_supplied_entry_state_not_full_CPU_or_hardware'}


def synthetic_audit():
    import pypcode
    from ecu_workbench.core import ROMImage
    from ecu_workbench.nc_boot import NCBootDiagnostic
    context=pypcode.Context(LANGUAGE);count=0
    for displacement in (0,2,15):
        words=(0x605C,0x4018,0x666C,0x306C,0x303C,0x81C0|displacement)
        code=b''.join(w.to_bytes(2,'big') for w in words)
        data=bytearray(1048576)
        for i,v in enumerate((0x100,0xFFFFBFA0,0x100,0xFFFFBFA0)):data[4*i:4*i+4]=v.to_bytes(4,'big')
        data[0x100:0x100+len(code)]=code;image=ROMImage('generated-audit',bytes(data))
        for mode in range(8):
            for dlc in (0,8,15,255):
                for nmc in (0,0x2000,0xFFFFFF00):
                    for base in (0xFFFF8000,0xFFFF8200,0xFFFFBF80):
                        seeds={'r3':nmc,'r5':0xABCDEF00|mode,'r6':0x12345600|dlc,'r12':base}
                        reference=LiftMachine(seeds,context=context).run(code)
                        cpu=NCBootDiagnostic(image)
                        for name,value in seeds.items():cpu.r[int(name[1:])]=value
                        result=cpu.run(6);expected=(nmc+(mode<<8)+dlc)&0xFFFFFFFF;address=base+2*displacement
                        assert result['completed_instructions']==6
                        assert cpu.r[0]==reference['r0']==expected
                        assert reference['writes']==[{'address':address,'width':2,'value':expected&65535}]
                        assert cpu.bus.read(address,2)==expected&65535
                        assert cpu.t is None
                        count+=1
    return {'generated_vectors':count,'all_matched':True,'covers':['EXTU.B byte alias','SHLL8','ADD modulo32',
        'MOV.W scaled displacement','big_endian_word_store','T_unchanged'],'physical_timing_verified':False}

PROFILES={
 'bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf':('LF9VEB',0xE60,0xE70),
 '590111ace660ef6257572dd1ec45948558a7741f3c6aa505fa432a698d1f15f7':('LFNPEA',0xE60,0xE70),
 'ca9ecd4bf0556dc66712341d303c171c220be104060e61bc4cbe32f4b4f1adcf':('LF4XEC',0xCAC,0xCBC),
}

def audit_rom(path):
    from ecu_workbench.core import ROMImage
    from ecu_workbench.nc_boot import NCBootDiagnostic
    image=ROMImage.from_file(path)
    if image.sha256 not in PROFILES:raise ValueError('No reviewed straight-line window for this ROM hash')
    name,start,stop=PROFILES[image.sha256]
    fixture={'reset_completion_ticks':1,'recessive_bus_ticks':64}
    cpu=NCBootDiagnostic(image,nmi_high=True,hudi_scenario='trst-reset',phi_cycles_per_instruction=1,
        experimental_mcr_bit6=0,hcan_fixture=fixture)
    captured={};observed_writes=[];execute=cpu.execute
    write=cpu.bus.write_cpu_value
    def capture_write(address,width,bits):
        if captured:
            observed_writes.append({'address':address,'width':width,'value':bits.concrete() & ((1<<(8*width))-1)})
        return write(address,width,bits)
    cpu.bus.write_cpu_value=capture_write
    def capture(**kwargs):
        if cpu.pc==start and not captured:
            if kwargs.get('delay_slot'):raise ValueError('Audit window begins in delay slot')
            captured.update({f'r{i}':v for i,v in enumerate(cpu.r) if type(v) is int})
        return execute(**kwargs)
    cpu.execute=capture
    result=cpu.run(100000)
    if not captured or result['next_dependency']['instruction_pc']!=f'0x{stop:08X}':
        raise ValueError('Expected reached window not observed')
    code=image.data[start:stop+2]
    reference=LiftMachine(captured,image.data).run(code,address=start)
    access=result['stop']
    expected={'address':int(access['address'],16),'width':access['width'],'value':int(access['value'],16)}
    if reference['writes']!=observed_writes or observed_writes[-1]!=expected or reference['r0']!=cpu.r[0]:
        raise ValueError('Independent semantic mismatch for '+name)
    return {'calibration':name,'rom_sha256':image.sha256,'entry_state_source':'captured_local_emulator_state_not_independent_full_reset_trace',
        'assumptions':{'reset':'power','nmi_high':True,'hudi_scenario':'trst-reset','phi_cycles_per_instruction':1,
            'experimental_mcr_bit6':0,'hcan_fixture':fixture},
        'window_start':f'0x{start:08X}','window_end':f'0x{stop:08X}',
        'instructions':reference['instructions'],'stores_compared':len(observed_writes),'all_matched':True,
        'store':{'address':f"0x{expected['address']:08X}",'width':expected['width'],'value':f"0x{expected['value']:04X}"},
        'mode':(expected['value']>>8)&7,'hardware_behavior_verified':False,'initialization_verified':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',action='append',default=[])
    parser.add_argument('--synthetic',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.synthetic and not args.rom:parser.error('Select --synthetic or --rom')
    result={'schema':'nc-ecu-independent-sh2-audit-v1','tool':metadata(),
        'synthetic':synthetic_audit() if args.synthetic else None,'rom_windows':[audit_rom(p) for p in args.rom]}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'synthetic':result['synthetic'],'rom_windows':result['rom_windows']}))
if __name__=='__main__':main()
