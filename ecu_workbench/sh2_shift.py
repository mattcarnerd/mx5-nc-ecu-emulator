"""B11: SH-2E fixed shifts and rotations; 32-bit wrap, exact T rules."""

def execute_shift(cpu,op,n):
    key=op & 0xF0FF
    multi={0x4008:(2,True),0x4018:(8,True),0x4028:(16,True),
           0x4009:(2,False),0x4019:(8,False),0x4029:(16,False)}
    single=(0x4000,0x4001,0x4020,0x4021,0x4004,0x4005,0x4024,0x4025)
    if key not in multi and key not in single: return False
    value=cpu.reg(n)
    if key in multi:
        count,left=multi[key]
        cpu.r[n]=((value<<count) if left else value>>count) & 0xFFFFFFFF
        return True  # multi-bit shifts do not alter T
    if key in (0x4024,0x4025) and cpu.t is None:
        from .nc_boot import BootStop
        raise BootStop('unknown_status','Carry rotate requires known T')
    left=key in (0x4000,0x4020,0x4004,0x4024)
    outgoing=(value>>31) if left else value&1
    shifted=(value<<1)&0xFFFFFFFF if left else value>>1
    if key==0x4021: shifted |= value & 0x80000000
    elif key==0x4004: shifted |= outgoing
    elif key==0x4005: shifted |= outgoing<<31
    elif key==0x4024: shifted |= int(cpu.t)
    elif key==0x4025: shifted |= int(cpu.t)<<31
    cpu.r[n]=shifted
    cpu.t=bool(outgoing)
    return True
