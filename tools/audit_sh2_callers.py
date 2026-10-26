"""Seed-free mode-literal and observed-path preservation check using SLEIGH.

This checks register writes on a supplied path. It does not independently
choose branches or certify reset control flow, timing or controller behavior.
"""
from tools.audit_sh2_sleigh import PIN,LANGUAGE,PROFILES

SAFE_OPS=frozenset(('IMARK','COPY','INT_ADD','INT_SUB','INT_AND','INT_OR','INT_XOR',
    'INT_NEGATE','INT_LEFT','INT_RIGHT','INT_SEXT','INT_ZEXT','INT_EQUAL','INT_LESS',
    'INT_MULT','SUBPIECE','LOAD','STORE','CBRANCH','BRANCH','BRANCHIND','CALL','CALLIND','RETURN'))

def prove_mode_path(data,path,consumer,expected=3):
    import pypcode
    if pypcode.__version__!=PIN:raise ValueError('Pinned audit dependency required')
    if not path or len(path)>10000:raise ValueError('Invalid bounded path')
    context=pypcode.Context(LANGUAGE);r5=context.registers['r5']
    def ops(pc,window=4):
        if type(pc) is not int or pc<0 or pc%2 or pc+2>len(data):raise ValueError('Invalid instruction address')
        tx=context.translate(data[pc:pc+window],base_address=pc,max_instructions=1)
        if not tx.ops or tx.ops[0].opcode.name!='IMARK':raise ValueError('Missing decoded instruction')
        if tx.ops[0].inputs[0].offset!=pc:raise ValueError('Lift origin mismatch')
        return tx.ops
    def overlaps(node):
        return (node is not None and node.space.name=='register' and
            node.offset<r5.offset+r5.size and node.offset+node.size>r5.offset)
    literal=[o for o in ops(path[0],2) if o.opcode.name!='IMARK']
    if len(literal)!=1:raise ValueError('Literal has additional effects')
    op=literal[0]
    if (op.opcode.name!='COPY' or op.output is None or op.output.space.name!='register' or
        op.output.offset!=r5.offset or op.output.size!=4 or len(op.inputs)!=1 or
        op.inputs[0].space.name!='const' or op.inputs[0].offset!=expected):
        raise ValueError('Caller must independently assign the reviewed full-register literal')
    inspected=0
    for pc in path[1:]:
        for op in ops(pc):
            if op.opcode.name not in SAFE_OPS:raise ValueError('Opaque/unsupported path operation')
            if overlaps(op.output):raise ValueError('Intervening mode-register write, including possible delay slot')
            if op.opcode.name in ('LOAD','STORE') and op.inputs[0].getSpaceFromConst().name!='ram':
                raise ValueError('Unexpected memory address space')
            if op.output is not None and op.output.space.name not in ('register','unique'):
                raise ValueError('Unreviewed output address space')
            inspected+=1
    use=[o for o in ops(consumer,2) if o.opcode.name!='IMARK']
    if (len(use)!=1 or use[0].opcode.name!='INT_ZEXT' or
        use[0].inputs[0].space.name!='register' or use[0].inputs[0].offset!=r5.offset+3 or
        use[0].inputs[0].size!=1 or use[0].output.getRegisterName()!='r0'):
        raise ValueError('Consumer is not the reviewed R5 low-byte extraction')
    return {'literal_value':expected,'entry_register_seeds_required':False,
        'observed_instruction_events':len(path),'nonliteral_pcode_operations_inspected':inspected,
        'intervening_mode_writes':0,'delay_slot_effects_included':True,
        'consumer_low_byte':expected&255,'branch_decisions_independently_verified':False}


def generated_caller_audit():
    def data(words):
        return b''.join(x.to_bytes(2,'big') for x in words)
    # Generated code, unrelated to any copied OEM instruction stream.
    positives=[(data((0xE503,0x0009,0x605C)),[0,2],4),
        (data((0xE503,0xE407,0x7441,0x605C)),[0,2,4],6),
        (data((0xE503,0xA001,0x0009,0x0009,0x605C)),[0,2,4],8)]
    for raw,path,end in positives:prove_mode_path(raw,path,end)
    negatives=[(data((0xE502,0x0009,0x605C)),[0,2],4),
        (data((0xE503,0xE504,0x605C)),[0,2],4),
        (data((0xE503,0xA001,0xE504,0x0009,0x605C)),[0,2,4],8),
        (data((0xE503,0x001B,0x605C)),[0,2],4)]
    for raw,path,end in negatives:
        try:prove_mode_path(raw,path,end)
        except ValueError:continue
        raise ValueError('Negative generated caller case was accepted')
    return {'positive_paths':len(positives),'negative_paths_rejected':len(negatives),
        'all_matched':True,'full_control_flow_verified':False}

CALLERS={
 'LF9VEB':(0x1E2,0xE64),'LFNPEA':(0x1E2,0xE64),'LF4XEC':(0x21A,0xCB4),
}

def audit_rom_caller(path):
    from ecu_workbench.core import ROMImage
    from ecu_workbench.nc_boot import NCBootDiagnostic
    image=ROMImage.from_file(path)
    if image.sha256 not in PROFILES:raise ValueError('No reviewed caller for this ROM hash')
    name,_,stop=PROFILES[image.sha256];literal,consumer=CALLERS[name]
    fixture={'reset_completion_ticks':1,'recessive_bus_ticks':64}
    cpu=NCBootDiagnostic(image,nmi_high=True,hudi_scenario='trst-reset',phi_cycles_per_instruction=1,
        experimental_mcr_bit6=0,hcan_fixture=fixture)
    records=[];state={'recording':False,'done':False,'consumer_value':None};execute=cpu.execute
    def capture(**kwargs):
        if cpu.pc==literal:
            if kwargs.get('delay_slot') or state['recording'] or state['done']:raise ValueError('Unexpected literal reentry/delay slot')
            state['recording']=True
        if cpu.pc==consumer and state['recording']:
            state['recording']=False;state['done']=True;state['consumer_value']=cpu.r[5]
        if state['recording']:
            if len(records)>=10000:raise ValueError('Caller path bound exceeded')
            records.append(cpu.pc)
        return execute(**kwargs)
    cpu.execute=capture;run=cpu.run(100000)
    if not state['done'] or state['consumer_value']!=3 or run['interrupt_entries']!=0:
        raise ValueError('Expected zero-interrupt observed caller path not reached')
    if run['next_dependency']['instruction_pc']!=f'0x{stop:08X}':raise ValueError('Unexpected terminal stop')
    proof=prove_mode_path(image.data,records,consumer)
    return {'calibration':name,'rom_sha256':image.sha256,'literal_pc':f'0x{literal:08X}',
        'consumer_pc':f'0x{consumer:08X}','proof':proof,
        'path_source':'local_emulator_observed_not_independent_reset_trace',
        'assumptions':{'reset':'power','nmi_high':True,'hudi_scenario':'trst-reset',
            'phi_cycles_per_instruction':1,'experimental_mcr_bit6':0,'hcan_fixture':fixture},
        'hardware_behavior_verified':False,'initialization_verified':False}
