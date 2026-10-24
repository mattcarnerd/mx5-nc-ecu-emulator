"""B21: one explicitly supplied WDT ITI source; no timer generation.

SH7058 Rev.3 table 7.3: ITI vector224, IPRL[7:4]. A module request
is held until the caller deasserts it; acceptance does not clear its flag.
"""
from .sh2_exception import enter_exception

ITI_VECTOR=224
IPRL_ADDRESS=0xFFFFED16


def service_interval_request(cpu):
    from .nc_boot import BootStop
    if not cpu.interval_request or cpu._pending_target is not None or cpu._interrupt_inhibit:
        return False
    cpu._active_instruction=None
    cpu._fetch_pc=cpu.pc
    raw=cpu.bus.ipr[IPRL_ADDRESS]
    mask_known=cpu.known_sr_mask & 0xF0==0xF0
    mask=(cpu.known_sr_value>>4)&15
    if mask_known and mask==15:return False
    if raw is None:
        raise BootStop('unknown_peripheral_reset_state','IPRL priority unknown for pending ITI')
    priority=(raw>>4)&15
    if priority==0:return False
    if not mask_known:raise BootStop('unknown_status','SR interrupt mask unknown for pending ITI')
    if priority<=mask:return False
    # Entry faults are not attributed to the previously fetched instruction.
    cpu._active_instruction=None
    cpu._fetch_pc=cpu.pc
    enter_exception(cpu,ITI_VECTOR,cpu.pc,source='ITI',priority=priority)
    cpu.interrupt_entries+=1
    return True
