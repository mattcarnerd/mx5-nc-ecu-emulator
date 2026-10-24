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
    """Disabled TCNT/TCSR programming subset; running modes fail closed."""
    def __init__(self, *, power_on, trace, stop_type):
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
            if low & 0x20:
                raise self.stop_type('unsupported_peripheral_mode','Running watchdog timing is not modelled',
                                     address=address,width=width,access='write',value=value)
            if self.tcsr is None:
                raise self.stop_type('unknown_peripheral_reset_state','TCSR overflow state unknown',
                                     address=address,width=width,access='write',value=value)
            flag=self.tcsr & 0x80
            if self.ovf_read and not low & 0x80:
                flag=0; self.ovf_read=False
            self.tcsr=flag | (low & 0x47) | 0x18
            self.tcnt=0
            name='TCSR'
        else:
            raise self.stop_type('invalid_peripheral_write','WDT requires 5A counter or A5 control key',
                                 address=address,width=width,access='write',value=value)
        self.trace.append({'register':name,'access':'write','width':width,'value':value&0xFFFF,
                           'scope':'disabled_watchdog_programming_only'})
