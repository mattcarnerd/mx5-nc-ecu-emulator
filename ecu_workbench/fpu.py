"""Bounded SH-2E FPU: software manual sections2.6,4.2,7.3."""
FPSCR_WRITABLE=0x00018C60
FPSCR_FIXED=0x00040001

class FpuState:
    def __init__(self):
        self.fr=[None]*16
        self.fpul=None
        self.fpscr=FPSCR_FIXED

    def load_fpscr(self,value):
        self.fpscr=(value & FPSCR_WRITABLE)|FPSCR_FIXED

    def known(self,value,name):
        if value is None:
            from .nc_boot import BootStop
            raise BootStop('unknown_register',f'{name} reset-undefined; initialize before use')
        return value

    def read_fr(self,n):
        return self.known(self.fr[n],f'FR{n}')

def execute_fpu(cpu,op,n,m):
    f=cpu.fpu
    key=op & 0xF0FF
    stores={0x005A:'fpul',0x006A:'fpscr',0x4052:'fpul',0x4062:'fpscr'}
    loads={0x405A:'fpul',0x406A:'fpscr',0x4056:'fpul',0x4066:'fpscr'}
    if key in stores:
        name=stores[key];value=f.known(getattr(f,name),name)
        if key & 0x4000:
            address=(cpu.reg(n)-4)&0xFFFFFFFF
            cpu.bus.write(address,4,value)
            cpu.r[n]=address
        else:cpu.r[n]=value
        return True
    if key in loads:
        name=loads[key];address=cpu.reg(n)
        memory=(key & 15)==6
        value=cpu.bus.read(address,4) if memory else address
        if name=='fpscr':f.load_fpscr(value)
        else:f.fpul=value
        if memory:cpu.r[n]=(address+4)&0xFFFFFFFF
        return True
    return False
