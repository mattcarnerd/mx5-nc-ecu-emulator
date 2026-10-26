"""ATU-II channel1A/GR1A subset; explicit selected-counter-clock ticks only."""
TSTR=0xFFFFF401
PSCR=0xFFFFF404
TCNT=0xFFFFF440
GR=0xFFFFF444
GRB=0xFFFFF446
TIOR=0xFFFFF459
TCR1B=0xFFFFF45C
TCR2A=0xFFFFF62B
TCR2B=0xFFFFF62A
TCR3=0xFFFFF4AC
TCR4=0xFFFFF4CC
TCR5=0xFFFFF4EC
EXTRA_TCR_STOP={TCR1B:8,TCR2A:4,TCR2B:8,TCR3:0x10,TCR4:0x20,TCR5:0x40}
TCR=0xFFFFF45D
TSR=0xFFFFF45E
TIER=0xFFFFF462
PWM_TCR_STOP={0xFFFFF521:0x03,0xFFFFF520:0x0C,0xFFFFF5A1:0x30,0xFFFFF5A0:0xC0}
PMDR=0xFFFFF526
TMDR=0xFFFFF484
TRGMDR=0xFFFFF466
TCNR=0xFFFFF662
OTR=0xFFFFF664
ITVRR=(0xFFFFF424,0xFFFFF426,0xFFFFF428)
DSTR=0xFFFFF666
TSTR2=0xFFFFF400
TSTR3=0xFFFFF402
PSCR_EXTRA=(0xFFFFF406,0xFFFFF408,0xFFFFF40A)
WIDTHS={PMDR:1,**{a:1 for a in PWM_TCR_STOP},TCR3:1,TCR4:1,TCR5:1,TMDR:1,TCR2A:1,TCR2B:1,TRGMDR:1,TCNR:2,OTR:2,TCR1B:1,**{a:1 for a in ITVRR},DSTR:2,TSTR2:1,TSTR3:1,**{a:1 for a in PSCR_EXTRA},PSCR:1,TSTR:1,TCNT:2,GR:2,GRB:2,TIOR:1,TCR:1,TSR:2,TIER:2}

class Atu1A:
    def __init__(self,*,power_on,trace,stop_type):
        self.trace,self.stop_type=trace,stop_type
        self.regs={a:(0xFFFF if a in (GR,GRB) else 0) if power_on else None for a in WIDTHS}
        # Rev3 table11.3/11.2.11: no channel8 counter/reload writes are
        # supported yet. Retain documented power state, unknown on manual reset.
        self.channel8_counters=[0 if power_on else None for _ in range(16)]
        self.channel8_reload_value=0 if power_on else None
        self.channel8_reload_enabled=False if power_on else None
        self.read_flags=0;self.ticks=0;self.clock_supplied=False;self.pin=None;self.pin_b=None
        self.events=[]
        self.event_sink=None;self.explicit_input_events=0
        self.clock_mode=None;self.phi_cycles=0;self.fixture_phase=None;self.clock_pins={'A':None,'B':None}

    def handles(self,a):return a in WIDTHS or a-1 in (TCNT,GR,GRB,TSR,TIER,DSTR,TCNR,OTR)

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
        if a==PMDR and (value or self.known(TSTR2)&0x0F):
            self.fail('unsupported_peripheral_mode','PMDR subset accepts observed0 only with timer6 counters stopped; PWM outputs unmodelled',a,width,'write')
        if a in PWM_TCR_STOP:
            if value&0x88 or value&7>5 or (value>>4)&7>5:
                self.fail('invalid_peripheral_write','Timer6/7 clockfields require reserved7/3zero and selectors0..5',a,width,'write')
            if self.known(TSTR2)&PWM_TCR_STOP[a]:self.fail('unsupported_peripheral_mode','Configure timer6/7 clocks only while selected counters stopped',a,width,'write')
        if a==TMDR:
            if value&0xF8:self.fail('invalid_peripheral_write','TMDR reserved bits7..3 require zero',a,width,'write')
            if value or self.known(TSTR)&0x70:self.fail('unsupported_peripheral_mode','TMDR subset supports stopped channels3..5 and PWM disabled only',a,width,'write')
        if a in (TCNR,OTR) and value and not self.channel8_quiescent():
            self.fail('unsupported_peripheral_mode','Channel8 configuration requires proven zero downcounters and unavailable reload',a,width,'write')
        if a==TRGMDR:
            if value&0x7F:self.fail('invalid_peripheral_write','TRGMDR reserved bits6..0 require zero',a,width,'write')
            if not self.channel8_quiescent():
                self.fail('unsupported_peripheral_mode','TRGMDR subset requires proven quiescent channel8',a,width,'write')
        if a in EXTRA_TCR_STOP:
            if value&0xC0:self.fail('invalid_peripheral_write','TCR reserved bits7..6 require zero',a,width,'write')
            if value&0xF not in range(8):self.fail('unsupported_peripheral_mode','TCR AGCK/AGCKM clock outside subset',a,width,'write')
            if self.known(TSTR)&EXTRA_TCR_STOP[a]:self.fail('unsupported_peripheral_mode','TCR configuration requires its counter stopped',a,width,'write')
        if a in ITVRR and value and self.known(TSTR)&1:
            self.fail('unsupported_peripheral_mode','Interval/ADC trigger generation requires unmodelled TCNT0 execution',a,width,'write')
        if a==DSTR:
            if value:self.fail('unsupported_peripheral_mode','DSTR one-bit starts need unmodelled channel8 downcounters/triggers',a,width,'write')
            # Rev3 11.2.11: only1 can be written. Zero leaves all bits,
            # including retained unknown manual state, untouched.
            self.trace.append({'register':'DSTR','access':'write','width':2,'value':0,'scope':'write_zero_no_operation'})
            return
        if a in (TSTR2,TSTR3) and value!=0:
            self.fail('unsupported_peripheral_mode','Other ATU channel starts outside subset',a,width,'write')
        if a in PSCR_EXTRA:
            if value&0xE0:self.fail('invalid_peripheral_write','PSCR reserved bits7..5 require zero',a,width,'write')
            if any(self.known(start)!=0 for start in (TSTR,TSTR2,TSTR3)):
                self.fail('unsupported_peripheral_mode','Configure common prescaler only with all counters stopped',a,width,'write')
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

    def channel8_quiescent(self):
        return (self.regs[DSTR]==0 and all(v==0 for v in self.channel8_counters)
                and (self.channel8_reload_enabled is False or self.channel8_reload_value==0))

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
