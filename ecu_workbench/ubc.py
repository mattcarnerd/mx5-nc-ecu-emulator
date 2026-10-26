"""Rev3 sections8.1-8.3: inactive UBC configuration, no comparator/output model."""
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
        if not known[9] or all(proposed[9]&mask for mask in (0xC0,0x30,0x0C)):
            stop('unsupported_peripheral_mode','Active or unknown UBC break matching outside subset')
        self.data,self.valid=proposed,known
        self.trace.append({'register':'UBC','address':f'0x{a:08X}','access':'write','width':width,'value':value,'scope':'inactive_break_configuration'})
