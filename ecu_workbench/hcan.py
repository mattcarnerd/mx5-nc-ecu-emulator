from .known_bits import KnownBits
"""HCAN MCR reset/release command subset, Rev.3 table16.4/16.4.2.

No CAN bus synchronization, frames, acknowledgements or GSR transitions are
invented. MCR reserved-bit6 readback is explicitly not guaranteed by the manual.
"""
MCR_ADDRESSES=(0xFFFFD000,0xFFFFD800)
GSR_ADDRESSES=(0xFFFFD002,0xFFFFD802)
MBIMR_ADDRESSES=(0xFFFFD050,0xFFFFD052,0xFFFFD850,0xFFFFD852)
BCR_MASKS={0xFFFFD004:0xF733,0xFFFFD006:0x00FF,0xFFFFD804:0xF733,0xFFFFD806:0x00FF}

def mcr_scenario_metadata(bit):
    if bit is not None and (type(bit) is not int or bit not in (0,1)):
        raise ValueError('experimental_mcr_bit6 must be omitted,0 or1')
    return {'experimental_mcr_bit6':bit,'conditional_mcr_scenario':bit is not None,
            'mcr_scenario_note':('Experimental constant MCR reserved-bit6 readback fixture on both channels; not measured hardware.'
                                 if bit is not None else 'MCR reserved-bit6 readback unknown.')}

class HcanResetCommands:
    def __init__(self,*,power_on,trace,stop_type,experimental_mcr_bit6=None):
        mcr_scenario_metadata(experimental_mcr_bit6)
        self.experimental_mcr_bit6=experimental_mcr_bit6
        self.generations=[0,0];self.on_request=None
        self.commands=[1 if power_on else None for _ in MCR_ADDRESSES]
        self.release_requests=[False,False]
        self.software_reset_requests=[False,False]
        self.gsr=[KnownBits(0xC,0x3F) if power_on else KnownBits(0,0) for _ in MCR_ADDRESSES]
        self.mbimr={a:0xFFFF if power_on else None for a in MBIMR_ADDRESSES}
        self.bcr={a:KnownBits(0,mask) if power_on else KnownBits(0,0) for a,mask in BCR_MASKS.items()}
        self.mailbox_writes={}
        self.trace,self.stop_type=trace,stop_type

    def _channel(self,address,width,access):
        if width==2 and address in MCR_ADDRESSES:return MCR_ADDRESSES.index(address)
        raise self.stop_type('unsupported_access_size','HCAN MCR requires aligned word access',
                             address=address,width=width,access=access)

    def write(self,address,width,value):
        channel=self._channel(address,width,'write')
        value &= 0xFFFF
        if value not in (0,1):
            raise self.stop_type('unsupported_peripheral_mode','Only HCAN reset/release commands0/1 with reserved bits zero are modelled',
                                 address=address,width=width,access='write',value=value)
        prior_status=self.gsr[channel]
        self.gsr[channel]=KnownBits(0,0)  # processing/bus status is not supplied
        self.commands[channel]=value
        self.release_requests[channel]=value==0
        if value==1:
            self.software_reset_requests[channel]=True
            for a in MBIMR_ADDRESSES[2*channel:2*channel+2]:self.mbimr[a]=None
            for address in (MCR_ADDRESSES[channel]+4,MCR_ADDRESSES[channel]+6):self.bcr[address]=KnownBits(0,0)
        self.trace.append({'register':f'MCR_{channel}','access':'write','width':2,'value':value,
                           'scope':'CAN_software_reset_request_only' if value else 'CAN_reset_release_request_only',
                           'reset_processing':'unknown','bus_synchronization':'unknown'})
        self.generations[channel]+=1
        if self.on_request:self.on_request(channel,value,self.generations[channel],prior_status)

    def read(self,address,width):
        channel=self._channel(address,width,'read')
        if self.experimental_mcr_bit6 is not None:return self.read_known_word(address).concrete()
        raise self.stop_type('unknown_peripheral_reset_state',
            f'MCR_{channel} full-word readback includes unspecified reserved bit6; no value fabricated',
            address=address,width=width,access='read')

    def complete_reset_subset(self,channel):
        for a in MBIMR_ADDRESSES[2*channel:2*channel+2]:self.mbimr[a]=0xFFFF
        for address in (MCR_ADDRESSES[channel]+4,MCR_ADDRESSES[channel]+6):
            self.bcr[address]=KnownBits(0,BCR_MASKS[address])

    def mask_access(self,address,width,access,value=None):
        if width!=2 or address not in MBIMR_ADDRESSES:
            raise self.stop_type('unsupported_access_size','MBIMR requires aligned word access',
                                 address=address,width=width,access=access)
        if access=='write':self.mbimr[address]=value&0xFFFF
        result=self.mbimr[address]
        if result is None:
            raise self.stop_type('unknown_peripheral_reset_state','Mailbox mask prior/reset-processing state unknown',
                                 address=address,width=width,access=access)
        self.trace.append({'register':f'MBIMR_{address:08X}','access':access,'width':2,'value':result,
                           'scope':'mailbox_interrupt_mask_only_no_bus_events'})
        return result

    def _bcr_guard(self,address,width,access):
        if width!=2 or address not in BCR_MASKS:
            raise self.stop_type('unsupported_access_size','HCAN BCR requires aligned word access',
                                 address=address,width=width,access=access)

    def read_bcr_known(self,address):
        self._bcr_guard(address,2,'read');bits=self.bcr[address]
        self.trace.append({'register':f'BCR_{address:08X}','access':'read','width':2,
                           'known_value':bits.value,'known_mask':bits.mask,'unknown_mask':0xFFFF^bits.mask})
        return bits

    def read_bcr(self,address,width):
        self._bcr_guard(address,width,'read')
        raise self.stop_type('unknown_peripheral_reset_state','BCR reserved readback not guaranteed; typed CPU read required',
                             address=address,width=width,access='read')

    def write_bcr(self,address,width,value):
        self._bcr_guard(address,width,'write')
        channel=int(address>=0xFFFFD800);value &= 0xFFFF
        if value & ~BCR_MASKS[address]:
            raise self.stop_type('invalid_peripheral_write','BCR reserved write bits require zero',
                                 address=address,width=width,access='write',value=value)
        status=self.gsr[channel]
        if not status.mask&8:
            raise self.stop_type('unknown_peripheral_reset_state','BCR configuration requires known reset/configuration state',
                                 address=address,width=width,access='write',value=value)
        if not status.value&8:
            raise self.stop_type('unsupported_peripheral_mode','BCR writes outside configuration mode not modelled',
                                 address=address,width=width,access='write',value=value)
        if address&7==4 and (value>>12<3 or (value>>8)&7==0):
            raise self.stop_type('invalid_peripheral_write','BCR1 prohibited individual segment selection',
                                 address=address,width=width,access='write',value=value)
        self.bcr[address]=KnownBits(value,BCR_MASKS[address])
        self.trace.append({'register':f'BCR_{address:08X}','access':'write','width':2,'value':value,
                           'configuration':self.bit_configuration(channel),'scope':'configuration_latch_only_no_bus_simulation'})

    def bit_configuration(self,channel):
        first=self.bcr[MCR_ADDRESSES[channel]+4];second=self.bcr[MCR_ADDRESSES[channel]+6]
        if first.mask!=0xF733 or second.mask!=255:
            return {'known':False,'valid_constraints':None,'baud_hz':None}
        value=first.value;segment1=(value>>12)+1;segment2=((value>>8)&7)+1
        sjw=((value>>4)&3)+1;brp=second.value
        valid=(4<=segment1<=16 and 2<=segment2<=8 and segment1>segment2>=sjw
               and 8<=segment1+segment2+1<=25 and (brp!=0 or segment2>=3)
               and (not value&1 or brp<4))
        return {'known':True,'segment1_quanta':segment1,'segment2_quanta':segment2,
                'sjw_quanta':sjw,'peripheral_clock_divisor':brp+1,
                'valid_constraints':valid,'baud_hz':None}

    def _gsr_channel(self,address,width,access):
        if width==2 and address in GSR_ADDRESSES:return GSR_ADDRESSES.index(address)
        raise self.stop_type('unsupported_access_size','HCAN GSR requires aligned word access',
                             address=address,width=width,access=access)

    def read_gsr_known(self,address,width=2):
        channel=self._gsr_channel(address,width,'read')
        bits=self.gsr[channel]
        self.trace.append({'register':f'GSR_{channel}','access':'read','width':2,
                           'known_value':bits.value,'known_mask':bits.mask,
                           'unknown_mask':0xFFFF ^ bits.mask,
                           'scope':'status_only_no_reset_completion_or_bus_simulation'})
        return bits

    def read_gsr(self,address,width):
        self._gsr_channel(address,width,'read')
        raise self.stop_type('unknown_peripheral_reset_state',
                            'GSR reserved readback/status not fully known; use typed CPU read',
                            address=address,width=width,access='read')

    def write_gsr(self,address,width,value):
        self._gsr_channel(address,width,'write')
        raise self.stop_type('read_only_peripheral','GSR is read-only',
                             address=address,width=width,access='write',value=value)

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
        identifier=offset in (0,2) and (offset==2 or value&0x8000==0)
        inactive=offset==4 and value in (0x0700,0x2700)
        if value & 0xFFFF and not inactive and not identifier:
            raise self.stop_type('unsupported_peripheral_mode','Only zero mailbox initialization is modelled',
                                 address=address,width=width,access='write',value=value)
        self.mailbox_writes[address]=value & 0xFFFF
        self.trace.append({'register':f'MB{mailbox}_{channel}+{offset:02X}',
                           'access':'write','width':2,'value':value & 0xFFFF,
                           'scope':'mailbox_identifier_command_only' if identifier and value else 'mailbox_inactive_command' if inactive else 'mailbox_zero_initialization_only',
                           'configuration_note':('Inactive mailbox initialization requires non-MBC settings zero; NMC remains set in this observed command, so correct CAN operation is not guaranteed'
                                                 if inactive and value & 0x2000 else None)})

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
        if self.experimental_mcr_bit6 is not None:
            value=command|(self.experimental_mcr_bit6<<6)
            self.trace.append({'register':f'MCR_{channel}','access':'read','width':2,'value':value,
                               'scope':'experimental_reserved_bit_readback','experimental_mcr_bit6':self.experimental_mcr_bit6})
            return KnownBits.exact(value)
        self.trace.append({'register':f'MCR_{channel}','access':'read','width':2,
                           'known_value':command,'known_mask':0xFFBF,'unknown_mask':0x0040})
        return KnownBits(command,0xFFBF)
