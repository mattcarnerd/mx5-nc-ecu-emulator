"""Optional TCNT0 explicit-Pphi runtime; SH7058 Rev3 11.2.5-7/15.

No physical frequency, ADC trigger, capture or other-channel clock is assumed.
"""
TCNT0=0xFFFFF430
TSR0=0xFFFFF42C
TIER0=0xFFFFF42E
TSTR1=0xFFFFF401
PSCR1=0xFFFFF404
ITVRR=(0xFFFFF424,0xFFFFF426,0xFFFFF428)

class Counter0Runtime:
    def __init__(self,atu):
        self.atu=atu;self.enabled=False;self.read_flags=0;self.counter_ticks=0

    def guard_start(self):
        a=self.atu
        for address in (TCNT0,TSR0,TIER0,*ITVRR):a.known(address)
        if any(a.regs[address]&0xF0 for address in ITVRR):
            a.fail('unsupported_peripheral_mode','TCNT0 ADC interval triggers outside subset')
        if a.regs[TIER0]&0xF:a.fail('unsupported_peripheral_mode','TCNT0 capture IRQs outside subset')

    def bind(self,*,phase):
        if self.enabled:raise ValueError('Counter0 fixture already bound')
        self.guard_start();self.atu.begin_clock_fixture(phase=phase)
        self.enabled=True

    @property
    def interval_pending(self):
        value=self.atu.regs[TSR0]
        return None if value is None else bool(value&0xE0)

    @property
    def overflow_pending(self):
        from .interrupts import enabled_flag_request
        return enabled_flag_request(self.atu.regs[TSR0],self.atu.regs[TIER0],0x10)

    def advance_phi(self,count):
        a=self.atu
        if not self.enabled or not a.known(TSTR1)&1:return
        self.guard_start()
        divisor=a.known(PSCR1)+1
        ticks=(a.phi_cycles+count)//divisor-a.phi_cycles//divisor
        before=a.known(TCNT0);total=before+ticks;flags=0
        for address,first,flag in zip(ITVRR,(6,10,10),(0x20,0x40,0x80)):
            controls=a.known(address)
            for n in range(4):
                bit=first+n;half=1<<bit;period=half*2
                rises=(total+half)//period-(before+half)//period
                if rises and controls&(1<<n):flags|=flag
        if total>>32:flags|=0x10
        self.counter_ticks+=ticks;a.regs[TCNT0]=total&0xFFFFFFFF
        if flags:
            a.regs[TSR0]|=flags
            event={'kind':'counter0_status','counter':a.regs[TCNT0],
                'tick':self.counter_ticks,'time_unit':'explicit_counter0_selected_ticks',
                'status_flags':flags,'interval_request':self.interval_pending,
                'overflow_request':self.overflow_pending}
            a.events.append(event);a.events[:]=a.events[-100:]
            if a.event_sink:a.event_sink(dict(event))
