"""SH7058 Rev.3 section 22.7: Port F data register (PFDR).

PFDR is a 16-bit R/W data latch at 0xFFFFF74E (8/16-bit accesses).
PFIOR=0 reads physical input pins; PFIOR=1 reads the data latch.
Writing PFDR *never* implies output-pin state or external bus signalling.
POD can tri-state PF0–PF4 outputs; the physical POD level is not modelled.
See Renesas hardware manual table 22.11 and table 22.12.
"""
PFDR_ADDRESS = 0xFFFFF74E
PFIOR_ADDRESS = 0xFFFFF748


class PortF:
    def __init__(self, *, power_on, pfc, trace, stop_type,
                 pin_values=None, pin_known_mask=0xFFFF):
        self.data = 0
        self.known_mask = 0xFFFF if power_on else 0
        self.pfc, self.trace, self.stop_type = pfc, trace, stop_type
        self.set_pins(pin_values, pin_known_mask)

    def set_pins(self, values, known_mask=0xFFFF):
        if type(known_mask) is not int or not 0 <= known_mask <= 0xFFFF:
            raise ValueError("Port F known mask must be 16-bit integer")
        if values is not None and (type(values) is not int or not 0 <= values <= 0xFFFF):
            raise ValueError("Port F pin values must be None or 16-bit integer")
        self.pin_values = 0 if values is None else values
        self.pin_known_mask = 0 if values is None else known_mask

    def _mask(self, address, width, access):
        if width == 2 and address == PFDR_ADDRESS:
            return 0xFFFF
        if width == 1 and address == PFDR_ADDRESS:
            return 0xFF00
        if width == 1 and address == PFDR_ADDRESS + 1:
            return 0x00FF
        raise self.stop_type(
            "unsupported_access_size",
            "PFDR permits aligned 8/16-bit access only",
            address=address, width=width, access=access)

    def write(self, address, width, value):
        mask = self._mask(address, width, "write")
        shifted = ((value & 0xFF) << 8) if mask == 0xFF00 else value & 0xFFFF
        self.data = (self.data & ~mask) | (shifted & mask)
        self.known_mask |= mask
        self.trace.append({
            "register": "PFDR", "access": "write", "width": width,
            "value": value & ((1 << (8 * width)) - 1),
            "known_mask": f"0x{self.known_mask:04X}",
            "scope": "output_latch_only",
            "note": "POD pin, alternate functions and physical outputs not simulated",
        })

    def read(self, address, width):
        mask = self._mask(address, width, "read")
        direction = self.pfc[PFIOR_ADDRESS]
        if direction is None:
            raise self.stop_type(
                "unknown_peripheral_reset_state",
                "PFIOR direction register preserved and unknown after manual reset",
                address=address, width=width, access="read")
        inputs, outputs = mask & ~direction, mask & direction
        missing = inputs & ~self.pin_known_mask
        if missing:
            raise self.stop_type(
                "missing_input",
                f"Port F physical pin levels unknown: 0x{missing:04X}",
                address=address, width=width, access="read")
        missing_latch = outputs & ~self.known_mask
        if missing_latch:
            raise self.stop_type(
                "unknown_peripheral_reset_state",
                f"PFDR output latch unknown: 0x{missing_latch:04X}",
                address=address, width=width, access="read")
        result = ((self.pin_values & inputs) | (self.data & outputs)) & mask
        value = result >> (8 if mask == 0xFF00 else 0)
        self.trace.append({
            "register": "PFDR", "access": "read", "width": width,
            "value": value,
            "physical_input_mask": f"0x{inputs:04X}",
            "latch_mask": f"0x{outputs:04X}",
            "scope": "mixed_pin_and_latch_values" if inputs else "output_latch_only",
        })
        return value
