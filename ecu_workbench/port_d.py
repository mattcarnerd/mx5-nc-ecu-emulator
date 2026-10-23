"""Renesas SH7058 Rev 3.00 Port D, sections 22.5.1-22.5.3.

PDDR stores PD13..PD0 (bits 15-14 reserved); PDPR reads physical pins.
The module deliberately does not model output drive, CAN or timer mux wiring.
"""
PDDR_ADDRESS = 0xFFFFF746
PDIOR_ADDRESS = 0xFFFFF740
PDPR_ADDRESS = 0xFFFFF784
PD_VALID_MASK = 0x3FFF


class PortD:
    def __init__(self, *, power_on, pfc, trace, stop_type,
                 pin_values=None, pin_known_mask=0xFFFF):
        self.data = 0
        self.data_known_mask = PD_VALID_MASK if power_on else 0
        self.pfc, self.trace, self.stop_type = pfc, trace, stop_type
        self.set_pins(pin_values, pin_known_mask)

    def set_pins(self, values, known_mask=0xFFFF):
        """Known external levels are independent of the PDDR data latch.

        PDPR defines 16 bit positions, while PDDR implements PD13..PD0.
        Never invent unspecified high pin-register bits.
        """
        if type(known_mask) is not int or not 0 <= known_mask <= 0xFFFF:
            raise ValueError('Port D known mask must fit 16 bits')
        if values is not None and (type(values) is not int or not 0 <= values <= 0xFFFF):
            raise ValueError('Port D pin levels must be None or 16-bit integer')
        self.pin_values = 0 if values is None else values
        self.pin_known_mask = 0 if values is None else known_mask

    def _mask(self, address, width, base, name, access):
        if width == 2 and address == base:
            return 0xFFFF
        if width == 1 and address == base:
            return 0xFF00
        if width == 1 and address == base + 1:
            return 0x00FF
        raise self.stop_type('unsupported_access_size',
                             f'{name} permits aligned 8/16-bit access only',
                             address=address, width=width, access=access)

    def _physical(self, mask, address, width):
        missing = mask & ~self.pin_known_mask
        if missing:
            raise self.stop_type('missing_input',
                                 f'Port D physical pin levels unknown: 0x{missing:04X}',
                                 address=address, width=width, access='read')
        return self.pin_values & mask

    def read(self, address, width):
        if PDPR_ADDRESS <= address <= PDPR_ADDRESS + 1:
            mask = self._mask(address,width,PDPR_ADDRESS,'PDPR','read')
            value = self._physical(mask,address,width)
            value >>= 8 if mask == 0xFF00 else 0
            self.trace.append({'register':'PDPR','access':'read','value':value,
                               'width':width,'scope':'explicit_external_pin_levels'})
            return value

        mask = self._mask(address,width,PDDR_ADDRESS,'PDDR','read')
        valid = mask & PD_VALID_MASK
        if valid == 0:
            self.trace.append({'register':'PDDR','access':'read',
                               'value':0,'width':width,'scope':'reserved_bits_zero'})
            return 0
        direction = self.pfc[PDIOR_ADDRESS]
        if direction is None:
            raise self.stop_type('unknown_peripheral_reset_state',
                                 'PDIOR preserved state is unknown',
                                 address=address,width=width,access='read')
        # Renesas Table 22.8: PDIOR=0 -> physical input; =1 -> data latch.
        # Alternate timer/HCAN routing does not change this read rule.
        inputs, outputs = valid & ~direction, valid & direction
        external = self._physical(inputs,address,width) if inputs else 0
        unknown_latch = outputs & ~self.data_known_mask
        if unknown_latch:
            raise self.stop_type('unknown_peripheral_reset_state',
                                 f'PDDR output latch unknown: 0x{unknown_latch:04X}',
                                 address=address,width=width,access='read')
        value = (external | (self.data & outputs)) & valid
        value >>= 8 if mask == 0xFF00 else 0
        self.trace.append({'register':'PDDR','access':'read','value':value,
                           'width':width,'physical_input_mask':f'0x{inputs:04X}',
                           'latch_mask':f'0x{outputs:04X}',
                           'scope':'mixed_pin_and_latch_values' if inputs else 'output_latch_only'})
        return value

    def write(self, address, width, value):
        if PDPR_ADDRESS <= address <= PDPR_ADDRESS + 1:
            self._mask(address,width,PDPR_ADDRESS,'PDPR','write')
            raise self.stop_type('read_only_peripheral',
                                 'PDPR samples physical pins and is not writable',
                                 address=address,width=width,access='write',value=value)
        mask = self._mask(address,width,PDDR_ADDRESS,'PDDR','write')
        shifted = ((value & 0xFF) << 8) if mask == 0xFF00 else (value & 0xFFFF)
        if (shifted & mask) & ~PD_VALID_MASK:
            raise self.stop_type('invalid_peripheral_write',
                                 'PDDR reserved bits 15-14 must be written zero',
                                 address=address,width=width,access='write',value=value)
        self.data = (self.data & ~(mask & PD_VALID_MASK)) | (shifted & mask & PD_VALID_MASK)
        self.data_known_mask |= mask & PD_VALID_MASK
        self.trace.append({'register':'PDDR','access':'write',
                           'value':value & ((1 << (8*width))-1),
                           'width':width,'known_mask':f'0x{self.data_known_mask:04X}',
                           'scope':'output_latch_only',
                           'note':'Physical output and alternate functions not simulated'})
