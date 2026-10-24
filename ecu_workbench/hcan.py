"""B44 HCAN MCR reset-release requests only, Rev.3 table16.4/16.4.2.

No CAN bus synchronization, frames, acknowledgements or GSR transitions are
invented. MCR reserved-bit6 readback is explicitly not guaranteed by the manual.
"""
MCR_ADDRESSES=(0xFFFFD000,0xFFFFD800)

class HcanResetCommands:
    def __init__(self,*,power_on,trace,stop_type):
        self.commands=[1 if power_on else None for _ in MCR_ADDRESSES]
        self.release_requests=[False,False]
        self.trace,self.stop_type=trace,stop_type

    def _channel(self,address,width,access):
        if width==2 and address in MCR_ADDRESSES:return MCR_ADDRESSES.index(address)
        raise self.stop_type('unsupported_access_size','HCAN MCR requires aligned word access',
                             address=address,width=width,access=access)

    def write(self,address,width,value):
        channel=self._channel(address,width,'write')
        value &= 0xFFFF
        if value!=0:
            raise self.stop_type('unsupported_peripheral_mode','Only observed HCAN reset-release word zero is modelled',
                                 address=address,width=width,access='write',value=value)
        self.commands[channel]=0
        self.release_requests[channel]=True
        self.trace.append({'register':f'MCR_{channel}','access':'write','width':2,'value':0,
                           'scope':'CAN_reset_release_request_only','bus_synchronization':'unknown'})

    def read(self,address,width):
        channel=self._channel(address,width,'read')
        raise self.stop_type('unknown_peripheral_reset_state',
            f'MCR_{channel} full-word readback includes unspecified reserved bit6; no value fabricated',
            address=address,width=width,access='read')
