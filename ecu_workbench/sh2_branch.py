"""B10: SH-2E BT/S, BF/S, BRAF, BSRF (software manual 7.2.4-12)."""

def execute_delayed_branch(cpu,op,n,pc,delay_slot):
    from .nc_boot import BootStop,sign_extend
    conditional=(op & 0xFF00) in (0x8D00,0x8F00)
    relative=(op & 0xF0FF) in (0x0023,0x0003)
    if not conditional and not relative:return False,None
    if delay_slot:
        raise BootStop('illegal_delay_slot','Delayed branch in delay slot')
    if conditional:
        if cpu.t is None:raise BootStop('unknown_status','Delayed conditional branch requires known T')
        take=cpu.t if op & 0xFF00==0x8D00 else not cpu.t
        # The SH-2E operation defines a delay slot only when the branch is taken.
        return True,((pc+4+2*sign_extend(op&0xFF,8)) & 0xFFFFFFFF if take else None)
    displacement=cpu.reg(n)
    if op & 0xF0FF==0x0003:cpu.pr=(pc+4)&0xFFFFFFFF
    return True,(pc+4+displacement)&0xFFFFFFFF
