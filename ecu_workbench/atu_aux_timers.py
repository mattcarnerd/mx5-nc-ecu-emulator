"""Optional timer6/7/11 counts until an unimplemented compare/overflow.

Rev3 11.2.15/20/22/24. No PWM/APC output, compare flag or IRQ is dropped:
packets reaching those boundaries stop before any timer state changes.
"""
TSTR2=0xFFFFF400;TSTR3=0xFFFFF402;PMDR=0xFFFFF526
MEMBERS={
    **{0xFFFFF500+2*i:(TSTR2,1<<i,0xFFFFF406,
         0xFFFFF521 if i<2 else 0xFFFFF520,4*(i%2),
         (0xFFFFF508+2*i,0xFFFFF518+2*i)) for i in range(4)},
    **{0xFFFFF580+2*i:(TSTR2,0x10<<i,0xFFFFF408,
         0xFFFFF5A1 if i<2 else 0xFFFFF5A0,4*(i%2),
         (0xFFFFF588+2*i,0xFFFFF598+2*i)) for i in range(4)},
    0xFFFFF5C0:(TSTR3,1,0xFFFFF404,0xFFFFF5C8,0,(0xFFFFF5C2,0xFFFFF5C4))}

class AuxiliaryTimerRuntime:
    def __init__(self,atu,*,power_on):
        self.atu=atu;self.enabled=False
        self.comparators={x:0xFFFF if power_on else None for *_,comparators in MEMBERS.values() for x in comparators}

    def guard_start(self,start,value):
        a=self.atu
        if start==TSTR3 and value&0xFE:
            a.fail('invalid_peripheral_write','TSTR3 reserved bits7..1 require zero',start,1,'write',value)
        if start==TSTR2 and value&15 and a.known(PMDR)!=0:
            a.fail('unsupported_peripheral_mode','Timer6 runtime requires supported PMDR0 mode',PMDR,1,'read')
        for address,(register,bit,prescaler,tcr,shift,comparators) in MEMBERS.items():
            if register!=start or not value&bit:continue
            a.known(address);a.known(prescaler)
            selector=(a.known(tcr)>>shift)&7
            if selector>5:a.fail('unsupported_peripheral_mode','Auxiliary timer requires internal divisor0..5',tcr,1,'read')
            if any(self.comparators[x] is None for x in comparators):
                a.fail('unknown_peripheral_reset_state','Auxiliary retained compare state unknown',address,2,'read')

    def prepare(self,count):
        if not self.enabled:return {}
        a=self.atu;starts={x:a.known(x) for x in (TSTR2,TSTR3)}
        for start,value in starts.items():self.guard_start(start,value)
        plan={}
        for address,(start,bit,prescaler,tcr,shift,comparators) in MEMBERS.items():
            if not starts[start]&bit:continue
            divisor=(a.known(prescaler)+1)*(1<<((a.known(tcr)>>shift)&7))
            ticks=(a.phi_cycles+count)//divisor-a.phi_cycles//divisor
            before=a.known(address);distance=65536-before
            for comparator in comparators:
                delta=(self.comparators[comparator]-before)&0xFFFF
                distance=min(distance,delta or 65536)
            if ticks>=distance:
                a.fail('unsupported_peripheral_mode','Auxiliary timer packet reaches unmodelled PWM/APC/compare/overflow; packet not applied',address,2)
            plan[address]=before+ticks
        return plan
