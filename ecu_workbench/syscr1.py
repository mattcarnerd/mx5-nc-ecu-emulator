"""SH7058 Rev3 25.2.2: bounded RAM-already-enabled SYSCR1 command.

Bit7 OSCSTOP has no supplied oscillator history. AUDSRST initial state is
conflicting in Rev3 (diagram0/table1), so it remains unknown before a write.
Only observed byte1 is supported, and only with RAME already known enabled.
RAM disable/re-enable sequencing and AUD/oscillator changes are unmodelled.
"""
from .known_bits import KnownBits
ADDRESS=0xFFFFF708

class SystemControl1:
    def __init__(self, *, power_on,trace,stop_type):
        self.state=KnownBits(1,0x7D) if power_on else KnownBits(0,0x3C)
        self.trace,self.stop_type=trace,stop_type

    def access(self,width,operation,value=None,*,typed=False):
        if width!=1:
            raise self.stop_type('unsupported_access_size','SYSCR1 requires byte access',address=ADDRESS,width=width,access=operation)
        if operation=='write':
            if value & 0x3C:
                raise self.stop_type('invalid_peripheral_write','SYSCR1 reserved bits5..2 require zero',address=ADDRESS,width=width,access=operation,value=value)
            if value!=1:
                raise self.stop_type('unsupported_peripheral_mode','SYSCR1 subset supports only byte1 with RAM already enabled; oscillator/AUD changes and RAM disable are unmodelled',address=ADDRESS,width=width,access=operation,value=value)
            if not self.state.mask&1 or not self.state.value&1:
                raise self.stop_type('unknown_peripheral_reset_state','SYSCR1 RAME must already be known enabled; re-enable sequencing unmodelled',address=ADDRESS,width=width,access=operation,value=value)
            self.state=KnownBits(self.state.value&0x80|1,self.state.mask|0x7F)
            self.trace.append({'register':'SYSCR1','access':'write','width':1,'value':value,'scope':'RAM_already_enabled_control_subset'})
            return
        if not typed and self.state.mask!=0xFF:
            raise self.stop_type('unknown_peripheral_reset_state','SYSCR1 oscillator/AUD history contains unknown bits',address=ADDRESS,width=width,access=operation)
        self.trace.append({'register':'SYSCR1','access':'read','width':1,'known_value':self.state.value,'known_mask':self.state.mask,'scope':'partial_control_readback_no_oscillator_model'})
        return KnownBits(self.state.value,self.state.mask|0xFFFFFF00) if typed else self.state.value
