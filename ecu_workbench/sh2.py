"""Limited SH-2 big-endian instruction subset for research only.

Unsupported instructions or addresses stop rather than guessing. NOT an SH7058
ECU emulator: no ECU RAM, peripherals, interrupts, exceptions or floating point.
"""
from __future__ import annotations
from dataclasses import dataclass
from .core import ROMImage

class Halt(Exception):
    pass

def sx(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value

@dataclass
class State:
    pc: int
    r: list[int]
    pr: int=0
    t: bool=False
    count: int=0

class SH2Subset:
    def __init__(self, rom: ROMImage, pc: int, base_address: int = 0):
        self.rom = rom
        self.base = base_address
        self.state = State(pc,[0]*16)
        self.trace = []
        self.in_delay = False

    def read16(self, address: int) -> int:
        off = address - self.base
        if off < 0 or off + 2 > self.rom.size or off & 1:
            raise Halt(f"Unmapped or unaligned address: 0x{address:X}")
        return int.from_bytes(self.rom.data[off:off+2],"big")

    def read32(self, address: int) -> int:
        off = address - self.base
        if off < 0 or off + 4 > self.rom.size or off & 3:
            raise Halt(f"Unmapped or unaligned 32-bit address: 0x{address:X}")
        return int.from_bytes(self.rom.data[off:off+4],"big")

    def delay_to(self, destination: int):
        if self.in_delay:
            raise Halt("Nested branch in delay slot")
        self.in_delay = True
        try:
            self.step()
        finally:
            self.in_delay = False
        self.state.pc = destination & 0xFFFFFFFF

    def step(self):
        s = self.state
        pc = s.pc
        op = self.read16(pc)
        s.pc = pc + 2
        s.count += 1
        self.trace.append({"pc":f"0x{pc:08X}","opcode":f"{op:04X}"})
        n, m = (op>>8)&15, (op>>4)&15
        if op == 0x0009: return
        if (op & 0xF000) == 0xE000:
            s.r[n] = sx(op & 255,8) & 0xFFFFFFFF; return
        if (op & 0xF000) == 0x7000:
            s.r[n] = (s.r[n] + sx(op&255,8)) & 0xFFFFFFFF; return
        if (op & 0xF00F) == 0x6003:
            s.r[n] = s.r[m]; return
        if (op & 0xF00F) == 0x3000:
            s.t = s.r[n] == s.r[m]; return
        if (op & 0xFF00) == 0x8800:
            s.t = s.r[0] == (sx(op&255,8) & 0xFFFFFFFF); return
        if (op & 0xF0FF) == 0x4010:
            s.r[n] = (s.r[n]-1)&0xFFFFFFFF; s.t = s.r[n] == 0; return
        if (op & 0xF000) == 0x9000:
            s.r[n] = sx(self.read16(pc+4+2*(op&255)),16)&0xFFFFFFFF; return
        if (op & 0xF000) == 0xD000:
            s.r[n] = self.read32(((pc+4)&~3)+4*(op&255)); return
        if (op & 0xFF00) == 0x8900:
            if s.t: s.pc = pc+4+2*sx(op&255,8)
            return
        if (op & 0xFF00) == 0x8B00:
            if not s.t: s.pc = pc+4+2*sx(op&255,8)
            return
        if (op & 0xF000) == 0xA000:
            self.delay_to(pc+4+2*sx(op&0xFFF,12)); return
        if (op & 0xF0FF) == 0x402B:
            self.delay_to(s.r[n]); return
        if op == 0x000B:
            self.delay_to(s.pr); return
        if (op & 0xF0FF) == 0x0029:
            s.r[n] = int(s.t); return
        raise Halt(f"Unsupported SH-2 opcode 0x{op:04X} at 0x{pc:08X}")

    def run(self, max_instructions: int=100) -> dict:
        if not 1 <= max_instructions <= 100000:
            raise ValueError("max_instructions must be between 1 and 100000")
        err = None
        for _ in range(max_instructions):
            try: self.step()
            except Halt as exc:
                err=str(exc)
                break
        s=self.state
        return {
            "architecture":"SuperH SH-2 integer subset (partial)",
            "input_rom_sha256":self.rom.sha256,
            "load_address":f"0x{self.base:X}",
            "pc":f"0x{s.pc:08X}",
            "registers":{f"R{i}":f"0x{r:08X}" for i,r in enumerate(s.r)},
            "pr":f"0x{s.pr:08X}", "t":s.t,
            "instructions":s.count,
            "status":"unsupported/unmapped" if err else "step_limit",
            "error":err, "trace":self.trace[:500],
            "warning":"Not a complete SH-2E or ECU emulation."
        }
