"""B09 SH-2 CMP/EQ, HS, GE, ADDC, SUBC with known T-bit semantics.

SH-2 T=1 after ADDC indicates carry out, after SUBC indicates a borrow.
Signed GE uses two's-complement comparison. Unknown incoming T may not
be silently treated as zero; stop without modifying register state.
"""
def execute_compare_carry(cpu,op,n,m):
    if op & 0xF0FF in (0x4015,0x4011):  # CMP/PL, CMP/PZ; Rev2 section7.2.15
        # Signed PL excludes zero; PZ includes zero. Both reject negative values.
        value=cpu.reg(n)  # unknown operand must stop before changing T
        cpu.t=(0 < value < 0x80000000) if op & 0xF0FF == 0x4015 else value < 0x80000000
        return True
    if op & 0xFF00 == 0x8800:  # CMP/EQ #imm,R0: sign-extended imm8
        from .nc_boot import sign_extend
        cpu.t=cpu.reg(0)==(sign_extend(op & 0xFF,8) & 0xFFFFFFFF)
        return True
    family=op & 0xF00F
    if family not in (0x3000,0x3002,0x3003,0x3006,0x300E,0x300A):
        return False
    left=cpu.reg(n)
    right=cpu.reg(m)
    if family==0x3000:  # CMP/EQ Rm,Rn
        cpu.t=left==right
    elif family==0x3002:  # CMP/HS Rm,Rn (unsigned >=)
        cpu.t=left>=right
    elif family==0x3006:  # CMP/HI Rm,Rn (unsigned strictly greater)
        cpu.t=left>right
    elif family==0x3003:  # CMP/GE Rm,Rn (signed >=)
        from .nc_boot import sign_extend
        cpu.t=sign_extend(left,32)>=sign_extend(right,32)
    else:
        if cpu.t is None:
            from .nc_boot import BootStop
            raise BootStop("unknown_status","ADDC/SUBC requires a known incoming T-bit")
        borrow_or_carry=int(cpu.t)
        if family==0x300E:  # ADDC Rm,Rn
            total=left+right+borrow_or_carry
            cpu.r[n]=total&0xFFFFFFFF
            cpu.t=total>0xFFFFFFFF
        else:  # SUBC Rm,Rn; T indicates an unsigned borrow
            total=left-right-borrow_or_carry
            cpu.r[n]=total&0xFFFFFFFF
            cpu.t=total<0
    return True
