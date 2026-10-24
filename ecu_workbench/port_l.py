"""SH7058 Rev.3 section 22.12, Tables 22.21/22.22 (pp. 828-830): Port L data register PLDR.

Only PL13..PL0 exist. Reserved bits 15..14 read zero and must be written
zero. PLIOR selects output-latch readback versus real input pin levels.
No alternate-function activity or physical pin driving is simulated.
"""
PLDR_ADDRESS = 0xFFFFF75E
PLIOR_ADDRESS = 0xFFFFF756
PL_VALID_MASK = 0x3FFF


class PortL:
    def __init__(self, *, power_on, pfc, trace, stop_type,
                 pin_values=None, pin_known_mask=PL_VALID_MASK):
        self.data = 0
        self.known_mask = PL_VALID_MASK if power_on else 0
        self.pfc, self.trace, self.stop_type = pfc, trace, stop_type
        self.set_pins(pin_values, pin_known_mask)

    def set_pins(self, values, known_mask=PL_VALID_MASK):
        if type(known_mask) is not int or not 0 <= known_mask <= PL_VALID_MASK:
            raise ValueError("Port L known mask must fit PL13..PL0")
        if values is not None and (type(values) is not int or not 0 <= values <= PL_VALID_MASK):
            raise ValueError("Port L physical pin values must fit PL13..PL0")
        self.pin_values = 0 if values is None else values
        self.pin_known_mask = 0 if values is None else known_mask

    def _mask(self, address, width, access):
        if width == 2 and address == PLDR_ADDRESS:
            return 0xFFFF
        if width == 1 and address == PLDR_ADDRESS:
            return 0xFF00
        if width == 1 and address == PLDR_ADDRESS + 1:
            return 0x00FF
        raise self.stop_type("unsupported_access_size",
                             "PLDR permits aligned 8/16-bit access only",
                             address=address, width=width, access=access)

    def write(self, address, width, value):
        mask = self._mask(address, width, "write")
        shifted = ((value & 0xFF) << 8) if mask == 0xFF00 else value & 0xFFFF
        forbidden = shifted & mask & ~PL_VALID_MASK
        if forbidden:
            raise self.stop_type("invalid_peripheral_write",
                                 f"PLDR reserved bits must be written zero: 0x{forbidden:04X}",
                                 address=address, width=width, access="write", value=value)
        self.data = (self.data & ~mask) | (shifted & mask & PL_VALID_MASK)
        self.known_mask |= mask & PL_VALID_MASK
        self.trace.append({
            "register": "PLDR", "access": "write", "width": width,
            "value": value & ((1 << (8*width)) - 1),
            "known_mask": f"0x{self.known_mask:04X}",
            "scope": "output_latch_only",
            "note": "PL13..PL0 only; external pins and alternate functions not driven",
        })

    def read(self, address, width):
        mask = self._mask(address, width, "read")
        requested = mask & PL_VALID_MASK
        # Only implemented bits participate in direction and input checks.
        if not requested:
            value = 0
        else:
            direction = self.pfc[PLIOR_ADDRESS]
            if direction is None:
                raise self.stop_type("unknown_peripheral_reset_state",
                                     "PLIOR preserved direction unknown after manual reset",
                                     address=address, width=width, access="read")
            inputs = requested & ~direction
            outputs = requested & direction
            missing = inputs & ~self.pin_known_mask
            if missing:
                raise self.stop_type("missing_input",
                                     f"Port L external pin levels unknown: 0x{missing:04X}",
                                     address=address, width=width, access="read")
            if outputs & ~self.known_mask:
                raise self.stop_type("unknown_peripheral_reset_state",
                                     "PLDR output latch unknown after manual reset",
                                     address=address, width=width, access="read")
            value = ((self.pin_values & inputs) | (self.data & outputs)) & requested
        if mask == 0xFF00:
            value >>= 8
        self.trace.append({
            "register": "PLDR", "access": "read", "width": width,
            "value": value, "scope": "readback_or_explicit_pins",
            "reserved_bits_read_zero": True,
        })
        return value
