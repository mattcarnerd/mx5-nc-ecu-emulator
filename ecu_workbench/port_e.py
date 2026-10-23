"""SH7058 Rev 3.00 Port E PEDR (section 22.6): 16-bit data latch.

The POD input can disable physical outputs. We therefore model only the
software-visible latch and explicit pin reads, never physical pin drive.
"""
PEDR_ADDRESS = 0xFFFFF754
PEIOR_ADDRESS = 0xFFFFF750

class PortE:
    def __init__(self, *, power_on, pfc, trace, stop_type,
                 pin_values=None, pin_known_mask=0xFFFF):
        self.data = 0
        self.known_mask = 0xFFFF if power_on else 0
        self.pfc, self.trace, self.stop_type = pfc, trace, stop_type
        self.set_pins(pin_values, pin_known_mask)

    def set_pins(self, values, known_mask=0xFFFF):
        if type(known_mask) is not int or not 0 <= known_mask <= 0xFFFF:
            raise ValueError("Port E known mask must fit 16 bits")
        if values is not None and (type(values) is not int or not 0 <= values <= 0xFFFF):
            raise ValueError("Port E pin levels must be None or a 16-bit integer")
        self.pin_values = 0 if values is None else values
        self.pin_known_mask = 0 if values is None else known_mask

    def _mask(self, address, width, access):
        if width == 2 and address == PEDR_ADDRESS:
            return 0xFFFF
        if width == 1 and address == PEDR_ADDRESS:
            return 0xFF00
        if width == 1 and address == PEDR_ADDRESS + 1:
            return 0x00FF
        raise self.stop_type("unsupported_access_size",
                             "PEDR permits aligned 8/16-bit access only",
                             address=address, width=width, access=access)

    def write(self, address, width, value):
        mask = self._mask(address, width, "write")
        shifted = (value & 0xFF) << 8 if mask == 0xFF00 else value & 0xFFFF
        self.data = (self.data & ~mask) | (shifted & mask)
        self.known_mask |= mask
        self.trace.append({"register":"PEDR","access":"write",
                           "value": value & ((1 << (8*width))-1),
                           "width":width,"known_mask":f"0x{self.known_mask:04X}",
                           "scope":"output_latch_only",
                           "note":"POD, physical pin drive and alternate functions not simulated"})

    def read(self, address, width):
        mask = self._mask(address, width, "read")
        direction = self.pfc[PEIOR_ADDRESS]
        if direction is None:
            raise self.stop_type("unknown_peripheral_reset_state",
                                 "PEIOR preserved direction state unknown",
                                 address=address,width=width,access="read")
        inputs, outputs = mask & ~direction, mask & direction
        missing = inputs & ~self.pin_known_mask
        if missing:
            raise self.stop_type("missing_input",
                                 f"Port E external pin levels unknown: 0x{missing:04X}",
                                 address=address,width=width,access="read")
        if outputs & ~self.known_mask:
            raise self.stop_type("unknown_peripheral_reset_state",
                                 "PEDR output latch unknown after manual reset",
                                 address=address,width=width,access="read")
        combined = ((self.pin_values & inputs) | (self.data & outputs)) & mask
        value = combined >> (8 if mask == 0xFF00 else 0)
        self.trace.append({"register":"PEDR","access":"read","value":value,
                           "width":width,"physical_input_mask":f"0x{inputs:04X}",
                           "latch_mask":f"0x{outputs:04X}",
                           "scope":"mixed_pin_and_latch_values" if inputs else "output_latch_only"})
        return value
