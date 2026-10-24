"""B20: RSTCSR access only, SH7058 Rev.3 13.2.3/13.2.4.

No watchdog clock, overflow events or generated resets are fabricated.
Invalid keys/reserved encodings stop outside the supported write contract.
"""
RSTCSR_WRITE = 0xFFFFEC12
RSTCSR_READ = 0xFFFFEC13

class ResetControl:
    def __init__(self, *, power_on, trace, stop_type):
        self.value = 0x1F
        self.known_mask = 0xFF if power_on else 0x1F
        self.wovf_read = False
        self.trace, self.stop_type = trace, stop_type

    def guard(self, address, width, access):
        valid = (access=='read' and address==RSTCSR_READ and width==1) or (
            access=='write' and address==RSTCSR_WRITE and width==2)
        if not valid:
            raise self.stop_type('unsupported_access_size',
                'RSTCSR reads require byte EC13; writes require word EC12',
                address=address,width=width,access=access)

    def read(self, address, width):
        self.guard(address,width,'read')
        if self.known_mask!=0xFF:
            raise self.stop_type('unknown_peripheral_reset_state',
                'RSTCSR retained WDT-reset state unknown',address=address,width=width,access='read')
        self.wovf_read = bool(self.value & 0x80)
        self.trace.append({'register':'RSTCSR','access':'read','width':1,'value':self.value})
        return self.value

    def write(self, address, width, value):
        self.guard(address,width,'write')
        word=value & 0xFFFF
        if word>>8==0x5A and word & 0x1F==0x1F:
            self.value=(self.value & 0x80) | (word & 0x60) | 0x1F
            self.known_mask |= 0x60
        elif word==0xA500:
            if self.wovf_read:
                self.value &= ~0x80
                self.known_mask |= 0x80
                self.wovf_read=False
        else:
            raise self.stop_type('invalid_peripheral_write',
                'RSTCSR requires 5A control key/reserved ones or A500 flag clear',
                address=address,width=width,access='write',value=value)
        self.trace.append({'register':'RSTCSR','access':'write','width':2,'value':word,
                           'known_mask':f'0x{self.known_mask:02X}',
                           'scope':'reset_control_latch_only'})

class WatchdogTimer:
    """Interval mode requires explicit phi packets; no oscillator is assumed."""
    DIVISORS=(2,64,128,256,512,1024,4096,8192)

    def __init__(self, *, power_on, trace, stop_type, clock_supplied=False, request_interval=None):
        if type(clock_supplied) is not bool:raise ValueError('clock_supplied must be boolean')
        if request_interval is not None and not callable(request_interval):raise TypeError('Invalid ITI callback')
        self.clock_supplied=clock_supplied
        self.request_interval=request_interval
        self.phi_cycles=0  # explicit fixture origin/phase, not measured board timing
        self.overflow_count=0
        self.tcsr = 0x18 if power_on else None
        self.tcnt = 0 if power_on else None
        self.ovf_read = False
        self.trace, self.stop_type = trace, stop_type

    def read(self,address,width):
        if width!=1 or address not in (0xFFFFEC10,0xFFFFEC11):
            raise self.stop_type('unsupported_access_size','WDT reads require byte TCSR/TCNT',
                                 address=address,width=width,access='read')
        name='TCSR' if address==0xFFFFEC10 else 'TCNT'
        value=getattr(self,name.lower())
        if value is None:
            raise self.stop_type('unknown_peripheral_reset_state','WDT retained state unknown',
                                 address=address,width=width,access='read')
        if name=='TCSR': self.ovf_read=bool(value & 0x80)
        self.trace.append({'register':name,'access':'read','width':width,'value':value})
        return value

    def write(self,address,width,value):
        if address!=0xFFFFEC10 or width!=2:
            raise self.stop_type('unsupported_access_size','WDT writes require keyed word EC10',
                                 address=address,width=width,access='write',value=value)
        key=(value>>8)&0xFF; low=value&0xFF
        if key==0x5A:
            if self.tcsr is None:
                raise self.stop_type('unknown_peripheral_reset_state','WDT enable state unknown',
                                     address=address,width=width,access='write',value=value)
            self.tcnt=low
            name='TCNT'
        elif key==0xA5:
            if low & 0x18!=0x18:
                raise self.stop_type('invalid_peripheral_write','TCSR reserved bits require ones',
                                     address=address,width=width,access='write',value=value)
            if low & 0x20 and (not self.clock_supplied or low & 0x40):
                raise self.stop_type('unsupported_peripheral_mode','Running interval mode requires explicit phi input; watchdog reset mode unsupported',
                                     address=address,width=width,access='write',value=value)
            if self.tcsr is None:
                raise self.stop_type('unknown_peripheral_reset_state','TCSR overflow state unknown',
                                     address=address,width=width,access='write',value=value)
            if self.tcsr & 0x20 and (self.tcsr ^ low) & 0x47:
                raise self.stop_type('invalid_peripheral_write','Stop WDT before changing clock or mode',
                                     address=address,width=width,access='write',value=value)
            flag=self.tcsr & 0x80
            if self.ovf_read and not low & 0x80:
                flag=0; self.ovf_read=False
            self.tcsr=flag | (low & 0x67) | 0x18
            if not low & 0x20:self.tcnt=0
            self._update_request()
            name='TCSR'
        else:
            raise self.stop_type('invalid_peripheral_write','WDT requires 5A counter or A5 control key',
                                 address=address,width=width,access='write',value=value)
        self.trace.append({'register':name,'access':'write','width':width,'value':value&0xFFFF,
                           'scope':'explicit_phi_interval_subset' if self.clock_supplied else 'disabled_watchdog_programming_only'})


    def _update_request(self):
        if self.request_interval is not None:
            self.request_interval(bool(self.tcsr & 0x80) and not bool(self.tcsr & 0x40))

    def advance_phi_cycles(self,cycles):
        """Caller orders phi packets and register writes; no simultaneous T3 collision model.

        Explicit fixture phase starts at zero and advances even while counting is
        disabled. Packets are internal phi cycles, never seconds or instruction ticks.
        """
        if type(cycles) is not int or cycles<0:raise ValueError('phi cycles must be a nonnegative integer')
        if not self.clock_supplied:
            raise self.stop_type('missing_input','Explicit phi-cycle source required')
        if self.tcsr is None or self.tcnt is None:
            raise self.stop_type('unknown_peripheral_reset_state','WDT state unknown for supplied phi packet')
        before=self.phi_cycles
        self.phi_cycles+=cycles
        if not self.tcsr & 0x20:return
        divisor=self.DIVISORS[self.tcsr & 7]
        increments=self.phi_cycles//divisor - before//divisor
        total=self.tcnt+increments
        overflows=total//256
        self.tcnt=total & 0xFF
        if overflows:
            self.overflow_count+=overflows
            self.tcsr |= 0x80
            self._update_request()
            self.trace.append({'register':'TCNT','access':'overflow','count':overflows,
                               'phi_cycles':self.phi_cycles,'scope':'explicit_phi_fixture_only'})
