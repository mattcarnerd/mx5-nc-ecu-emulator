"""B07 SH-2 register-indirect auto-indexed MOV.B/W/L instructions."""
def execute_pre_post(cpu, op, n, m):
    family = op & 0xF00F
    if family in (0x2004,0x2005,0x2006):
        width=(1,2,4)[family-0x2004]
        old_base=cpu.reg(n)
        old_source=cpu.reg(m)  # Rm==Rn alias stores original source value.
        new_base=(old_base-width)&0xFFFFFFFF
        # SH-2 pre-decrement happens before the addressed memory access.
        cpu.r[n]=new_base
        cpu.bus.write(new_base,width,old_source)
        return True
    if family in (0x6004,0x6005,0x6006):
        width=(1,2,4)[family-0x6004]
        old_base=cpu.reg(m)
        value=cpu.bus.read(old_base,width)
        if width!=4:
            from .nc_boot import sign_extend
            value=sign_extend(value,width*8)&0xFFFFFFFF
        cpu.r[n]=value
        if m!=n:
            cpu.r[m]=(old_base+width)&0xFFFFFFFF
        return True
    return False
