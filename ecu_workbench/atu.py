"""ATU-II channel1A/GR1A subset; explicit selected-counter-clock ticks only."""
TSTR=0xFFFFF401
PSCR=0xFFFFF404
TCNT=0xFFFFF440
GR=0xFFFFF444
GRB=0xFFFFF446
TIOR=0xFFFFF459
TCR=0xFFFFF45D
TSR=0xFFFFF45E
TIER=0xFFFFF462
WIDTHS={PSCR:1,TSTR:1,TCNT:2,GR:2,GRB:2,TIOR:1,TCR:1,TSR:2,TIER:2}

class Atu1A:
    def __init__(self,*,power_on,trace,stop_type):
        self.trace,self.stop_type=trace,stop_type
        self.regs={a:(0xFFFF if a in (GR,GRB) else 0) if power_on else None for a in WIDTHS}
        self.read_flags=0;self.ticks=0;self.clock_supplied=False;self.pin=None;self.pin_b=None
        self.events=[]
        self.event_sink=None;self.explicit_input_events=0
        self.clock_mode=None;self.phi_cycles=0;self.fixture_phase=None;self.clock_pins={'A':None,'B':None}

    def handles(self,a):return a in WIDTHS or a-1 in (TCNT,GR,GRB,TSR,TIER)

    def fail(self,kind,detail,a=None,width=None,access=None):
        raise self.stop_type(kind,detail,address=a,width=width,access=access)

    def known(self,a):
        if self.regs[a] is None:self.fail('unknown_peripheral_reset_state','ATU manual prior state unknown',a,WIDTHS[a],'read')
        return self.regs[a]

    def guard(self,a,width,access):
        if WIDTHS.get(a)!=width:self.fail('unsupported_access_size','ATU1A subset requires documented aligned access',a,width,access)

    @property
    def interrupt_pending(self):
        if self.regs[TSR] is None or self.regs[TIER] is None:return None
        return bool(self.regs[TSR]&self.regs[TIER]&0x103)

    def event(self,kind,*,counter=None,tick=None,**details):
        self.events.append({'kind':kind,'counter':self.regs[TCNT] if counter is None else counter,'tick':self.ticks if tick is None else tick,
                            'time_unit':'explicit_selected_counter_ticks','interrupt_request':self.interrupt_pending,**details})
        self.events[:]=self.events[-100:]
        if self.event_sink:self.event_sink(dict(self.events[-1]))

    def read(self,a,width):
        self.guard(a,width,'read')
        if a==TCNT and self.known(TSTR)&2 and not self.clock_supplied:
            self.fail('missing_input','Running ATU counter needs explicit selected-clock ticks',a,width,'read')
        value=self.known(a)
        if a==TSR:self.read_flags|=value
        return value

    def write(self,a,width,value):
        self.guard(a,width,'write');value &= (1<<(8*width))-1
        allowed={TSTR:(0,2),TIOR:tuple(low|(high<<4) for low in range(8) for high in (0,4,5,6,7)),TCR:tuple(range(6))+tuple(select|(edge<<4) for select in (6,7) for edge in range(4)),PSCR:tuple(range(32)),TIER:(0,1,2,3,0x100,0x101,0x102,0x103)}
        if a in allowed and value not in allowed[a]:
            self.fail('unsupported_peripheral_mode','Other ATU channels/clock modes outside bounded1A subset',a,width,'write')
        if a in (TCR,PSCR) and value!=self.regs[a]:
            if self.clock_mode is not None or self.known(TSTR)&2:
                self.fail('unsupported_peripheral_mode','Configure clock before running/binding fixture; phase changes outside subset',a,width,'write')
        if a==TSR:
            old=self.known(a)
            self.regs[a]=old & ~(self.read_flags & ~value & 0x103)
            self.read_flags=0;self.event('status_write');return
        if a in (GR,GRB) and ((self.known(TIOR)>>(4 if a==GRB else 0))&4):self.fail('read_only_peripheral','GR1A cannot be written in capture mode',a,width,'write')
        self.regs[a]=value
        self.trace.append({'register':f'ATU1A_{a:08X}','access':'write','width':width,'value':value})

    def begin_clock_fixture(self,*,phase):
        if type(phase) is not int or phase!=0:raise ValueError('Only explicitly declared zero phase fixture supported')
        if self.clock_mode is not None:raise ValueError('Clock fixture already bound; do not mix clock domains')
        self.known(PSCR)
        if self.known(TCR) not in range(6):self.fail('unsupported_peripheral_mode','Internal fixture requires internal clock selection')
        self.clock_mode='supplied_phi';self.fixture_phase=phase
        self.explicit_input_events+=1

    def begin_external_clock_fixture(self):
        if self.clock_mode is not None:raise ValueError('Clock fixture already bound')
        if self.known(TCR)&15 not in (6,7):self.fail('unsupported_peripheral_mode','External fixture requires TCLKA or TCLKB')
        self.clock_mode='external_pin'
        self._advance_counter_ticks(0)

    def set_clock_pin(self,pin,level):
        if pin not in ('A','B') or type(level) is not bool:raise ValueError('Explicit TCLKA/B boolean level required')
        if self.clock_mode!='external_pin':raise ValueError('Bind external clock fixture first')
        control=self.known(TCR);old=self.clock_pins[pin]
        selected=pin==('A' if control&15==6 else 'B')
        edge=(control>>4)&3
        accepted=(selected and old is not None and old!=level and
                  (edge==2 or edge==0 and level or edge==1 and not level))
        self._advance_counter_ticks(1 if accepted else 0)
        self.clock_pins[pin]=level

    def clock_report(self):
        return {'source':self.clock_mode,'fixture_phase_origin':self.fixture_phase,
                'supplied_phi_cycles':self.phi_cycles,'selected_counter_ticks':self.ticks,
                'frequency_hz':None,'physical_timing_verified':False}

    def advance_phi_cycles(self,count):
        if type(count) is not int or count<0:raise ValueError('Nonnegative supplied phi packet required')
        if self.clock_mode!='supplied_phi':raise ValueError('Declare the zero-phase clock fixture first')
        select=self.known(TCR)
        if select not in range(6):self.fail('unsupported_peripheral_mode','Internal clock packet requires internal selection')
        divisor=(self.known(PSCR)+1)*(1<<select)
        pulses=(self.phi_cycles+count)//divisor-self.phi_cycles//divisor
        self._advance_counter_ticks(pulses)
        self.phi_cycles+=count

    def advance_ticks(self,count):
        if type(count) is not int or count<0:raise ValueError('Nonnegative selected-clock packet required')
        if self.clock_mode not in (None,'selected_counter_ticks'):raise ValueError('Do not mix selected ticks and supplied phi')
        self._advance_counter_ticks(count)
        self.clock_mode='selected_counter_ticks'

    def _advance_counter_ticks(self,count):
        if type(count) is not int or count<0:raise ValueError('Nonnegative integer selected-clock ticks required')
        running=self.known(TSTR)&2;start=self.known(TCNT);mode=self.known(TIOR)&7
        events=[]
        if running and count:
            if mode in (1,2,3):
                distance=(self.known(GR)-start)&0xFFFF
                if distance==0:distance=65536
                if count>=distance:events.append((distance,'compare_match',self.regs[GR],1,1+(count-distance)//65536))
            distance=65536-start
            if count>=distance:events.append((distance,'counter_overflow',0,0x100,1+(count-distance)//65536))
        if events:self.known(TSR)
        self.explicit_input_events+=1;self.clock_supplied=True
        origin=self.ticks;self.ticks+=count
        if not running:return
        for distance,kind,counter,flag,occurrences in sorted(events):
            self.regs[TSR]|=flag
            self.event(kind,counter=counter,tick=origin+distance,occurrences=occurrences,
                       last_tick=origin+distance+(occurrences-1)*65536)
        self.regs[TCNT]=(start+count)&0xFFFF

    def set_pin(self,level,channel="A"):
        if type(level) is not bool:raise ValueError('Explicit boolean TIO1A level required')
        if channel not in ("A","B"):raise ValueError("Capture channel must be A or B")
        self.explicit_input_events+=1
        name="pin" if channel=="A" else "pin_b"
        old=getattr(self,name);setattr(self,name,level)
        mode=(self.known(TIOR)>>(4 if channel=="B" else 0))&7
        if old is None or old==level:return
        if mode not in (5,6,7) or (mode==5 and not level) or (mode==6 and level):return
        value=self.read(TCNT,2)
        self.regs[GR if channel=='A' else GRB]=value
        self.regs[TSR]=self.known(TSR)|(1 if channel=='A' else 2)
        self.event('input_capture_'+channel)
