"""B12: SH-2E SR/GBR/VBR/PR transfers, including stack forms.

Renesas SH-2E software manual 2.2, 7.2.26/27/58/59. SH7058 has
SR M/Q/I/S/T bits only; reserved bits read zero. No SH-4 privilege model.
Unknown source values stop before a synthetic value can reach memory.
"""
SR_MASK = 0x3F3


def read_sr(cpu):
    from .nc_boot import BootStop
    mask = cpu.known_sr_mask & ~1
    value = cpu.known_sr_value & ~1
    if cpu.t is not None:
        mask |= 1
        value |= int(cpu.t)
    if mask & SR_MASK != SR_MASK:
        raise BootStop('unknown_status', 'SR contains unknown implemented bits')
    return value & SR_MASK


def load_sr(cpu, value):
    cpu.known_sr_value = value & SR_MASK
    cpu.known_sr_mask = SR_MASK
    cpu.t = bool(value & 1)


def execute_control(cpu, op, n):
    from .nc_boot import BootStop
    key = op & 0xF0FF
    stores = {0x0002:'sr', 0x0012:'gbr', 0x0022:'vbr', 0x002A:'pr',
              0x4003:'sr', 0x4013:'gbr', 0x4023:'vbr', 0x4022:'pr'}
    loads = {0x400E:'sr', 0x401E:'gbr', 0x402E:'vbr', 0x402A:'pr',
             0x4007:'sr', 0x4017:'gbr', 0x4027:'vbr', 0x4026:'pr'}
    if key in stores:
        name = stores[key]
        value = read_sr(cpu) if name == 'sr' else getattr(cpu, name)
        if value is None:
            raise BootStop('unknown_register', f'{name.upper()} value is unknown')
        if key & 0x4000:
            address = (cpu.reg(n) - 4) & 0xFFFFFFFF
            cpu.r[n] = address
            cpu.bus.write(address, 4, value)
        else:
            cpu.r[n] = value
        cpu._interrupt_inhibit=1
        return True
    if key in loads:
        name = loads[key]
        memory = (key & 0xF) in (6, 7)
        address = cpu.reg(n)
        value = cpu.bus.read(address, 4) if memory else address
        if name == 'sr':
            load_sr(cpu, value)
        else:
            setattr(cpu, name, value)
        if memory:
            cpu.r[n] = (address + 4) & 0xFFFFFFFF
        cpu._interrupt_inhibit=1
        return True
    if op in (0x0008, 0x0018):  # CLRT / SETT
        cpu.t = op == 0x0018
        return True
    return False
