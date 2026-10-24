"""SH-2 logical forms preserve partial bits; only TST changes T."""
from .known_bits import KnownBits

def execute_logic(cpu,op,n,m):
    family=op & 0xF00F
    if family==0x6007:
        bits=cpu.transport_bits(m)
        cpu.r[n]=KnownBits(~bits.value,bits.mask).compact()
        return True
    immediate=op & 0xFF00
    if family in (0x2008,0x2009,0x200A,0x200B):
        left,right=cpu.reg_bits(n),cpu.reg_bits(m)
        dest=n
        operation=family & 3
        alias=n==m
    elif immediate in (0xC800,0xC900,0xCA00,0xCB00):
        left,right=cpu.reg_bits(0),KnownBits.exact(op & 255)
        dest=0
        operation=(op>>8)&3
        alias=False
    else:return False
    if operation==0:
        cpu.t=left.bit_and(right).is_zero()
    elif operation==1:
        cpu.r[dest]=left.bit_and(right).compact()
    elif operation==2:
        cpu.r[dest]=0 if alias else left.bit_xor(right).compact()
    else:
        cpu.r[dest]=left.bit_or(right).compact()
    return True
