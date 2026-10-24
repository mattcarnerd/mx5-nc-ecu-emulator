"""Validation/provenance for explicitly supplied AN0 ideal fixture."""
from fractions import Fraction

def normalize_adc_fixture(fixture):
    if fixture is None:return None
    if not isinstance(fixture,dict) or set(fixture)!={'voltage','reference','completion_ticks'}:
        raise ValueError('AN0 fixture requires voltage, reference and completion_ticks')
    if isinstance(fixture['voltage'],bool) or isinstance(fixture['reference'],bool):raise ValueError('Numeric voltages required')
    try:v,r=Fraction(str(fixture['voltage'])),Fraction(str(fixture['reference']))
    except (ValueError,ZeroDivisionError):raise ValueError('Finite numeric voltages required')
    ticks=fixture['completion_ticks']
    if r<=0 or not 0<=v<=r:raise ValueError('Require0 <= AN0 <= explicit positive reference')
    if type(ticks) is not int or not 1<=ticks<=1000000:raise ValueError('Artificial conversion delay must be1..1000000 completed instructions')
    return {'voltage':str(v),'reference':str(r),'completion_ticks':ticks}

def adc_fields(voltage,reference,ticks):
    values=[str(v).strip() if v is not None else '' for v in (voltage,reference,ticks)]
    if not any(values):return None
    if not all(values):raise ValueError('Supply AN0 voltage, reference and artificial completion delay together')
    return normalize_adc_fixture(dict(voltage=values[0],reference=values[1],completion_ticks=int(values[2])))
