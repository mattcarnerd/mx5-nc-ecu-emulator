"""First SH7058 NC ROM *reset diagnostic*, not a complete ECU emulator.

The real instruction stream is executed from its reset vector, with fail-closed
memory/peripheral handling. Uninitialised CPU registers are NOT treated as zero.
SH7058 hardware manual (Rev 3.00): sections 6.1.3 and 9.1.5.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from typing import Optional
from .core import ROMImage
from .boot_reporting import explain_stop
from .port_d import PortD, PDDR_ADDRESS, PDPR_ADDRESS
from .port_e import PortE, PEDR_ADDRESS
from .port_f import PortF, PFDR_ADDRESS
from .peripheral_router import PeripheralRouter

ROM_BASE, ROM_LIMIT = 0x00000000, 0x00100000
RAM_BASE, RAM_LIMIT = 0xFFFF0000, 0xFFFFC000
PERIPHERAL_BASE, PERIPHERAL_LIMIT = 0xFFFFC000, 0x100000000

# Renesas SH7058 Rev 3.00, sections 22.3.1-22.3.2, Tables 22.3/22.4.
PBDR_ADDRESS = 0xFFFFF738
PBIOR_ADDRESS = 0xFFFFF730
PBPR_ADDRESS = 0xFFFFF782  # physical Port B pin levels, 16-bit read-only
PCDR_ADDRESS = 0xFFFFF73E  # Renesas SH7058 Rev 3.00, Table 22.5
PCIOR_ADDRESS = 0xFFFFF73A
PC_VALID_MASK = 0x001F  # PC4..PC0; remaining 11 bits reserved

class BootStop(Exception):
    def __init__(self, kind: str, detail: str, *, address: Optional[int] = None, width: Optional[int] = None, access: Optional[str] = None, value: Optional[int] = None):
        self.kind, self.detail = kind, detail
        self.address, self.width, self.access, self.value = address, width, access, value
        super().__init__(detail)
    def report(self):
        r = {'reason': self.kind, 'detail': self.detail}
        for k in ('address','width','access','value'):
            v = getattr(self,k)
            if v is not None: r[k] = f'0x{v:08X}' if k in ('address','value') else v
        return r

def sign_extend(n: int, bits: int) -> int:
    return n - (1 << bits) if n & (1 << (bits-1)) else n

@dataclass(frozen=True)
class ResetVectors:
    power_pc: int
    power_sp: int
    manual_pc: int
    manual_sp: int
    @classmethod
    def read(cls, data: bytes) -> 'ResetVectors':
        if len(data) < 16: raise BootStop('invalid_vectors','ROM is shorter than the 16-byte reset table')
        return cls(*(int.from_bytes(data[n:n+4], 'big') for n in (0, 4, 8, 12)))
    def as_dict(self):
        return {k:f'0x{getattr(self,k):08X}' for k in ('power_pc','power_sp','manual_pc','manual_sp')}

# SH7058 Rev. 3.00 hardware manual, Table 9.2, page 144.
BSC_REGISTERS = {
    0xFFFFEC20: ('BCR1', 0x000F),
    0xFFFFEC22: ('BCR2', 0xFFFF),
    0xFFFFEC24: ('WCR', 0x7777),
    0xFFFFEC26: ('RAMER', 0x0000),
}

# SH7058 hardware manual 21.2: 16-bit PFC config latches. These only store
# configuration; effects on external pins/ATU-II are *not* simulated.
PFC_REGISTERS = {
    0xFFFFF720: ('PAIOR',0), 0xFFFFF722: ('PACRH',0), 0xFFFFF724: ('PACRL',0),
    0xFFFFF730: ('PBIOR',0), 0xFFFFF732: ('PBCRH',0), 0xFFFFF734: ('PBCRL',0),
    0xFFFFF736: ('PBIR',0), 0xFFFFF73A: ('PCIOR',0), 0xFFFFF73C: ('PCCR',0),
    0xFFFFF740: ('PDIOR',0), 0xFFFFF742: ('PDCRH',0), 0xFFFFF744: ('PDCRL',0),
    0xFFFFF750: ('PEIOR',0), 0xFFFFF752: ('PECR',0),
    0xFFFFF748: ('PFIOR',0), 0xFFFFF74A: ('PFCRH',0x0015), 0xFFFFF74C: ('PFCRL',0x5000),
    0xFFFFF760: ('PGIOR',0), 0xFFFFF762: ('PGCR',0),
    0xFFFFF728: ('PHIOR',0), 0xFFFFF72A: ('PHCR',0),
    0xFFFFF766: ('PJIOR',0), 0xFFFFF768: ('PJCRH',0), 0xFFFFF76A: ('PJCRL',0),
    0xFFFFF770: ('PKIOR',0), 0xFFFFF772: ('PKCRH',0), 0xFFFFF774: ('PKCRL',0),
    0xFFFFF776: ('PKIR',0), 0xFFFFF756: ('PLIOR',0), 0xFFFFF758: ('PLCRH',0),
    0xFFFFF75A: ('PLCRL',0), 0xFFFFF75C: ('PLIR',0),
}

class BootBus:
    def __init__(self, image: ROMImage, *, power_on: bool=True, nmi_high: Optional[bool]=None,
                 port_b_pin_values: Optional[int]=None, port_b_pin_known_mask: int=0xFFFF,
                 port_c_pin_values: Optional[int]=None, port_c_pin_known_mask: int=PC_VALID_MASK,
                 port_d_pin_values: Optional[int]=None, port_d_pin_known_mask: int=0xFFFF,
                 port_e_pin_values: Optional[int]=None, port_e_pin_known_mask: int=0xFFFF,
                 port_f_pin_values: Optional[int]=None, port_f_pin_known_mask: int=0xFFFF):
        self.image = image
        self.bsc = {addr:(reset if power_on else None) for addr, (_,reset) in BSC_REGISTERS.items()}
        self.peripheral_trace=[]
        # SYSCR2 clock/source control: write word with 0x3C key, read byte.
        # SH7058 manual sect. 5.1.3 & 5.2.3: power-on initial 0x01.
        self.syscr2 = 0x01 if power_on else None
        # SH7058 section 7.1.4: IPRx power-on reset to 0; ICR bit 15
        # reads the physical NMI pin state and is not faked by this model.
        self.ipr = {0xFFFFED00 + 2*i: (0 if power_on else None) for i in range(12)}
        self.icr_control = 0 if power_on else None
        self.nmi_high = nmi_high  # explicit simulated physical input (unknown by default)
        self.pfc = {addr:(default if power_on else None) for addr,(_,default) in PFC_REGISTERS.items()}
        # PADR output data latch; no external pin driver/input model yet.
        self.padr = 0 if power_on else None
        # PBDR is a 16-bit stored output latch, not the external pin register.
        # Power-on reset clears it; manual reset need not define its state.
        # Track known bytes so a manual-reset byte write does not falsely
        # initialise the untouched half of the register.
        self.pbdr = 0
        self.pbdr_known_mask = 0xFFFF if power_on else 0
        self.set_port_b_pin_levels(port_b_pin_values, port_b_pin_known_mask)
        self.pcdr = 0
        self.pcdr_known_mask = PC_VALID_MASK if power_on else 0
        self.set_port_c_pin_levels(port_c_pin_values, port_c_pin_known_mask)
        self.port_d = PortD(power_on=power_on, pfc=self.pfc, trace=self.peripheral_trace,
                            stop_type=BootStop, pin_values=port_d_pin_values,
                            pin_known_mask=port_d_pin_known_mask)
        self.port_e = PortE(power_on=power_on, pfc=self.pfc, trace=self.peripheral_trace,
                            stop_type=BootStop, pin_values=port_e_pin_values,
                            pin_known_mask=port_e_pin_known_mask)
        self.port_f = PortF(power_on=power_on, pfc=self.pfc, trace=self.peripheral_trace,
                            stop_type=BootStop, pin_values=port_f_pin_values,
                            pin_known_mask=port_f_pin_known_mask)
        # Register only known GPIO addresses; the original handlers retain
        # width, reset, reserved-bit and physical-input checks.
        self.port_router = PeripheralRouter()
        self.port_router.add_word(name='PBDR',base=PBDR_ADDRESS,
                                  read=self._pbdr_read,write=self._pbdr_write)
        self.port_router.add_word(name='PBPR',base=PBPR_ADDRESS,
                                  read=self._pbpr_read,write=self._pbpr_write)
        self.port_router.add_word(name='PCDR',base=PCDR_ADDRESS,
                                  read=self._pcdr_read,write=self._pcdr_write)
        self.port_router.add_word(name='PDDR',base=PDDR_ADDRESS,
                                  read=self.port_d.read,write=self.port_d.write)
        self.port_router.add_word(name='PDPR',base=PDPR_ADDRESS,
                                  read=self.port_d.read,write=self.port_d.write)
        self.port_router.add_word(name='PEDR',base=PEDR_ADDRESS,
                                  read=self.port_e.read,write=self.port_e.write)
        self.port_router.add_word(name='PFDR',base=PFDR_ADDRESS,
                                  read=self.port_f.read,write=self.port_f.write)
        # RAM bytes have no predetermined initial value after a reset.
        self.ram = bytearray(RAM_LIMIT-RAM_BASE)
        self.ram_valid = bytearray(RAM_LIMIT-RAM_BASE)
    def _region(self, a: int, width: int, access: str, value=None):
        if not 0 <= a < 2**32 or a+width > 2**32:
            raise BootStop('unmapped_memory',f'Address out of 32-bit range: 0x{a:X}',address=a,width=width,access=access)
        if a % width:
            raise BootStop('unaligned_access',f'Unaligned {width}-byte access at 0x{a:X}',address=a,width=width,access=access)
        if ROM_BASE <= a and a+width <= len(self.image.data):
            if access == 'write':
                raise BootStop('rom_write',f'Attempted write to flash 0x{a:X}',address=a,width=width,access=access,value=value)
            return 'rom',a
        if RAM_BASE <= a and a+width <= RAM_LIMIT:
            return 'ram',a-RAM_BASE
        if PERIPHERAL_BASE <= a and a+width <= PERIPHERAL_LIMIT:
            return 'peripheral',a
        raise BootStop('unmapped_memory',f'Unmapped {access} at 0x{a:08X}',address=a,width=width,access=access,value=value)
    @staticmethod
    def _pbdr_mask(a: int, width: int) -> int:
        # SH7058 section 22.3.1 specifies 8/16-bit accesses. Big endian:
        # 0xFFFFF738 is PB15..PB8, 0xFFFFF739 is PB7..PB0.
        if width == 2 and a == PBDR_ADDRESS:
            return 0xFFFF
        if width == 1 and a == PBDR_ADDRESS:
            return 0xFF00
        if width == 1 and a == PBDR_ADDRESS + 1:
            return 0x00FF
        raise BootStop('unsupported_access_size',
                       f'PBDR permits only aligned 8/16-bit access at 0x{a:08X}',
                       address=a, width=width)

    def set_port_b_pin_levels(self, values: Optional[int], known_mask: int = 0xFFFF) -> None:
        """Explicit 16-bit physical pin levels; bits absent from mask are unknown."""
        if type(known_mask) is not int or not 0 <= known_mask <= 0xFFFF:
            raise ValueError("port_b_pin_known_mask must be a 16-bit integer")
        if values is not None and (type(values) is not int or not 0 <= values <= 0xFFFF):
            raise ValueError("port_b_pin_values must be None or a 16-bit integer")
        self.port_b_pin_values = 0 if values is None else values
        self.port_b_pin_known_mask = 0 if values is None else known_mask

    @staticmethod
    def _port_b_mask(address: int, width: int, base_address: int, name: str) -> int:
        if width == 2 and address == base_address: return 0xFFFF
        if width == 1 and address == base_address: return 0xFF00
        if width == 1 and address == base_address + 1: return 0x00FF
        raise BootStop('unsupported_access_size',
                       f'{name} permits only aligned 8/16-bit accesses at 0x{address:08X}',
                       address=address, width=width)

    def _port_b_physical_bits(self, mask: int, address: int, width: int) -> int:
        if self.port_b_pin_known_mask & mask != mask:
            missing = mask & ~self.port_b_pin_known_mask
            raise BootStop('missing_input',
                           f'Unknown physical Port B pin levels for bits 0x{missing:04X}',
                           address=address, width=width, access='read')
        return self.port_b_pin_values & mask

    def _pbpr_read(self, address: int, width: int) -> int:
        # SH7058 Rev 3.00 section 22.3.3: PBPR is always physical pin
        # levels, even for outputs. Do not derive them from PBDR.
        mask = self._port_b_mask(address, width, PBPR_ADDRESS, 'PBPR')
        physical = self._port_b_physical_bits(mask, address, width)
        value = physical >> (8 if mask == 0xFF00 else 0)
        self.peripheral_trace.append({'register': 'PBPR', 'access': 'read',
                                      'value': value, 'width': width,
                                      'scope': 'explicit_external_pin_levels'})
        return value

    def _pbpr_write(self, address: int, width: int, value: int) -> None:
        self._port_b_mask(address, width, PBPR_ADDRESS, 'PBPR')
        raise BootStop('read_only_peripheral',
                       'PBPR always samples physical pins and cannot be written',
                       address=address, width=width, access='write', value=value)

    def _pbdr_read(self, address: int, width: int) -> int:
        mask = self._pbdr_mask(address, width)
        directions = self.pfc[PBIOR_ADDRESS]
        if directions is None:
            raise BootStop('unknown_peripheral_reset_state',
                           'PBIOR preserved state is unknown; cannot interpret PBDR read',
                           address=address, width=width, access='read')
        # SH7058 Table 22.4: PBIOR=0 reads physical input; PBIOR=1
        # returns the data latch. Other mux behaviour isn't claimed.
        external_mask = mask & ~directions
        latch_mask = mask & directions
        external = self._port_b_physical_bits(external_mask, address, width) if external_mask else 0
        if self.pbdr_known_mask & latch_mask != latch_mask:
            raise BootStop('unknown_peripheral_reset_state',
                           'PBDR output latch contains unknown bits after manual reset',
                           address=address, width=width, access='read')
        combined = external | (self.pbdr & latch_mask)
        value = (combined & mask) >> (8 if mask == 0xFF00 else 0)
        self.peripheral_trace.append({'register': 'PBDR', 'access': 'read',
                                      'value': value, 'width': width,
                                      'physical_input_mask': f'0x{external_mask:04X}',
                                      'latch_mask': f'0x{latch_mask:04X}',
                                      'scope': ('output_latch_not_pin_levels' if external_mask == 0 else
                                                'mixed_pin_and_latch_values')})
        return value

    def _pbdr_write(self, address: int, width: int, value: int) -> None:
        mask = self._pbdr_mask(address, width)
        shifted = ((value & 0xFF) << 8) if mask == 0xFF00 else value
        self.pbdr = ((self.pbdr & ~mask) | (shifted & mask)) & 0xFFFF
        self.pbdr_known_mask |= mask
        # Writes latch data regardless of pin direction/mux. Do NOT
        # assume a physical output or invented input state.
        self.peripheral_trace.append({'register':'PBDR','access':'write',
                                      'value':value & ((1 << (8 * width)) - 1),
                                      'width':width,'known_mask':f'0x{self.pbdr_known_mask:04X}',
                                      'scope':'output_latch_only',
                                      'note':'External pin state and timer/serial mux not modelled'})

    def set_port_c_pin_levels(self, values: Optional[int], known_mask: int = PC_VALID_MASK) -> None:
        if type(known_mask) is not int or not 0 <= known_mask <= PC_VALID_MASK:
            raise ValueError('Port C known mask must select only PC4..PC0')
        if values is not None and (type(values) is not int or not 0 <= values <= PC_VALID_MASK):
            raise ValueError('Port C pin values must be None or PC4..PC0 bits')
        self.port_c_pin_values = 0 if values is None else values
        self.port_c_pin_known_mask = 0 if values is None else known_mask

    @staticmethod
    def _pcdr_mask(address: int, width: int, access: str) -> int:
        if width == 2 and address == PCDR_ADDRESS: return 0xFFFF
        if width == 1 and address == PCDR_ADDRESS: return 0xFF00
        if width == 1 and address == PCDR_ADDRESS + 1: return 0x00FF
        raise BootStop('unsupported_access_size','PCDR supports aligned byte/word access only',
                       address=address,width=width,access=access)

    def _pcdr_write(self, address: int, width: int, value: int) -> None:
        mask = self._pcdr_mask(address,width,'write')
        bits = ((value & 0xFF) << 8) if mask == 0xFF00 else (value & 0xFFFF)
        if (bits & mask) & ~PC_VALID_MASK:
            raise BootStop('invalid_peripheral_write','PCDR reserved bits 15..5 must be written zero',
                           address=address,width=width,access='write',value=value)
        self.pcdr = (self.pcdr & ~(mask & PC_VALID_MASK)) | (bits & mask & PC_VALID_MASK)
        self.pcdr_known_mask |= mask & PC_VALID_MASK
        self.peripheral_trace.append({'register':'PCDR','access':'write',
                                      'value':value & ((1 << (8*width))-1),
                                      'width':width, 'known_mask':f'0x{self.pcdr_known_mask:04X}',
                                      'scope':'output_latch_only',
                                      'note':'No external pin or serial peripheral simulation'})

    def _pcdr_read(self, address: int, width: int) -> int:
        mask = self._pcdr_mask(address,width,'read')
        valid = mask & PC_VALID_MASK
        if valid == 0:
            self.peripheral_trace.append({'register':'PCDR','access':'read','value':0,
                                          'width':width,'scope':'reserved_bits_zero'})
            return 0
        direction = self.pfc[PCIOR_ADDRESS]
        if direction is None:
            raise BootStop('unknown_peripheral_reset_state',
                           'Port C I/O direction unknown after manual reset',
                           address=address,width=width,access='read')
        # SH7058 Rev 3.00 Table 22.6: PCIOR=0 -> physical pin; PCIOR=1
        # -> data latch, including alternate pin-function configurations.
        inputs = valid & ~direction
        outputs = valid & direction
        if inputs & ~self.port_c_pin_known_mask:
            raise BootStop('missing_input','Port C physical input levels not supplied',
                           address=address,width=width,access='read')
        if outputs & ~self.pcdr_known_mask:
            raise BootStop('unknown_peripheral_reset_state','Port C latch bits unknown',
                           address=address,width=width,access='read')
        combined = (self.port_c_pin_values & inputs) | (self.pcdr & outputs)
        value = (combined & valid) >> (8 if mask == 0xFF00 else 0)
        self.peripheral_trace.append({'register':'PCDR','access':'read','value':value,
                                      'width':width,'physical_input_mask':f'0x{inputs:04X}',
                                      'latch_mask':f'0x{outputs:04X}',
                                      'scope':'mixed_pin_and_latch_values' if inputs else 'output_latch_only'})
        return value

    def read(self, a: int, width: int) -> int:
        self.port_router.guard_32bit(a,width,access='read')
        if width not in (1,2,4): raise ValueError('Unsupported width')
        region,off=self._region(a,width,'read')
        if region=='rom':return int.from_bytes(self.image.data[off:off+width], 'big')
        if region=='peripheral':
            routed = self.port_router.read(off,width)
            if routed is not PeripheralRouter.UNHANDLED:
                return routed
            if off == 0xFFFFF70B and width == 1:
                if self.syscr2 is None:
                    raise BootStop('unknown_peripheral_reset_state','SYSCR2 state unknown after manual reset',address=off,width=1,access='read')
                self.peripheral_trace.append({'register':'SYSCR2','access':'read','value':self.syscr2})
                return self.syscr2
            if width == 2 and off == 0xFFFFF726:
                # PADR reads return *physical input levels* for pins in input
                # mode, which are not known from the firmware image alone.
                if self.pfc[0xFFFFF720] != 0xFFFF or self.padr is None:
                    raise BootStop('missing_input','PADR read includes pin inputs that are not simulated',address=off,width=2,access='read')
                self.peripheral_trace.append({'register':'PADR','access':'read','value':self.padr,'scope':'output_latch_only'})
                return self.padr
            if width == 2 and off in self.pfc:
                v = self.pfc[off]
                if v is None:
                    raise BootStop('unknown_peripheral_reset_state','PFC latch reset state unknown',address=off,width=width,access='read')
                self.peripheral_trace.append({'register':PFC_REGISTERS[off][0],'access':'read','value':v,'scope':'config_latch_only'})
                return v
            if width == 2 and off in self.ipr:
                v = self.ipr[off]
                if v is None:
                    raise BootStop('unknown_peripheral_reset_state','IPR reset state unknown',address=off,width=width,access='read')
                self.peripheral_trace.append({'register':f'IPR{chr(65+(off-0xFFFFED00)//2)}','access':'read','value':v})
                return v
            if width == 2 and off == 0xFFFFED18:
                # A known physical NMI pin does not make a preserved
                # manual-reset ICR control latch known. Diagnose each
                # missing dependency separately rather than inventing state.
                if self.icr_control is None:
                    raise BootStop('unknown_peripheral_reset_state',
                                   'ICR control state is unknown after manual reset',
                                   address=off,width=width,access='read')
                if self.nmi_high is None:
                    raise BootStop('missing_input',
                                   'ICR NMIL bit needs an explicitly simulated NMI pin level',
                                   address=off,width=width,access='read')
                v=(self.icr_control & 0x7FFF) | (0x8000 if self.nmi_high else 0)
                self.peripheral_trace.append({'register':'ICR','access':'read','value':v,'nmi_high':self.nmi_high})
                return v
            if width==2 and off in self.bsc:
                v=self.bsc[off]
                if v is None:
                    raise BootStop('unknown_peripheral_reset_state',f'Manual reset preserved BSC register 0x{off:X} has unknown value',address=off,width=width,access='read')
                self.peripheral_trace.append({'register':BSC_REGISTERS[off][0],'access':'read','value':v})
                return v
            raise BootStop('unmodelled_peripheral',f'Peripheral read at 0x{off:08X} ({width} bytes) is not modelled',address=off,width=width,access='read')
        if not all(self.ram_valid[off:off+width]):
            raise BootStop('uninitialised_ram',f'Read of unknown reset RAM at 0x{a:08X}',address=a,width=width,access='read')
        return int.from_bytes(self.ram[off:off+width], 'big')
    def write(self, a:int,width:int,value:int):
        self.port_router.guard_32bit(a,width,access='write',value=value)
        if width not in (1,2,4): raise ValueError('Unsupported width')
        region,off=self._region(a,width,'write',value)
        if region=='peripheral':
            routed = self.port_router.write(off,width,value)
            if routed is not PeripheralRouter.UNHANDLED:
                return routed
            if off == 0xFFFFF70A and width == 2:
                if (value >> 8) & 0xFF != 0x3C:
                    raise BootStop('invalid_peripheral_write','SYSCR2 requires 0x3C upper write key',address=off,width=2,access='write',value=value)
                self.syscr2=value & 0xFF
                self.peripheral_trace.append({'register':'SYSCR2','access':'write','value':self.syscr2,'write_word':f'0x{value:04X}'})
                return
            if width == 2 and off == 0xFFFFF726:
                self.padr=value & 0xFFFF
                self.peripheral_trace.append({'register':'PADR','access':'write','value':self.padr,'scope':'output_latch_only','note':'Pin output/input levels not emulated'})
                return
            if width == 2 and off in self.pfc:
                self.pfc[off]=value & 0xFFFF
                self.peripheral_trace.append({'register':PFC_REGISTERS[off][0],'access':'write','value':value & 0xFFFF,'scope':'config_latch_only'})
                return
            if width == 2 and off in self.ipr:
                self.ipr[off]=value & 0xFFFF
                self.peripheral_trace.append({'register':f'IPR{chr(65+(off-0xFFFFED00)//2)}','access':'write','value':value & 0xFFFF})
                return
            if width == 2 and off == 0xFFFFED18:
                self.icr_control = value & 0x7FFF
                self.peripheral_trace.append({'register':'ICR','access':'write','value':value & 0x7FFF, 'note':'NMI pin level unmodelled; interrupt dispatch not implemented'})
                return
            if width==2 and off in self.bsc:
                self.bsc[off]=value&0xFFFF
                self.peripheral_trace.append({'register':BSC_REGISTERS[off][0],'access':'write','value':value&0xFFFF})
                return
            raise BootStop('unmodelled_peripheral',f'Peripheral write at 0x{off:08X} ({width} bytes) is not modelled',address=off,width=width,access='write',value=value)
        if region=='ram':
            self.ram[off:off+width]=(value&((1<<(width*8))-1)).to_bytes(width,'big')
            self.ram_valid[off:off+width]=b'\x01'*width

class NCBootDiagnostic:
    """Instruction subset sufficient to report exact first boot blocker.

    Not cycle accurate, no interrupt execution, and no fabricated peripheral state.
    """
    def __init__(self, rom: ROMImage, *, reset: str='power', nmi_high: Optional[bool]=None,
                 port_b_pin_values: Optional[int]=None, port_b_pin_known_mask: int=0xFFFF,
                 port_c_pin_values: Optional[int]=None, port_c_pin_known_mask: int=PC_VALID_MASK,
                 port_d_pin_values: Optional[int]=None, port_d_pin_known_mask: int=0xFFFF):
        if len(rom.data) != ROM_LIMIT:
            raise BootStop('unsupported_image_size','SH7058 1 MiB full-flash profile requires exactly 1,048,576 bytes')
        if reset not in ('power','manual'): raise ValueError('reset must be power or manual')
        self.bus=BootBus(rom,power_on=(reset=="power"),nmi_high=nmi_high,
                         port_b_pin_values=port_b_pin_values, port_b_pin_known_mask=port_b_pin_known_mask,
                         port_c_pin_values=port_c_pin_values, port_c_pin_known_mask=port_c_pin_known_mask,
                         port_d_pin_values=port_d_pin_values, port_d_pin_known_mask=port_d_pin_known_mask); self.vectors=ResetVectors.read(rom.data); self.reset=reset
        self.pc=self.vectors.power_pc if reset=='power' else self.vectors.manual_pc
        sp=self.vectors.power_sp if reset=='power' else self.vectors.manual_sp
        if self.pc & 1 or not (ROM_BASE <= self.pc < ROM_LIMIT):
            raise BootStop('invalid_reset_vector',f'Invalid {reset} PC 0x{self.pc:08X}')
        if sp & 3 or not (RAM_BASE <= sp < RAM_LIMIT):
            raise BootStop('invalid_reset_vector',f'Invalid {reset} SP 0x{sp:08X}')
        self.r: list[Optional[int]]=[None]*16;self.r[15]=sp
        self.pr:Optional[int]=None
        self.t: Optional[bool] = None  # T bit not known from partial reset SR value
        self.known_sr_mask=0xF0
        self.known_sr_value=0xF0
        self.vbr=0
        self.executed=0;self.trace=[]
        self._active_instruction=None
        self._fetch_pc=None
    def reg(self,n):
        v=self.r[n]
        if v is None:raise BootStop('unknown_register',f'R{n} used before its reset-undefined value was initialised')
        return v
    def execute(self, *, delay_slot: bool=False):
        pc=self.pc
        self._fetch_pc=pc
        self._active_instruction=None
        op=self.bus.read(pc,2)
        n,m=(op>>8)&15,(op>>4)&15
        self.pc=(pc+2)&0xFFFFFFFF
        entry={'pc':f'0x{pc:08X}','opcode':f'{op:04X}','delay_slot':delay_slot}
        self.trace.append(entry)
        self._active_instruction=entry
        self.executed+=1
        if op==0x0009: return None
        if (op&0xF000)==0xE000:  # mov #imm,Rn
            self.r[n]=sign_extend(op&0xFF,8)&0xFFFFFFFF;return None
        if (op&0xF000)==0x9000:  # mov.w @(disp,PC),Rn
            self.r[n]=sign_extend(self.bus.read(pc+4+2*(op&0xFF),2),16)&0xFFFFFFFF;return None
        if (op&0xF000)==0xD000:  # mov.l @(disp,PC),Rn
            self.r[n]=self.bus.read(((pc+4)&~3)+4*(op&0xFF),4);return None
        if (op&0xF00F)==0x2000:  # mov.b Rm,@Rn
            self.bus.write(self.reg(n),1,self.reg(m));return None
        if (op&0xF00F)==0x2001:  # mov.w Rm,@Rn
            self.bus.write(self.reg(n),2,self.reg(m));return None
        if (op&0xF00F)==0x2002:  # mov.l Rm,@Rn
            self.bus.write(self.reg(n),4,self.reg(m));return None
        if (op&0xF00F)==0x6000:  # mov.b @Rm,Rn (sign-extend)
            self.r[n]=sign_extend(self.bus.read(self.reg(m),1),8)&0xFFFFFFFF;return None
        if (op&0xF00F)==0x6001:  # mov.w @Rm,Rn (sign-extend)
            self.r[n]=sign_extend(self.bus.read(self.reg(m),2),16)&0xFFFFFFFF;return None
        if (op&0xF00F)==0x6002:  # mov.l @Rm,Rn
            self.r[n]=self.bus.read(self.reg(m),4);return None
        if (op&0xF00F)==0x600C:  # extu.b Rm,Rn
            self.r[n]=self.reg(m)&0xFF;return None
        if (op&0xF00F)==0x600D:  # extu.w Rm,Rn
            self.r[n]=self.reg(m)&0xFFFF;return None
        if (op&0xF00F)==0x600E:  # exts.b Rm,Rn
            self.r[n]=sign_extend(self.reg(m)&0xFF,8)&0xFFFFFFFF;return None
        if (op&0xF00F)==0x600F:  # exts.w Rm,Rn
            self.r[n]=sign_extend(self.reg(m)&0xFFFF,16)&0xFFFFFFFF;return None
        if (op&0xF00F)==0x6003:  # mov Rm,Rn
            self.r[n]=self.reg(m);return None
        if (op&0xF00F)==0x2008:  # tst Rm,Rn -> T=1 when zero
            self.t=(self.reg(n)&self.reg(m))==0;return None
        if (op&0xFF00)==0x8900:  # bt disp
            if delay_slot: raise BootStop('illegal_delay_slot',f'BT in delay slot at 0x{pc:X}')
            if self.t is None: raise BootStop('unknown_status',f'T flag unknown at 0x{pc:X}')
            if self.t: self.pc=(pc+4+2*sign_extend(op&0xFF,8))&0xFFFFFFFF
            return None
        if (op&0xFF00)==0x8B00:  # bf disp
            if delay_slot: raise BootStop('illegal_delay_slot',f'BF in delay slot at 0x{pc:X}')
            if self.t is None: raise BootStop('unknown_status',f'T flag unknown at 0x{pc:X}')
            if not self.t: self.pc=(pc+4+2*sign_extend(op&0xFF,8))&0xFFFFFFFF
            return None
        if (op&0xF000)==0x7000:  # add #imm,Rn
            self.r[n]=(self.reg(n)+sign_extend(op&255,8))&0xFFFFFFFF;return None
        # Delayed branch destinations are applied *after* executing one slot.
        if (op&0xF000)==0xB000:
            if delay_slot: raise BootStop('illegal_delay_slot',f'BSR in delay slot at 0x{pc:X}')
            self.pr=(pc+4)&0xFFFFFFFF
            return (pc+4+2*sign_extend(op&0xFFF,12))&0xFFFFFFFF
        if (op&0xF000)==0xA000:
            if delay_slot: raise BootStop('illegal_delay_slot',f'BRA in delay slot at 0x{pc:X}')
            return (pc+4+2*sign_extend(op&0xFFF,12))&0xFFFFFFFF
        if op==0x000B:
            if delay_slot: raise BootStop('illegal_delay_slot',f'RTS in delay slot at 0x{pc:X}')
            if self.pr is None:raise BootStop('unknown_register',f'PR undefined at RTS 0x{pc:X}')
            return self.pr
        if (op&0xF0FF)==0x400B:  # jsr @Rn
            if delay_slot: raise BootStop('illegal_delay_slot',f'JSR in delay slot at 0x{pc:X}')
            addr=self.reg(n);self.pr=(pc+4)&0xFFFFFFFF
            return addr
        if (op&0xF0FF)==0x402B:  # jmp @Rn
            if delay_slot: raise BootStop('illegal_delay_slot',f'JMP in delay slot at 0x{pc:X}')
            return self.reg(n)
        raise BootStop('unsupported_opcode',f'Unsupported instruction 0x{op:04X} at PC 0x{pc:08X}', address=pc,width=2,access='fetch')
    def run(self, max_steps: int=200) -> dict:
        if not 1<=max_steps<=100000: raise ValueError('max_steps must be 1..100000')
        stop={'reason':'instruction_limit','detail':f'Maximum {max_steps} instructions reached'}
        while self.executed < max_steps:
            try:
                target=self.execute()
                if target is not None:
                    if self.executed >= max_steps:
                        stop={'reason':'instruction_limit','detail':'Stopped before executing required branch delay slot'}
                        break
                    second=self.execute(delay_slot=True)
                    if second is not None:raise BootStop('illegal_delay_slot','Branch in delay slot')
                    self.pc=target
            except BootStop as e:
                stop=e.report();break
        dependency=explain_stop(stop, trace=self.trace,
                                active_instruction=self._active_instruction,
                                fetch_pc=self._fetch_pc)
        return {
            'engine':'SH7058 reset diagnostic (partial SH-2 integer instruction subset)',
            'rom_sha256':hashlib.sha256(self.bus.image.data).hexdigest(),
            'rom_size_bytes':len(self.bus.image.data),
            'profile':'sh7058-1m-readonly',
            'reset':self.reset,
            'nmi_high':self.bus.nmi_high,
            'port_d_explicit_pins':None if self.bus.port_d.pin_known_mask == 0 else {
                'value':f'0x{self.bus.port_d.pin_values:04X}',
                'known_mask':f'0x{self.bus.port_d.pin_known_mask:04X}'},
            'port_c_explicit_pins':None if self.bus.port_c_pin_known_mask == 0 else {
                'value':f'0x{self.bus.port_c_pin_values:04X}',
                'known_mask':f'0x{self.bus.port_c_pin_known_mask:04X}'},
            'port_b_explicit_pins':None if self.bus.port_b_pin_known_mask == 0 else {
                'value':f'0x{self.bus.port_b_pin_values:04X}',
                'known_mask':f'0x{self.bus.port_b_pin_known_mask:04X}'},
            'vectors':self.vectors.as_dict(),
            'initial_sp':f'0x{(self.vectors.power_sp if self.reset=="power" else self.vectors.manual_sp):08X}',
            'sr_known_bits':{'mask':'0x000000F0','value':'0x000000F0'},
            'pc_at_stop':f'0x{self.pc:08X}',
            'last_fetched_pc':self.trace[-1]['pc'] if self.trace else None,
            'pr_at_stop':None if self.pr is None else f'0x{self.pr:08X}',
            'executed_instructions':self.executed,
            'stop':stop,
            'next_dependency':dependency,
            'trace':self.trace[-min(100,len(self.trace)):],
            'modelled_peripheral_accesses':self.bus.peripheral_trace,
            'boot_complete':False,
            'note':'Not a complete SH7058 emulator; never assume firmware boots from this result.'
        }

def diagnose_nc_reset(rom: ROMImage, reset: str='power', max_steps: int=200, nmi_high: Optional[bool]=None,
                      port_b_pin_values: Optional[int]=None, port_b_pin_known_mask: int=0xFFFF,
                      port_c_pin_values: Optional[int]=None, port_c_pin_known_mask: int=PC_VALID_MASK,
                      port_d_pin_values: Optional[int]=None, port_d_pin_known_mask: int=0xFFFF) -> dict:
    try:
        return NCBootDiagnostic(rom, reset=reset, nmi_high=nmi_high,
                                port_b_pin_values=port_b_pin_values,
                                port_b_pin_known_mask=port_b_pin_known_mask,
                                port_c_pin_values=port_c_pin_values,
                                port_c_pin_known_mask=port_c_pin_known_mask,
                                port_d_pin_values=port_d_pin_values,
                                port_d_pin_known_mask=port_d_pin_known_mask).run(max_steps=max_steps)
    except BootStop as e:
        return {'engine':'SH7058 reset diagnostic','profile':'sh7058-1m-readonly','reset':reset,'nmi_high':nmi_high,
                'stop':e.report(),
                'next_dependency':explain_stop(e.report(),trace=[]),
                'boot_complete':False}
