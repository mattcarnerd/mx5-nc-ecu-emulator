"""Bounded SH7058 on-chip arbitration: ITI, ATU IMI1A and ADC ADI0, Rev.3 table7.3.

Highest configured priority wins; supported equal-priority sources use table
order. Entry does not acknowledge a held module flag. Other source families
remain outside this bounded controller.
"""
from .sh2_exception import enter_exception

ITI_VECTOR=224
IPRL_ADDRESS=0xFFFFED16
IMI1A_VECTOR=96
IMI1B_VECTOR=97
IPRD_ADDRESS=0xFFFFED06
OVI1A_VECTOR=104
IPRE_ADDRESS=0xFFFFED08
ADI0_VECTOR=190
IPRJ_ADDRESS=0xFFFFED12


def enabled_flag_request(flag,enable,bit):
    if flag is not None and not flag&bit:return False
    if enable is not None and not enable&bit:return False
    if flag is None or enable is None:return None
    return True


def routed_requests(cpu):
    from .atu import TSR,TIER
    t=cpu.bus.atu
    requests=[
        ('IMI1A',IMI1A_VECTOR,IPRD_ADDRESS,4,enabled_flag_request(t.regs[TSR],t.regs[TIER],1),True),
        ('IMI1B',IMI1B_VECTOR,IPRD_ADDRESS,4,enabled_flag_request(t.regs[TSR],t.regs[TIER],2),True),
        ('OVI1A',OVI1A_VECTOR,IPRE_ADDRESS,12,enabled_flag_request(t.regs[TSR],t.regs[TIER],0x100),True),
        ('ADI0',ADI0_VECTOR,IPRJ_ADDRESS,8,cpu.bus.adc.interrupt_pending,True),
        ('ITI',ITI_VECTOR,IPRL_ADDRESS,4,cpu.interval_request,True),
    ]
    if t.counter0.enabled:
        requests.extend([
            ('ATU0_interval',80,0xFFFFED04,4,t.counter0.interval_pending,False),
            ('OVI0',92,IPRD_ADDRESS,8,t.counter0.overflow_pending,False)])
    return requests


def service_interrupt_requests(cpu):
    from .nc_boot import BootStop
    if cpu._pending_target is not None or cpu._interrupt_inhibit:return False
    mask_known=cpu.known_sr_mask & 0xF0==0xF0
    mask=(cpu.known_sr_value>>4)&15
    if mask_known and mask==15:return False
    requests=routed_requests(cpu)
    if all(request is False for _,_,_,_,request,_ in requests):return False
    cpu.coverage.current_pc=None
    cpu._active_instruction=None
    cpu._fetch_pc=cpu.pc
    candidates=[]
    for name,vector,address,shift,request,supported in requests:
        if request is False:continue
        raw=cpu.bus.ipr[address]
        if raw is None:
            raise BootStop('unknown_peripheral_reset_state',f'Priority unknown for possible {name} request')
        priority=(raw>>shift)&15
        if priority==0:continue
        if not mask_known:raise BootStop('unknown_status',f'SR interrupt mask unknown for possible {name}')
        if priority<=mask:continue
        if request is None:
            raise BootStop('unknown_peripheral_reset_state',f'{name} flag/enable state unknown; no request assumed')
        candidates.append((priority,vector,name,supported))
    if not candidates:return False
    priority,vector,name,supported=min(candidates,key=lambda c:(-c[0],c[1]))
    if not supported:raise BootStop('unsupported_interrupt_source',f'{name} CPU route outside bounded subset')
    enter_exception(cpu,vector,cpu.pc,source=name,priority=priority)
    cpu.interrupt_entries+=1
    return True


def service_interval_request(cpu):
    """Compatibility entry point; now arbitrates all supported sources."""
    return service_interrupt_requests(cpu)
