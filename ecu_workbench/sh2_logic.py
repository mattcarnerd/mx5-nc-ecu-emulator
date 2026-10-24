"""B08 SH-2 register AND/OR/XOR/TST and immediate R0 forms.

Only TST modifies the T flag. Other logical instructions preserve the flag,
even when its prior power-on state is unknown. GBR-memory immediate forms are
deferred until a verified known GBR state exists.
"""
def execute_logic(cpu,op,n,m):
    family=op & 0xF00F
    if family in (0x2008,0x2009,0x200A,0x200B):
        left=cpu.reg(n)
        right=cpu.reg(m)
        if family==0x2008:
            cpu.t=(left & right)==0
        elif family==0x2009:
            cpu.r[n]=(left & right)&0xFFFFFFFF
        elif family==0x200A:
            cpu.r[n]=(left ^ right)&0xFFFFFFFF
        else:
            cpu.r[n]=(left | right)&0xFFFFFFFF
        return True
    immediate=op & 0xFF00
    if immediate in (0xC800,0xC900,0xCA00,0xCB00):
        left=cpu.reg(0)
        right=op & 255  # SH2 logical immediate is zero-extended
        if immediate==0xC800:
            cpu.t=(left & right)==0
        elif immediate==0xC900:
            cpu.r[0]=left & right
        elif immediate==0xCA00:
            cpu.r[0]=(left ^ right)&0xFFFFFFFF
        else:
            cpu.r[0]=(left | right)&0xFFFFFFFF
        return True
    return False
