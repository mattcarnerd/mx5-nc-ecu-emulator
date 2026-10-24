"""B39 SDSR only: SH7058 Rev.3 table 19.2, 19.3.2 and 19.5.4.

RES does not reset H-UDI. External TRST/serial activity is never inferred.
SDIR/SDDR, TAP and combined 32-bit transactions remain unsupported.
"""
SDSR_ADDRESS=0xFFFFF7C2
HUDI_SCENARIOS=('unknown','trst-reset','transfer-complete')
HUDI_SCENARIO_LABELS={
    'Unknown (default)': 'unknown',
    'Assume TRST reset': 'trst-reset',
    'Assume transfer complete': 'transfer-complete',
}

def scenario_metadata(scenario):
    if scenario not in HUDI_SCENARIOS:
        raise ValueError('Invalid H-UDI scenario')
    conditional=scenario!='unknown'
    return {'hudi_scenario':scenario, 'conditional_hardware_scenario':conditional,
            'hardware_scenario_note': (
                'Conditional simulation: assumed H-UDI state; not verified ECU hardware history.'
                if conditional else 'H-UDI initial state unknown; no TRST/serial history assumed.')}


def run_scenario_metadata(hudi_scenario,phi_cycles_per_instruction=None):
    from .virtual_clock import phi_scenario_metadata
    result=scenario_metadata(hudi_scenario)
    result.update(phi_scenario_metadata(phi_cycles_per_instruction))
    result['conditional_hardware_scenario'] |= result['conditional_clock_scenario']
    return result


class HudiStatus:
    def __init__(self, *, trace, stop_type, scenario="unknown"):
        scenario_metadata(scenario)
        self.scenario=scenario
        self.sdtrf=None
        self.trace,self.stop_type=trace,stop_type
        if scenario=="trst-reset":self.trst_reset()
        elif scenario=="transfer-complete":self.serial_transfer_completed()

    def trst_reset(self):
        """Explicit test-reset event supplied by a caller; not a power reset."""
        self.sdtrf=True

    def serial_transfer_completed(self):
        """Explicit synthetic serial event; there is no autonomous TAP model."""
        self.sdtrf=False

    def _mask(self,address,width,access):
        if address==SDSR_ADDRESS and width==2:return 0xFFFF
        if width==1 and address==SDSR_ADDRESS:return 0xFF00
        if width==1 and address==SDSR_ADDRESS+1:return 0xFF
        raise self.stop_type('unsupported_access_size',
            'SDSR subset permits byte/word; combined SDIR/SDSR long access is unmodelled',
            address=address,width=width,access=access)

    def read(self,address,width):
        mask=self._mask(address,width,'read')
        if mask&1 and self.sdtrf is None:
            raise self.stop_type('unknown_peripheral_reset_state',
                'H-UDI SDSR SDTRF unknown: power/manual reset does not initialize it; TRST/serial history required',
                address=address,width=width,access='read')
        value=0x0B00 | (int(self.sdtrf) if self.sdtrf is not None else 0)
        value=(value & mask) >> (8 if mask==0xFF00 else 0)
        self.trace.append({'register':'SDSR','access':'read','width':width,'value':value,
                           'scope':'status_only_no_debugger_simulation'})
        return value

    def write(self,address,width,value):
        mask=self._mask(address,width,'write')
        shifted=(value&0xFF)<<8 if mask==0xFF00 else value&0xFFFF
        if (shifted & mask & 0xFFFE)!=(0x0B00 & mask):
            raise self.stop_type('invalid_peripheral_write','SDSR reserved bits require 0x0B00 pattern',
                address=address,width=width,access='write',value=value)
        # CPU writing one sets SDTRF; only a serial completion clears it.
        if mask & shifted & 1:self.sdtrf=True
        self.trace.append({'register':'SDSR','access':'write','width':width,
                           'value':value&((1<<(width*8))-1),
                           'scope':'status_only_no_debugger_simulation'})
