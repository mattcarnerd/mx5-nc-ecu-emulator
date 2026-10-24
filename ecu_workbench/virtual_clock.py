"""B19 deterministic abstract clock; deliberately not hardware phi/cycle time."""
import heapq

class InstructionClock:
    def __init__(self):
        self.ticks=0
        self._sequence=0
        self._events=[]

    def schedule(self,at_tick,callback):
        if type(at_tick) is not int or at_tick<self.ticks:
            raise ValueError('Event tick must be an integer at or after current tick')
        if not callable(callback):raise TypeError('Event callback must be callable')
        heapq.heappush(self._events,(at_tick,self._sequence,callback))
        self._sequence+=1

    def dispatch_due(self):
        while self._events and self._events[0][0]<=self.ticks:
            _,_,callback=heapq.heappop(self._events)
            callback()

    def completed_instruction(self):
        self.ticks+=1
        self.dispatch_due()

    def report(self):
        return {'unit':'completed_instruction_ticks','ticks':self.ticks,
                'cpu_cycles':None,'seconds':None,'cycle_accurate':False,
                'pending_events':len(self._events)}


def phi_scenario_metadata(value):
    if value is not None and (type(value) is not int or not 1<=value<=1000000):
        raise ValueError('Assumed phi cycles per completed instruction must be 1..1000000 or unknown')
    return {'phi_cycles_per_instruction':value,'conditional_clock_scenario':value is not None,
            'phi_fixture_origin':None if value is None else 0,
            'clock_scenario_note':('Clock unknown; no instruction-to-phi ratio assumed.' if value is None else
                'Conditional artificial clock ratio and zero phi origin/phase; not measured CPU timing.')}
