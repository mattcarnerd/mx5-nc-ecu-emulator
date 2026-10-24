"""ATU-II channel1A/GR1A subset; explicit selected-counter-clock ticks only."""
TSTR=0xFFFFF401
TCNT=0xFFFFF440
GR=0xFFFFF444
TIOR=0xFFFFF459
TCR=0xFFFFF45D
TSR=0xFFFFF45E
TIER=0xFFFFF462
WIDTHS={TSTR:1,TCNT:2,GR:2,TIOR:1,TCR:1,TSR:2,TIER:2}

class Atu1A:
    def __init__(self,*,power_on,trace,stop_type):
        self.trace,self.stop_type=trace,stop_type
        self.regs={a:(0xFFFF if a==GR else 0) if power_on else None for a in WIDTHS}
        self.read_flags=0;self.ticks=0;self.clock_supplied=False;self.pin=None
        self.events=[]

    def handles(self,a):return a in WIDTHS or a-1 in (TCNT,GR,TSR,TIER)

    def fail(self,kind,detail,a=None,width=None,access=None):
        raise self.stop_type(kind,detail,address=a,width=width,access=access)

    def known(self,a):
        if self.regs[a] is None:self.fail('unknown_peripheral_reset_state','ATU manual prior state unknown',a,WIDTHS[a],'read')
        return self.regs[a]

    def guard(self,a,width,access):
        if WIDTHS.get(a)!=width:self.fail('unsupported_access_size','ATU1A subset requires documented aligned access',a,width,access)

    @property
    def interrupt_pending(self):return bool((self.regs[TSR] or 0)&(self.regs[TIER] or 0)&1)

    def event(self,kind):
        self.events.append({'kind':kind,'counter':self.regs[TCNT],'tick':self.ticks,
                            'time_unit':'explicit_selected_counter_ticks','interrupt_request':self.interrupt_pending})
        self.events[:]=self.events[-100:]

    def read(self,a,width):
        self.guard(a,width,'read')
        if a==TCNT and self.known(TSTR)&2 and not self.clock_supplied:
            self.fail('missing_input','Running ATU counter needs explicit selected-clock ticks',a,width,'read')
        value=self.known(a)
        if a==TSR:self.read_flags|=value
        return value

    def write(self,a,width,value):
        self.guard(a,width,'write');value &= (1<<(8*width))-1
        allowed={TSTR:(0,2),TIOR:tuple(range(8)),TCR:(0,),TIER:(0,1)}
        if a in allowed and value not in allowed[a]:
            self.fail('unsupported_peripheral_mode','Other ATU channels/clock modes outside bounded1A subset',a,width,'write')
        if a==TSR:
            old=self.known(a)
            self.regs[a]=old & ~(self.read_flags & ~value & 1)
            self.read_flags=0;self.event('status_write');return
        if a==GR and self.known(TIOR)&4:self.fail('read_only_peripheral','GR1A cannot be written in capture mode',a,width,'write')
        self.regs[a]=value
        self.trace.append({'register':f'ATU1A_{a:08X}','access':'write','width':width,'value':value})

    def advance_ticks(self,count):
        if type(count) is not int or count<0:raise ValueError('Nonnegative integer selected-clock ticks required')
        self.known(TSTR);self.known(TCNT);self.known(TIOR)
        self.clock_supplied=True
        start=self.regs[TCNT];self.ticks+=count
        if not self.regs[TSTR]&2:return
        if self.regs[TIOR] in (1,2,3):
            distance=(self.known(GR)-start)&0xFFFF
            if distance==0:distance=65536
            if count>=distance:self.regs[TSR]=self.known(TSR)|1;self.event('compare_match')
        self.regs[TCNT]=(start+count)&0xFFFF

    def set_pin(self,level):
        if type(level) is not bool:raise ValueError('Explicit boolean TIO1A level required')
        old=self.pin;self.pin=level
        mode=self.known(TIOR)
        if old is None or old==level:return
        if mode not in (5,6,7) or (mode==5 and not level) or (mode==6 and level):return
        value=self.read(TCNT,2)
        self.regs[GR]=value;self.regs[TSR]=self.known(TSR)|1;self.event('input_capture')
