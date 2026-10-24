"""B16 one SH-2E exception path: TRAPA entry and delayed RTE.

Software manual 7.2.48/65; SH7058 hardware manual 6.5.2.
Other exception causes are still explicit diagnostic stops.
"""
from .sh2_control import read_sr,load_sr


def record_exception(cpu,event):
    cpu.exception_events.append(event)
    if len(cpu.exception_events)>100:del cpu.exception_events[0]


def enter_exception(cpu,vector,return_pc,*,source,priority=None):
    sr=read_sr(cpu)  # refuse unknown SR before changing the stack
    cpu.r[15]=(cpu.reg(15)-4)&0xFFFFFFFF
    cpu.bus.write(cpu.r[15],4,sr)
    cpu.r[15]=(cpu.r[15]-4)&0xFFFFFFFF
    cpu.bus.write(cpu.r[15],4,return_pc)
    target=cpu.bus.read((cpu.vbr+4*vector)&0xFFFFFFFF,4)
    if priority is not None:load_sr(cpu,(sr & ~0xF0) | (priority<<4))
    cpu.pc=target
    cpu.exception_entries+=1
    record_exception(cpu,{'event':'entry','source':source,'vector':vector,
        'saved_pc':f'0x{return_pc:08X}','saved_sr':f'0x{sr:08X}',
        'target':f'0x{target:08X}','tick':cpu.clock.ticks})


def execute_exception(cpu,op,pc,delay_slot):
    from .nc_boot import BootStop
    trap=op & 0xFF00==0xC300
    if not trap and op!=0x002B:return False,None
    if delay_slot:raise BootStop('illegal_delay_slot','TRAPA/RTE in delay slot')
    if trap:
        enter_exception(cpu,op & 0xFF,(pc+2)&0xFFFFFFFF,source='TRAPA')
        return True,None
    saved_pc=cpu.bus.read(cpu.reg(15),4)
    cpu.r[15]=(cpu.r[15]+4)&0xFFFFFFFF
    sr=cpu.bus.read(cpu.r[15],4)
    load_sr(cpu,sr)
    cpu.r[15]=(cpu.r[15]+4)&0xFFFFFFFF
    record_exception(cpu,{'event':'return','source':'RTE','target':f'0x{saved_pc:08X}',
                          'restored_sr':f'0x{read_sr(cpu):08X}','tick':cpu.clock.ticks})
    return True,saved_pc
