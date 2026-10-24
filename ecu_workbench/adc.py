"""AN0 ideal conversion fixture, hardware Rev.3 section17. No assumed voltage/time."""
from fractions import Fraction
ADDR0=0xFFFFF800
ADCSR0=0xFFFFF818
ADCR0=0xFFFFF819

class Adc0:
    def __init__(self,*,power_on,trace,stop_type):
        self.trace,self.stop_type=trace,stop_type
        self.data=0 if power_on else None
        self.csr=0 if power_on else None
        self.cr=15 if power_on else None
        self.input=None;self.sample=None;self.read_adf=False;self.on_start=None;self.generation=0
        self.event_sink=None;self.explicit_input_events=0

    def handles(self,a):return a in (ADDR0,ADDR0+1,ADCSR0,ADCR0)

    def fail(self,kind,detail,a=None,width=None,access=None):
        raise self.stop_type(kind,detail,address=a,width=width,access=access)

    def set_input(self,voltage,reference):
        if isinstance(voltage,bool) or isinstance(reference,bool):raise ValueError('Numeric voltage and reference required')
        v,r=Fraction(str(voltage)),Fraction(str(reference))
        if r<=0 or v<0 or v>r:raise ValueError('Require 0 <= AN0 voltage <= explicit positive reference')
        self.input=(v,r)
        self.explicit_input_events+=1

    def known(self,value,a,width):
        if value is None:self.fail('unknown_peripheral_reset_state','ADC prior state unknown',a,width,'read')
        return value

    def read(self,a,width):
        if a==ADDR0 and width==2:return self.known(self.data,a,width)
        if a in (ADDR0,ADDR0+1) and width==1:
            value=self.known(self.data,a,width);return (value>>(8 if a==ADDR0 else 0))&255
        if a==ADCSR0 and width==2:return (self.read(a,1)<<8)|self.read(ADCR0,1)
        if a==ADCSR0 and width==1:
            value=self.known(self.csr,a,width);self.read_adf=bool(value&128);return value
        if a==ADCR0 and width==1:return self.known(self.cr,a,width)
        self.fail('unsupported_access_size','ADC0 aligned byte/word access required',a,width,'read')

    def write(self,a,width,value):
        if a in (ADDR0,ADDR0+1):self.fail('read_only_peripheral','ADDR0 is read-only',a,width,'write')
        if width!=1 or a not in (ADCSR0,ADCR0):
            self.fail('unsupported_access_size','ADC0 control subset supports byte writes',a,width,'write')
        value &=255
        if a==ADCSR0:
            if value&0x3F:self.fail('unsupported_peripheral_mode','Only AN0 single mode supported',a,width,'write')
            old=self.known(self.csr,a,width)
            adf=(old&128) if value&128 or not self.read_adf else 0
            self.csr=adf|(value&64);self.read_adf=False
        else:
            if value&0xD0:self.fail('unsupported_peripheral_mode','Only software-start single conversion CKS0 supported',a,width,'write')
            old=self.known(self.cr,a,width)
            starting=bool(value&32) and not bool(old&32)
            self.cr=(value&32)|15
            if not value&32:self.generation+=1;self.sample=None
            if starting:
                self.generation+=1;self.sample=self.input
                if self.event_sink:self.event_sink({"kind":"adc_start","generation":self.generation})
                if self.on_start:self.on_start(self.generation)
        self.trace.append({'register':'ADCSR0' if a==ADCSR0 else 'ADCR0','access':'write','width':1,'value':value})

    @property
    def interrupt_pending(self):return None if self.csr is None else (self.csr&0xC0)==0xC0

    def complete_conversion(self,generation=None):
        if generation is not None and generation!=self.generation:return
        if self.cr is None or not self.cr&32:return
        if self.sample is None:self.fail('missing_input','AN0 conversion needs explicit voltage and reference',ADDR0,2,'read')
        v,r=self.sample
        count=min(1023,int(v*1024/r))
        self.data=count<<6;self.cr=15;self.csr=self.known(self.csr,ADCSR0,1)|128
        if self.event_sink:self.event_sink({'kind':'adc_complete','count':count,'value':self.data,'generation':self.generation})
        self.trace.append({'register':'ADDR0','access':'conversion','value':self.data,'count':count,
                           'scope':'explicit_ideal_AN0_fixture','completion':'explicit_event',
                           'interrupt_request':self.interrupt_pending})
