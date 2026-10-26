"""Independent CPU reset replay under an explicitly captured peripheral transcript.

The transcript is emulator-generated input, not a hardware trace. Branch
outcomes and instruction addresses are never supplied to the reference CPU.
"""
from tools.audit_sh2_path import SymbolicPath,Z3_PIN
from tools.audit_sh2_sleigh import PROFILES

class TranscriptEnd(Exception):pass

class TranscriptPath(SymbolicPath):
    def __init__(self,rom,registers,transcript):
        super().__init__(rom,registers)
        self.transcript=transcript;self.position=0

    def event(self,kind,address,width):
        if self.position>=len(self.transcript):raise ValueError('Peripheral transcript exhausted')
        event=self.transcript[self.position]
        if (event['kind'],event['address'],event['width'])!=(kind,address,width):
            raise ValueError('Independent peripheral request differs from transcript')
        self.position+=1;return event

    def load(self,address,width):
        if 0<=address and address+width<=len(self.rom) or 0xFFFF8000<=address and address+width<=0xFFFFC000:
            return super().load(address,width)
        if address<0xFFFFC000:raise ValueError('Unsupported memory gap load')
        event=self.event('read',address,width)
        return self.seed((event['value'],event['mask']),8*width,'io_'+str(self.position))

    def store(self,address,width,value):
        if 0xFFFF8000<=address and address+width<=0xFFFFC000:return super().store(address,width,value)
        if address<0xFFFFC000:raise ValueError('Unsupported memory/ROM store')
        event=self.event('write',address,width)
        difference=(value^self.z.BitVecVal(event['value'],8*width))&self.z.BitVecVal(event['mask'],8*width)
        if self.number(difference)!=0:raise ValueError('Independent peripheral output differs from transcript')
        self.stores+=1
        if self.position==len(self.transcript):raise TranscriptEnd()

    def replay(self,start,bound=100000):
        pc=start
        for _ in range(bound):
            try:pc=self.step(pc)
            except TranscriptEnd:
                return {'instruction_events':len(self.events),'control_transfers':self.branches,
                    'conditional_decisions':self.conditionals,'call_targets':self.calls,
                    'peripheral_events':self.position,'peripheral_transcript_consumed':True}
        raise ValueError('Independent reset replay bound exceeded')


def capture_reset_inputs(image):
    from ecu_workbench.nc_boot import NCBootDiagnostic
    fixture={'reset_completion_ticks':1,'recessive_bus_ticks':64}
    cpu=NCBootDiagnostic(image,nmi_high=True,hudi_scenario='trst-reset',phi_cycles_per_instruction=1,
        experimental_mcr_bit6=0,hcan_fixture=fixture)
    transcript=[];observed=[];depth={'read':0,'write':0}
    read_value=cpu.bus.read_cpu_value;read=cpu.bus.read
    write_value=cpu.bus.write_cpu_value;write=cpu.bus.write;execute=cpu.execute
    def peripheral(address):return address>=0xFFFFC000
    def record(kind,address,width,value,mask):
        limit=(1<<(8*width))-1
        transcript.append({'kind':kind,'address':address,'width':width,'value':value&limit,'mask':mask&limit})
    def typed_read(address,width):
        depth['read']+=1
        try:result=read_value(address,width)
        finally:depth['read']-=1
        if peripheral(address):record('read',address,width,result.value,result.mask)
        return result
    def concrete_read(address,width):
        result=read(address,width)
        if peripheral(address) and not depth['read']:record('read',address,width,result,(1<<(8*width))-1)
        return result
    def typed_write(address,width,bits):
        if peripheral(address):record('write',address,width,bits.value,bits.mask)
        depth['write']+=1
        try:return write_value(address,width,bits)
        finally:depth['write']-=1
    def concrete_write(address,width,value):
        if peripheral(address) and not depth['write']:record('write',address,width,value,(1<<(8*width))-1)
        return write(address,width,value)
    def capture(**kwargs):
        observed.append(cpu.pc)
        return execute(**kwargs)
    cpu.bus.read_cpu_value=typed_read;cpu.bus.read=concrete_read
    cpu.bus.write_cpu_value=typed_write;cpu.bus.write=concrete_write;cpu.execute=capture
    result=cpu.run(100000)
    if result['interrupt_entries']!=0:raise ValueError('Reset replay scope excludes interrupt input')
    if result['stop']['reason']!='invalid_peripheral_write' or result['stop'].get('address')!='0xFFFFD104':
        raise ValueError('Expected prohibited control store not reached')
    return transcript,observed,result


def audit_rom_reset(path):
    from ecu_workbench.core import ROMImage
    image=ROMImage.from_file(path)
    if image.sha256 not in PROFILES:raise ValueError('Unreviewed reset replay image')
    transcript,observed,original=capture_reset_inputs(image)
    pc=int.from_bytes(image.data[:4],'big');sp=int.from_bytes(image.data[4:8],'big')
    machine=TranscriptPath(image.data,{'r15':sp,'sr':(0xF0,0xF0)},transcript)
    result=machine.replay(pc)
    if machine.events!=observed:raise ValueError('Independent reset instruction path differs')
    return {'calibration':PROFILES[image.sha256][0],'rom_sha256':image.sha256,'z3_solver_version':Z3_PIN,
        'result':result,'all_instruction_events_matched':True,
        'reset_register_inputs':'ROM_vector_PC_SP_and_documented_SR_mask_F0_other_bits_symbolic',
        'ram_initial_values_selected':False,'peripheral_input_source':'emulator_generated_transcript_not_hardware',
        'branch_choices_forced_from_observation':False,'physical_timing_verified':False,
        'hardware_behavior_verified':False,'initialization_verified':False,
        'terminal_write_is_attempt_not_completed':True,
        'terminal_store':{'address':original['stop']['address'],'width':original['stop']['width'],'value':original['stop']['value']},
        'assumptions':{'reset':'power','nmi_high':True,'hudi_scenario':'trst-reset',
            'phi_cycles_per_instruction':1,'experimental_mcr_bit6':0,
            'hcan_fixture':{'reset_completion_ticks':1,'recessive_bus_ticks':64}}}


def generated_reset_audit():
    def image(branch=False):
        data=bytearray(1048576)
        data[:4]=(0x100).to_bytes(4,'big');data[4:8]=(0xFFFFBFA0).to_bytes(4,'big')
        if branch:words=(0x9307,0x6031,0xC901,0x8800,0x8901,0xE400,0x0009,0x2301,0x0009,0xD052)
        else:words=(0x9304,0xE503,0x605C,0x4018,0x8132,0x0009,0xD100)
        for i,w in enumerate(words):data[0x100+2*i:0x102+2*i]=w.to_bytes(2,'big')
        return bytes(data)
    def event(kind,address,value,mask=65535,width=2):
        return dict(kind=kind,address=address,width=width,value=value,mask=mask)
    seeds={'r15':0xFFFFBFA0,'sr':(0xF0,0xF0)}
    machine=TranscriptPath(image(),seeds,[event('write',0xFFFFD104,0x300)])
    result=machine.replay(0x100)
    if result['instruction_events']!=5:raise ValueError('Generated reset event count differs')
    for value,count in ((0,6),(1,8)):
        t=[event('read',0xFFFFD052,value),event('write',0xFFFFD052,value)]
        result=TranscriptPath(image(True),seeds,t).replay(0x100)
        if result['instruction_events']!=count:raise ValueError('Independent input-driven branch differs')
    bad=[lambda:TranscriptPath(image(),seeds,[event('write',0xFFFFD104,0x200)]).replay(0x100),
        lambda:TranscriptPath(image(),seeds,[event('write',0xFFFFD104,0x300,width=1)]).replay(0x100),
        lambda:TranscriptPath(image(True),seeds,[event('read',0xFFFFD052,0,mask=0),event('write',0xFFFFD052,0)]).replay(0x100),
        lambda:TranscriptPath(image(True),seeds,[event('read',0xFFFFD050,0),event('write',0xFFFFD052,0)]).replay(0x100)]
    for f in bad:
        try:f()
        except ValueError:continue
        raise ValueError('Negative transcript case accepted')
    return {'positive_programs':3,'negative_transcripts_rejected':4,'all_matched':True,
        'unknown_input_selected':False,'physical_hardware_verified':False}
