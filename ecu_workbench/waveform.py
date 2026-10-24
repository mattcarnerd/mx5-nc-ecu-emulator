"""Explicit synthetic square-wave crank/cam fixture, never an NC tooth pattern."""
from fractions import Fraction

def crank_cam_fixture(*,rpm,tick_hz,teeth,cam_phase_degrees,revolutions=2):
    rpm=Fraction(str(rpm));phase=Fraction(str(cam_phase_degrees))
    if rpm<=0 or type(tick_hz) is not int or tick_hz<=0:raise ValueError('Positive RPM and explicit selected-counter tick rate required')
    if type(teeth) is not int or not 1<=teeth<=360:raise ValueError('Synthetic teeth per revolution must be1..360')
    if type(revolutions) is not int or not 2<=revolutions<=100:raise ValueError('Revolutions must be2..100')
    if not 0<=phase<720:raise ValueError('Explicit cam phase must be0..719.999 degrees')
    revolution=Fraction(60*tick_hz,1)/rpm;end=revolution*revolutions
    events=[]
    for role,half_period,origin in (('crank',revolution/(2*teeth),Fraction(0)),('cam',revolution,revolution*phase/360)):
        at=origin;level=True;last=-1
        while at<end:
            tick=int(at)
            if tick<=last:raise ValueError('Tick resolution too low for distinct edges')
            events.append({'tick':tick,'role':role,'level':level})
            last=tick;level=not level;at+=half_period
    return {'kind':'synthetic_square_wave_fixture','validated_NC_pattern':False,'rpm':str(rpm),
            'selected_counter_tick_hz':tick_hz,'teeth_per_revolution':teeth,'cam_phase_degrees':str(phase),
            'duration_ticks':int(end),'events':sorted(events,key=lambda e:(e['tick'],e['role']))}

def play_fixture(timer,fixture):
    """Caller explicitly configures shared counter/capture modes; roles map A/B."""
    if fixture.get('kind')!='synthetic_square_wave_fixture':raise ValueError('Explicit synthetic fixture required')
    timer.set_pin(False,'A');timer.set_pin(False,'B')
    elapsed=0
    for event in fixture['events']:
        timer.advance_ticks(event['tick']-elapsed);elapsed=event['tick']
        timer.set_pin(event['level'],'A' if event['role']=='crank' else 'B')
    timer.advance_ticks(fixture['duration_ticks']-elapsed)
    return list(timer.events)
