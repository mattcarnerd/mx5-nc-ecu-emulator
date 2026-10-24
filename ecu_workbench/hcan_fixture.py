"""Opt-in CAN completion inputs; delays are artificial instruction scheduling only."""
from .known_bits import KnownBits

def normalize_hcan_fixture(fixture):
    if fixture is None:return None
    if not isinstance(fixture,dict) or not {'reset_completion_ticks','recessive_bus_ticks'}<=set(fixture) or set(fixture)-{'reset_completion_ticks','recessive_bus_ticks','defer_mailbox_effects','preserve_supplied_reset_status'}:
        raise ValueError('HCAN fixture requires exactly reset_completion_ticks and recessive_bus_ticks')
    result={}
    for key,value in fixture.items():
        if key in ('defer_mailbox_effects','preserve_supplied_reset_status'):
            if type(value) is not bool:raise ValueError('Mailbox effect deferral must be boolean')
            result[key]=value
            continue
        if value is not None and (type(value) is not int or not 1<=value<=1000000):
            raise ValueError('HCAN supplied event delay must be1..1000000 or omitted')
        result[key]=value
    if result.get('preserve_supplied_reset_status') and not result.get('defer_mailbox_effects'):
        raise ValueError('Reset-status isolation requires explicit mailbox effect deferral')
    if all(v is None or v is False for v in result.values()):raise ValueError('At least one explicit HCAN completion input required')
    return result

def bind_hcan_fixture(cpu,fixture):
    fixture=normalize_hcan_fixture(fixture)
    if fixture is None:return
    if cpu.hcan_fixture is not None:raise ValueError('HCAN fixture already bound')
    cpu.hcan_fixture=fixture
    cpu.hcan_fixture_input_events+=1
    module=cpu.bus.hcan
    module.defer_mailbox_effects=fixture.get('defer_mailbox_effects',False)
    module.preserve_supplied_reset_status=fixture.get('preserve_supplied_reset_status',False)
    def requested(channel,value,generation,prior_status):
        key='reset_completion_ticks' if value else 'recessive_bus_ticks'
        delay=fixture[key]
        if delay is None:return
        if not value and prior_status.mask&8 and prior_status.value&8:
            module.gsr[channel]=KnownBits(8,8)  # explicit fixture holds reset until declared bus event
        cpu.scheduled_peripheral_events+=1
        def complete():
            if module.generations[channel]!=generation:return
            if module.effect_unknown_channels[channel]:
                if module.preserve_supplied_reset_status:
                    cpu.hcan_fixture_input_events+=1
                    module.gsr[channel]=KnownBits(8 if value else 0,8)
                    module.trace.append({'register':f'GSR_{channel}','access':'supplied_reset_status_only',
                                         'known_value':module.gsr[channel].value,'known_mask':8,
                                         'scope':'explicit_reset_status_isolation_unresolved_mailbox_effects_retained'})
                    return
                module.trace.append({'register':f'GSR_{channel}','access':'supplied_event_not_applied','scope':'unresolved_mailbox_effects'})
                return
            cpu.hcan_fixture_input_events+=1
            if value:module.complete_reset_subset(channel)
            module.gsr[channel]=KnownBits(0xC,0x3F) if value else KnownBits(0,8)
            module.trace.append({'register':f'GSR_{channel}','access':'supplied_event',
                'event':'reset_completion' if value else 'eleven_recessive_bits',
                'known_value':module.gsr[channel].value,'known_mask':module.gsr[channel].mask,
                'tick':cpu.clock.ticks,'time_unit':'completed_instruction_ticks',
                'scope':'explicit_synthetic_completion_input_not_physical_timing'})
        cpu.clock.schedule(cpu.clock.ticks+delay,complete)
    module.on_request=requested
