"""Rev3 sections8.1-8.3: UBC configuration and guarded CPU data-write matches; no IRQ/output timing."""
BASE=0xFFFFEC00
class UserBreakConfig:
    def __init__(self, *, power_on,trace,stop_type):
        self.data=bytearray(12);self.valid=bytearray([int(power_on)]*12)
        self.trace,self.stop_type=trace,stop_type
    def reset_module(self):
        self.data[:]=bytes(12);self.valid[:]=bytes([1]*12)
    @staticmethod
    def handles(a):return BASE<=a<BASE+12
    def access(self,a,width,operation,value=None,*,syscr2):
        def stop(kind,detail):
            raise self.stop_type(kind,detail,address=a,width=width,access=operation,value=value)
        if width not in (1,2,4) or a%width or a+width>BASE+12:
            stop('unsupported_access_size','UBC requires aligned byte/word/long within register group')
        if syscr2 is None:stop('unknown_peripheral_reset_state','UBC module clock state unknown')
        if syscr2&1:stop('unsupported_peripheral_mode','UBC module-stopped accesses outside subset')
        off=a-BASE
        if operation=='read':
            if not all(self.valid[off:off+width]):stop('unknown_peripheral_reset_state','Retained UBC configuration unknown')
            result=int.from_bytes(self.data[off:off+width],'big')
            self.trace.append({'register':'UBC','address':f'0x{a:08X}','access':'read','width':width,'value':result,'scope':'inactive_break_configuration'})
            return result
        proposed=bytearray(self.data);known=bytearray(self.valid)
        proposed[off:off+width]=value.to_bytes(width,'big');known[off:off+width]=bytes([1]*width)
        for i,mask in ((8,0),(10,0),(11,7)):
            if known[i] and proposed[i]&~mask:stop('invalid_peripheral_write','UBC reserved bits require zero')
        # At least one CP/ID/RW group00 is sufficient proof that no match occurs.
        if not known[9]:stop('unsupported_peripheral_mode','Unknown UBC break matching outside subset')
        active=all(proposed[9]&mask for mask in (0xC0,0x30,0x0C))
        if active and (not proposed[9]&0x40 or proposed[9]&0x30!=0x20 or proposed[9]&0x0C!=8 or not all(known[:8])):
            stop('unsupported_peripheral_mode','Only fully known CPU data-write UBC matching is guarded')
        self.data,self.valid=proposed,known
        self.trace.append({'register':'UBC','address':f'0x{a:08X}','access':'write','width':width,'value':value,'scope':'inactive_break_configuration'})

    def guard_cpu_write(self,a,width,*,syscr2):
        if syscr2 is None or syscr2&1 or not self.valid[9]:return
        control=self.data[9]
        if not all(control&mask for mask in (0xC0,0x30,0x0C)):return
        size=control&3
        if size and width!={1:1,2:2,3:4}[size]:return
        target=int.from_bytes(self.data[:4],'big');mask=int.from_bytes(self.data[4:8],'big')
        if (a^target)&(~mask&0xFFFFFFFF):return
        raise self.stop_type('unsupported_peripheral_mode',
            'UBC CPU data-write condition matches; user-break IRQ/UBCTRG timing unmodelled, store not applied',
            address=a,width=width,access='write')
