"""Bounded explicit-Pphi upcounters; stop before unimplemented events.

Rev3 11.2.15/18/20: no fake compare flags, capture, clear or pulse effects.
The comparator registers below remain documented resetFFFF because their
CPU writes are still unmodelled. They are unknown after manual reset.
"""
MEMBERS={
    0xFFFFF442:(0xFFFFF45C,8,(0xFFFFF454,)),
    0xFFFFF600:(0xFFFFF62B,4,tuple(0xFFFFF604+2*i for i in range(8))),
    0xFFFFF602:(0xFFFFF62A,8,tuple(0xFFFFF614+2*i for i in range(8))),
    0xFFFFF4A0:(0xFFFFF4AC,0x10,tuple(0xFFFFF4A2+2*i for i in range(4))),
    0xFFFFF4C0:(0xFFFFF4CC,0x20,tuple(0xFFFFF4C2+2*i for i in range(4))),
    0xFFFFF4E0:(0xFFFFF4EC,0x40,tuple(0xFFFFF4E2+2*i for i in range(4)))}
TSTR=0xFFFFF401
PSCR=0xFFFFF404
TCNT1A=0xFFFFF440
TCR1A=0xFFFFF45D
EXTRA_GR1=tuple(0xFFFFF448+2*i for i in range(6))

class UpcounterBankRuntime:
    def __init__(self,atu,*,power_on):
        self.atu=atu;self.enabled=False
        addresses={x for _,_,comparators in MEMBERS.values() for x in comparators}|set(EXTRA_GR1)
        self.comparators={x:0xFFFF if power_on else None for x in addresses}

    def guard_start(self,value):
        a=self.atu
        if value&~0x7F:a.fail('unsupported_peripheral_mode','Channel10 runtime outside upcounter-bank subset',TSTR,1,'write',value)
        a.counter0.guard_start()
        if not a.channel8_quiescent():a.fail('unsupported_peripheral_mode','Counter bank requires proven quiescent channel8')
        active=[(address,tcr,comparators) for address,(tcr,bit,comparators) in MEMBERS.items() if value&bit]
        if value&2:
            active.append((TCNT1A,TCR1A,EXTRA_GR1))
            for address in (0xFFFFF459,0xFFFFF45E,0xFFFFF462,0xFFFFF444,0xFFFFF446):a.known(address)
        for address,tcr,comparators in active:
            a.known(address);select=a.known(tcr)&15
            if select>5:a.fail('unsupported_peripheral_mode','Counter bank requires internal clocks0..5',tcr,1,'read')
            if any(self.comparators[x] is None for x in comparators):
                a.fail('unknown_peripheral_reset_state','Unmodelled retained comparator state unknown',address,2,'read')

    def bind(self,*,phase):
        if self.enabled:raise ValueError('Upcounter bank already bound')
        self.guard_start(self.atu.known(TSTR))
        self.atu.counter0.bind(phase=phase);self.enabled=True

    def prepare(self,count):
        if not self.enabled:return {}
        a=self.atu;running=a.known(TSTR);self.guard_start(running)
        plan={}
        active=[(address,tcr,comparators) for address,(tcr,bit,comparators) in MEMBERS.items() if running&bit]
        if running&2:active.append((TCNT1A,TCR1A,EXTRA_GR1))
        for address,tcr,comparators in active:
            divisor=(a.known(PSCR)+1)*(1<<(a.known(tcr)&15))
            ticks=(a.phi_cycles+count)//divisor-a.phi_cycles//divisor
            before=a.known(address)
            # TCNT1A overflow is implemented, but an extra GR1C-H match is not.
            distance=65536-before if address!=TCNT1A else 65537
            for comparator in comparators:
                delta=(self.comparators[comparator]-before)&0xFFFF
                distance=min(distance,delta or 65536)
            if ticks>=distance:
                a.fail('unsupported_peripheral_mode',
                    'Counter-bank packet reaches unmodelled compare/overflow; packet not applied',address,2)
            if address!=TCNT1A:plan[address]=(before+ticks)&0xFFFF
        return plan
