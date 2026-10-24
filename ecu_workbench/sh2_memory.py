"""B06 documented SH-2/SH-2E indexed and displacement MOV memory forms.

Instruction values are 16-bit; memory accesses stay big-endian and route
through BootBus so address alignment, unknown data and peripherals fail closed.
"""
def execute_mov_indexed(cpu, op, n, m):
    size_from_code = (1, 2, 4)
    # 0000 nnnn mmmm 0100/0101/0110: MOV.B/W/L Rm,@(R0,Rn)
    if (op & 0xF00F) in (0x0004, 0x0005, 0x0006):
        width = size_from_code[(op & 15) - 4]
        addr = (cpu.reg(0) + cpu.reg(n)) & 0xFFFFFFFF
        cpu.bus.write_cpu_value(addr, width, cpu.transport_bits(m))
        return True
    # 0000 nnnn mmmm 1100/1101/1110: MOV.B/W/L @(R0,Rm),Rn
    if (op & 0xF00F) in (0x000C, 0x000D, 0x000E):
        width = size_from_code[(op & 15) - 12]
        addr = (cpu.reg(0) + cpu.reg(m)) & 0xFFFFFFFF
        cpu.r[n] = cpu.bus.read_cpu_value(addr,width).sign_extend(width).compact()
        return True
    # 0001 nnnn mmmm dddd: MOV.L Rm,@(disp:4,Rn), scaled by 4
    if (op & 0xF000) == 0x1000:
        addr = (cpu.reg(n) + (op & 15)*4) & 0xFFFFFFFF
        cpu.bus.write_cpu_value(addr, 4, cpu.transport_bits(m))
        return True
    # 0101 nnnn mmmm dddd: MOV.L @(disp:4,Rm),Rn, scaled by 4
    if (op & 0xF000) == 0x5000:
        addr = (cpu.reg(m) + (op & 15)*4) & 0xFFFFFFFF
        cpu.r[n] = cpu.bus.read_cpu_value(addr,4).compact()
        return True
    # 1000 0000/0001 nnnn dddd: MOV.B/W R0,@(disp:4,Rn)
    # 1000 0100/0101 mmmm dddd: MOV.B/W @(disp:4,Rm),R0
    family = op & 0xFF00
    if family in (0x8000,0x8100,0x8400,0x8500):
        width = 1 if family in (0x8000,0x8400) else 2
        base_reg = (op >> 4) & 15
        addr = (cpu.reg(base_reg) + (op & 15) * width) & 0xFFFFFFFF
        if family in (0x8000,0x8100):
            cpu.bus.write_cpu_value(addr,width,cpu.transport_bits(0))
        else:
            cpu.r[0] = cpu.bus.read_cpu_value(addr,width).sign_extend(width).compact()
        return True
    return False
