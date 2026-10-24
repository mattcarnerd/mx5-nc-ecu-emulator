from .known_bits import KnownBits
"""B44 HCAN MCR reset-release requests only, Rev.3 table16.4/16.4.2.

No CAN bus synchronization, frames, acknowledgements or GSR transitions are
invented. MCR reserved-bit6 readback is explicitly not guaranteed by the manual.
"""
MCR_ADDRESSES=(0xFFFFD000,0xFFFFD800)

class HcanResetCommands:
    def __init__(self,*,power_on,trace,stop_type):
        self.commands=[1 if power_on else None for _ in MCR_ADDRESSES]
        self.release_requests=[False,False]
        self.mailbox_writes={}
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

    @staticmethod
    def mailbox_region(address):
        return any(base <= address < base+0x400 for base in (0xFFFFD100,0xFFFFD900))

    def mailbox_write(self,address,width,value):
        base=0xFFFFD100 if address<0xFFFFD900 else 0xFFFFD900
        channel=int(base==0xFFFFD900)
        mailbox,offset=divmod(address-base,32)
        if width!=2 or offset%2 or offset>0x12:
            raise self.stop_type('unsupported_access_size','Mailbox initialization supports aligned documented words only',
                                 address=address,width=width,access='write',value=value)
        inactive=offset==4 and value in (0x0700,0x2700)
        if value & 0xFFFF and not inactive:
            raise self.stop_type('unsupported_peripheral_mode','Only zero mailbox initialization is modelled',
                                 address=address,width=width,access='write',value=value)
        self.mailbox_writes[address]=value & 0xFFFF
        self.trace.append({'register':f'MB{mailbox}_{channel}+{offset:02X}',
                           'access':'write','width':2,'value':value & 0xFFFF,
                           'scope':'mailbox_inactive_command' if inactive else 'mailbox_zero_initialization_only'})

    def mailbox_read(self,address,width):
        raise self.stop_type('unknown_peripheral_reset_state',
            'Mailbox readback and CAN receive state are outside initialization-only support',
            address=address,width=width,access='read')

    def read_known_word(self,address):
        channel=self._channel(address,2,'read')
        command=self.commands[channel]
        if command is None:
            raise self.stop_type('unknown_peripheral_reset_state','MCR prior command state unknown',
                                 address=address,width=2,access='read')
        self.trace.append({'register':f'MCR_{channel}','access':'read','width':2,
                           'known_value':command,'known_mask':0xFFBF,'unknown_mask':0x0040})
        return KnownBits(command,0xFFBF)
