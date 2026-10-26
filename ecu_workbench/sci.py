"""Stopped SCI configuration, SH7058 Rev.3 table15.2,15.2.5/.6/.8.

No serial clock, baud rate, pin activity, data arrival or SCI IRQ is generated.
"""
BASE=0xFFFFF000
class StoppedSci:
    def __init__(self,*,power_on,trace,stop_type):
        self.values=[[0,255,0] if power_on else [None,None,None] for _ in range(5)]
        self.trace,self.stop_type=trace,stop_type

    def handles(self,address):
        return BASE<=address<BASE+40 and (address-BASE)%8<3

    def access(self,address,width,access,value=None):
        channel,offset=divmod(address-BASE,8)
        def stop(kind,detail):
            raise self.stop_type(kind,detail,address=address,width=width,access=access,
                                 **({'value':value} if access=='write' else {}))
        if not 0<=channel<5 or offset>2 or not (width==1 or (width==2 and offset==0)):
            stop('unsupported_access_size','SCI stopped subset supports bytes SMR/BRR/SCR or paired SMR+BRR word')
        row=self.values[channel];indices=range(offset,offset+width)
        if access=='read':
            if any(row[i] is None for i in indices):
                stop('unknown_peripheral_reset_state','SCI configuration retained/unknown after manual reset')
            result=0
            for i in indices:result=(result<<8)|row[i]
        else:
            if offset==2:
                if value!=0:stop('unsupported_peripheral_mode','SCI enable/interrupt/clock-output behavior requires explicit runtime')
            elif row[2] is None or row[2]!=0:
                stop('unsupported_peripheral_mode','SCI configuration subset requires known disabled SCR')
            for i in indices:row[i]=(value>>(8*(offset+width-1-i)))&255
            result=None
        self.trace.append({'register':('SMR','BRR','SCR')[offset]+str(channel),
            'access':access,'width':width,'value':value if access=='write' else result,
            'scope':'stopped_sci_configuration_only'})
        return result
