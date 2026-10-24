"""B27 bounded execution coverage and explicit-event diagnostic harness."""
from collections import Counter

class ExecutionCoverage:
    EVENT_LIMIT=100
    PC_REPORT_LIMIT=256

    def __init__(self):
        self.visits=Counter()
        self.completed=0
        self.delay_slots=0
        self.completed_delay_slots=0
        self.current_pc=None
        self.bus_failure_count=0
        self.unsupported_bus_count=0
        self.bus_failure_reasons=Counter()
        self.bus_failure_events=[]

    def fetched(self,pc,delay_slot):
        self.visits[pc]+=1
        self.delay_slots+=int(delay_slot)

    def instruction_completed(self,delay_slot):
        self.completed+=1
        self.completed_delay_slots+=int(delay_slot)

    def bus_failed(self,error,address,width,access,value=None):
        self.bus_failure_count+=1
        self.bus_failure_reasons[error.kind]+=1
        if error.kind in ('unmodelled_peripheral','unsupported_access_size','unsupported_peripheral_mode'):
            self.unsupported_bus_count+=1
        event={'reason':error.kind,'address':f'0x{address:08X}','width':width,'access':access,
               'instruction_pc':None if self.current_pc is None else f'0x{self.current_pc:08X}'}
        if value is not None:event['value']=f'0x{value:08X}'
        self.bus_failure_events.append(event)
        if len(self.bus_failure_events)>self.EVENT_LIMIT:del self.bus_failure_events[0]

    def report(self):
        pcs=sorted(self.visits)
        return {'kind':'bounded_execution_diagnostic','fetched_instructions':sum(self.visits.values()),
                'completed_instructions':self.completed,'unique_instruction_pcs':len(pcs),
                'repeated_pc_visits':sum(n-1 for n in self.visits.values()),
                'max_pc_visits':max(self.visits.values(),default=0),
                'attempted_delay_slots':self.delay_slots,'completed_delay_slots':self.completed_delay_slots,
                'pc_visits':{f'0x{p:08X}':self.visits[p] for p in pcs[:self.PC_REPORT_LIMIT]},
                'pc_list_truncated':len(pcs)>self.PC_REPORT_LIMIT,
                'bus_failure_count':self.bus_failure_count,'unsupported_bus_access_count':self.unsupported_bus_count,
                'bus_failures_by_reason':dict(sorted(self.bus_failure_reasons.items())),
                'bus_failures':list(self.bus_failure_events),
                'bus_failure_events_dropped':max(0,self.bus_failure_count-self.EVENT_LIMIT),
                'note':'Repeated PC visits and instruction limits do not prove ECU boot or an engine loop.'}


def run_execution_harness(rom,*,max_steps=300,reset='power',nmi_high=None,
                          hudi_scenario='unknown',interval_events=()):
    """Same bounded CPU, with explicit {'tick': int, 'asserted': bool} ITI events.

    No module overflow/physical time is inferred. All input events are validated
    before execution, and even not-yet-fired events retain injection provenance.
    """
    from .nc_boot import NCBootDiagnostic
    if type(max_steps) is not int or not 1<=max_steps<=100000:
        raise ValueError('max_steps must be an integer in 1..100000')
    if not isinstance(interval_events,(list,tuple)):
        raise ValueError('interval_events must be an ordered list or tuple')
    for event in interval_events:
        if (not isinstance(event,dict) or set(event)!= {'tick','asserted'} or
            type(event['tick']) is not int or event['tick']<0 or type(event['asserted']) is not bool):
            raise ValueError('Each ITI event needs an integer tick and boolean asserted level')
    cpu=NCBootDiagnostic(rom,reset=reset,nmi_high=nmi_high,hudi_scenario=hudi_scenario)
    cpu.scheduled_interrupt_events=len(interval_events)
    for event in interval_events:
        cpu.clock.schedule(event['tick'],lambda asserted=event['asserted']:cpu.set_interval_request(asserted))
    result=cpu.run(max_steps)
    result['harness']={'max_steps':max_steps,'scheduled_interval_events':len(interval_events),
                       'event_time_unit':'completed_instruction_ticks','boot_complete':False}
    return result
