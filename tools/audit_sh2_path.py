"""Bounded SLEIGH control-flow execution with symbolic unsupplied entry bytes.

No observed branch choice is asserted as a solver constraint. This is an
entry-snapshot differential check, not a physical or full-reset simulator.
"""
from importlib.metadata import version
from tools.audit_sh2_sleigh import PIN,LANGUAGE,PROFILES
from tools.audit_sh2_callers import CALLERS
Z3_PIN='5.3.2.0'
MASK_WORDS=(0xFFFFD050,0xFFFFD052,0xFFFFD850,0xFFFFD852)

class SymbolicPath:
    def __init__(self,rom,registers=None,ram=None):
        import pypcode,z3
        if pypcode.__version__!=PIN or version('z3-solver')!=Z3_PIN:raise ValueError('Pinned audit engines required')
        self.z=z3;self.context=pypcode.Context(LANGUAGE);self.rom=rom
        self.storage={};self.ram={};self.mask_words={};self.events=[];self.branches=0;self.conditionals=0;self.calls=0;self.stores=0
        for name,item in (registers or {}).items():
            node=self.context.registers[name]
            self.put(node,self.seed(item,8*node.size,'entry_'+name))
        for address,item in (ram or {}).items():self.ram[address]=self.seed(item,8,'ram_'+str(address))

    def seed(self,item,bits,name):
        z=self.z
        if type(item) is int:return z.BitVecVal(item,bits)
        if isinstance(item,tuple) and len(item)==2:
            value,mask=item;return (z.BitVec(name,bits)&z.BitVecVal(~mask,bits))|z.BitVecVal(value&mask,bits)
        raise ValueError('Invalid explicit seed')

    def fit(self,value,bits):
        z=self.z
        if value.size()>bits:return z.Extract(bits-1,0,value)
        return z.ZeroExt(bits-value.size(),value)

    def put(self,node,value):
        value=self.fit(value,8*node.size)
        for i in range(node.size):
            hi=8*(node.size-i)-1
            self.storage[(node.space.name,node.offset+i)]=self.z.simplify(self.z.Extract(hi,hi-7,value))

    def get(self,node):
        z=self.z
        if node.space.name=='const':return z.BitVecVal(node.offset,8*node.size)
        pieces=[]
        for i in range(node.size):
            key=(node.space.name,node.offset+i)
            if key not in self.storage and node.space.name=='unique':raise ValueError('Uninitialised lift temporary')
            if key not in self.storage:self.storage[key]=z.BitVec('unknown_'+key[0]+'_'+str(key[1]),8)
            pieces.append(self.storage[key])
        return z.simplify(pieces[0] if len(pieces)==1 else z.Concat(*pieces))

    def number(self,value):
        z=self.z;value=z.simplify(value)
        if z.is_bv_value(value):return value.as_long()
        solver=z.Solver();solver.set(timeout=5000)
        if solver.check()!=z.sat:raise ValueError('Symbolic uniqueness unavailable')
        candidate=solver.model().eval(value,model_completion=True)
        solver.add(value!=candidate)
        if solver.check()!=z.unsat:raise ValueError('Unresolved branch/target/address; no value selected')
        return candidate.as_long()

    def load(self,address,width):
        z=self.z
        if 0<=address and address+width<=len(self.rom):return z.BitVecVal(int.from_bytes(self.rom[address:address+width],'big'),8*width)
        if width==2 and address in MASK_WORDS:
            if address not in self.mask_words:self.mask_words[address]=z.BitVec('unknown_mask_'+str(address),16)
            return self.mask_words[address]
        if not 0xFFFF8000<=address or address+width>0xFFFFC000:raise ValueError('Unsupported hardware load in independent path '+hex(address)+' width '+str(width))
        pieces=[]
        for a in range(address,address+width):
            if a not in self.ram:self.ram[a]=z.BitVec('unknown_ram_'+str(a),8)
            pieces.append(self.ram[a])
        return pieces[0] if len(pieces)==1 else z.Concat(*pieces)

    def store(self,address,width,value):
        if width==2 and address in MASK_WORDS:
            self.mask_words[address]=value;self.stores+=1;return
        if 0<=address<len(self.rom):raise ValueError('ROM store in independent path')
        if 0xFFFF8000<=address and address+width<=0xFFFFC000:
            for i in range(width):
                hi=8*(width-i)-1;self.ram[address+i]=self.z.Extract(hi,hi-7,value)
        elif not (0xFFFFD100<=address and address+width<=0xFFFFD500):
            raise ValueError('Unsupported hardware store in independent path')
        # Mailbox writes are intents only; no controller effect/readback assumed.
        self.stores+=1

    def step(self,pc):
        z=self.z
        if pc&1 or not 0<=pc<len(self.rom)-1:raise ValueError('Invalid independent PC')
        self.storage={k:v for k,v in self.storage.items() if k[0]!='unique'}
        self.put(self.context.registers['pc'],z.BitVecVal(pc,32))
        tx=self.context.translate(self.rom[pc:pc+4],base_address=pc,max_instructions=1)
        if not tx.ops or tx.ops[0].opcode.name!='IMARK':raise ValueError('Missing instruction marker')
        marks=tx.ops[0].inputs
        if any(m.space.name!='ram' or m.size!=2 for m in marks):raise ValueError('Unsupported instruction marker')
        self.events.extend(m.offset for m in marks)
        following=pc+sum(m.size for m in marks)
        for op in tx.ops[1:]:
            kind=op.opcode.name
            if kind=='IMARK':raise ValueError('Unexpected additional marker')
            if kind in ('BRANCH','CBRANCH','BRANCHIND','CALL','CALLIND','RETURN'):
                if kind=='CBRANCH':self.conditionals+=1
                if kind in ('CALL','CALLIND'):self.calls+=1
                if kind=='CBRANCH' and self.number(self.get(op.inputs[1]))==0:
                    self.branches+=1;continue
                target=op.inputs[0]
                if target.space.name=='const':raise ValueError('Unsupported internal p-code jump')
                following=target.offset if target.space.name=='ram' else self.number(self.get(target))
                self.branches+=1;break
            if kind in ('LOAD','STORE'):
                if op.inputs[0].getSpaceFromConst().name!='ram':raise ValueError('Unsupported address space')
                address=self.number(self.get(op.inputs[1]))
                if kind=='STORE':self.store(address,op.inputs[2].size,self.get(op.inputs[2]));continue
                value=self.load(address,op.output.size)
            else:
                args=[self.get(v) for v in op.inputs]
                bits=8*op.output.size if op.output is not None else 0
                if kind in ('COPY','INT_ZEXT'):value=self.fit(args[0],bits)
                elif kind=='INT_SEXT':value=z.SignExt(bits-args[0].size(),args[0])
                elif kind=='SUBPIECE':
                    lo=self.number(args[1])*8;value=z.Extract(lo+bits-1,lo,args[0])
                elif kind=='PIECE':value=z.Concat(*args)
                elif kind=='INT_NEGATE':value=~args[0]
                elif kind=='INT_2COMP':value=-args[0]
                elif kind in ('INT_ADD','INT_SUB','INT_MULT','INT_AND','INT_OR','INT_XOR','INT_LEFT','INT_RIGHT'):
                    a,b=args[0],self.fit(args[1],args[0].size())
                    if kind=='INT_ADD':value=a+b
                    elif kind=='INT_SUB':value=a-b
                    elif kind=='INT_MULT':value=a*b
                    elif kind=='INT_AND':value=a&b
                    elif kind=='INT_OR':value=a|b
                    elif kind=='INT_XOR':value=a^b
                    elif kind=='INT_LEFT':value=a<<b
                    else:value=z.LShR(a,b)
                elif kind in ('INT_EQUAL','INT_NOTEQUAL','INT_LESS','INT_LESSEQUAL','INT_SLESS','INT_SLESSEQUAL'):
                    a,b=args
                    condition={'INT_EQUAL':lambda:a==b,'INT_NOTEQUAL':lambda:a!=b,
                        'INT_LESS':lambda:z.ULT(a,b),'INT_LESSEQUAL':lambda:z.ULE(a,b),
                        'INT_SLESS':lambda:a<b,'INT_SLESSEQUAL':lambda:a<=b}[kind]()
                    value=z.If(condition,z.BitVecVal(1,bits),z.BitVecVal(0,bits))
                else:raise ValueError('Unsupported independent operation: '+kind)
            self.put(op.output,value)
        return following

    def run(self,start,end,bound=10000,expected_events=None):
        pc=start
        for _ in range(bound):
            if pc==end:
                if expected_events is not None and self.events!=expected_events:raise ValueError('Independent path differs from observation')
                return {'instruction_events':len(self.events),'control_transfers':self.branches,
                    'conditional_decisions':self.conditionals,'call_targets':self.calls,
                    'stores':self.stores,'r5_low_byte':self.number(self.get(self.context.registers['r5']))&255}
            pc=self.step(pc)
        raise ValueError('Independent path bound exceeded')


def audit_rom_path(path):
    from ecu_workbench.core import ROMImage
    from ecu_workbench.nc_boot import NCBootDiagnostic,RAM_BASE
    image=ROMImage.from_file(path)
    if image.sha256 not in PROFILES:raise ValueError('No reviewed caller for this ROM hash')
    name,_,stop=PROFILES[image.sha256];literal,consumer=CALLERS[name]
    fixture={'reset_completion_ticks':1,'recessive_bus_ticks':64}
    cpu=NCBootDiagnostic(image,nmi_high=True,hudi_scenario='trst-reset',phi_cycles_per_instruction=1,
        experimental_mcr_bit6=0,hcan_fixture=fixture)
    seeds={};ram={};observed=[];state={'active':False,'done':False};execute=cpu.execute
    def item(value):
        if type(value) is int:return value
        if hasattr(value,'mask'):return (value.value,value.mask)
        return None
    def capture(**kwargs):
        if cpu.pc==literal:
            if state['active'] or state['done']:raise ValueError('Unexpected caller reentry')
            state['active']=True
            for i,value in enumerate(cpu.r):
                v=item(value)
                if v is not None and i!=5:seeds['r'+str(i)]=v
            for reg in ('pr','gbr','vbr','mach','macl'):
                v=item(getattr(cpu,reg))
                if v is not None:seeds[reg]=v
            mask=cpu.known_sr_mask&~1;value=cpu.known_sr_value&mask
            if cpu.t is not None:mask|=1;value|=int(cpu.t)
            seeds['sr']=(value,mask)
            for i,valid in enumerate(cpu.bus.ram_valid):
                if valid:ram[RAM_BASE+i]=(cpu.bus.ram[i],cpu.bus.ram_known_mask[i])
        if cpu.pc==consumer and state['active']:state['active']=False;state['done']=True
        if state['active']:observed.append(cpu.pc)
        return execute(**kwargs)
    cpu.execute=capture;run=cpu.run(100000)
    if not state['done'] or run['interrupt_entries']!=0:raise ValueError('Expected observed path unavailable')
    machine=SymbolicPath(image.data,seeds,ram);result=machine.run(literal,consumer,expected_events=observed)
    if machine.events!=observed or result['r5_low_byte']!=3:raise ValueError('Independent caller path mismatch')
    return {'calibration':name,'rom_sha256':image.sha256,'literal_pc':f'0x{literal:08X}',
        'consumer_pc':f'0x{consumer:08X}','result':result,'all_path_events_matched':True,
        'z3_solver_version':Z3_PIN,'mask_register_entry_values':'unconstrained_symbolic',
        'entry_state':'emulator_snapshot_with_unknown_bits_symbolic_R5_unseeded',
        'branch_choices_forced_from_observation':False,'full_reset_trace_verified':False,
        'hardware_behavior_verified':False,'initialization_verified':False,
        'assumptions':{'reset':'power','nmi_high':True,'hudi_scenario':'trst-reset',
            'phi_cycles_per_instruction':1,'experimental_mcr_bit6':0,'hcan_fixture':fixture}}


def generated_path_audit():
    def code(*words):return b''.join(w.to_bytes(2,'big') for w in words)
    for operand,events in ((0,[0,2,4,6,8,10,12]),(3,[0,2,4,6,12])):
        machine=SymbolicPath(code(0xE503,0xE000|operand,0x3500,0x8901,0xE401,0xA000,0x0009,0x605C))
        machine.run(0,14,expected_events=events)
    machine=SymbolicPath(code(0xE503,0x400B,0xE000,0x0009,0x0009,0x0009,0x605C),{'r0':12})
    machine.run(0,12,expected_events=[0,2,4])
    if machine.number(machine.get(machine.context.registers['pr']))!=6:raise ValueError('Delay call return address differs')
    bad=[lambda:SymbolicPath(code(0xE503,0x3500,0x8901,0x0009,0x0009,0x605C)).run(0,10),
        lambda:SymbolicPath(code(0xE503,0x0009,0x605C)).run(0,4,expected_events=[0]),
        lambda:SymbolicPath(code(0xE503,0x6101,0x605C),{'r0':0xFFFFD002}).run(0,4)]
    for f in bad:
        try:f()
        except ValueError:continue
        raise ValueError('Negative generated path accepted')
    return {'positive_paths':3,'negative_paths_rejected':3,'all_matched':True,
        'unknown_branch_values_selected':False,'observed_outcomes_forced':False}
