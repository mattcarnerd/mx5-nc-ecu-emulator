"""Explicit artificial Pphi packets for separate startup investigation only."""

def normalize_startup_timer_fixture(value):
    if value is None:return None
    if not isinstance(value,dict) or set(value)!={'p_phi_cycles_per_instruction','channel10_initial_candidates','zero_reload_policy'}:
        raise ValueError('Startup timer fixture requires explicit Pphi ratio, A/C/F candidates and zero-reload policy')
    ratio=value['p_phi_cycles_per_instruction'];initial=value['channel10_initial_candidates']
    if type(ratio) is not int or not 1<=ratio<=1000000:raise ValueError('Startup Pphi ratio must be1..1000000')
    if not isinstance(initial,dict) or set(initial)!={'A','C','F'} or any(type(v) is not int or v not in (0,1) for v in initial.values()):
        raise ValueError('Startup channel10 A/C/F candidates must each be integer0 or1')
    policy=value['zero_reload_policy']
    if policy not in (None,'experimental-wrap16'):raise ValueError('Invalid startup zero-reload policy')
    return {'p_phi_cycles_per_instruction':ratio,'channel10_initial_candidates':dict(initial),'zero_reload_policy':policy}


def bind_startup_timer_fixture(cpu,value):
    fixture=normalize_startup_timer_fixture(value)
    if fixture is None:return None
    a=cpu.bus.atu
    if a.on_start is not None or a.clock_mode is not None:raise ValueError('Startup timer fixture already configured')
    a.channel10.set_initial_candidates(fixture['channel10_initial_candidates'],zero_reload_policy=fixture['zero_reload_policy'])
    state={'fixture':fixture,'bound_tick':None,'completed_packets':0,
           'phase_origin':0,'bind_on':'first_nonzero_TSTR1_write',
           'packet_order':'scheduled_completed_instruction_before_watchdog_phi',
           'correction_order':'old-state_Pphi_tick'}
    def packet():
        from .nc_boot import BootStop
        try:a.advance_phi_cycles(fixture['p_phi_cycles_per_instruction'])
        except BootStop:
            cpu._active_instruction=None;cpu._fetch_pc=cpu.pc
            raise
        state['completed_packets']+=1
        cpu.clock.schedule(cpu.clock.ticks+1,packet);cpu.scheduled_peripheral_events+=1
    def start(value):
        if state['bound_tick'] is not None:return
        # No fixture/clock/scheduled-event mutation on an unsupported request.
        a.upcounter_bank.guard_start(value&0x7F)
        if value&0x80:a.channel10.guard_start()
        a.begin_startup_timer_clock_fixture(phase=0)
        state['bound_tick']=cpu.clock.ticks
        cpu.clock.schedule(cpu.clock.ticks+1,packet);cpu.scheduled_peripheral_events+=1
    a.on_start=start
    return state
