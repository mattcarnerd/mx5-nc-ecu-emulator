from fractions import Fraction
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
    if (op & 0xF000)!=0xF000:return False
    form=op & 15
    if form in (0,1,2,3):
        check_mode(f)
        left_bits,right_bits=f.read_fr(n),f.read_fr(m)
        try:
            left,right=decode_finite(left_bits),decode_finite(right_bits)
            if form==0:result=left+right
            elif form==1:result=left-right
            elif form==2:result=left*right
            else:
                if right==0:raise ValueError('Division by zero outside bounded FPU exception subset')
                result=left/right
            negative_zero=(bool((left_bits^right_bits)&0x80000000) if form in (2,3) else
                left==0 and right==0 and bool(left_bits&0x80000000) and
                (not bool(right_bits&0x80000000) if form==1 else bool(right_bits&0x80000000)))
            bits=encode_truncate(result,negative_zero)
        except (ValueError,OverflowError) as error:unsupported(str(error))
        f.fr[n]=bits;f.fpscr &= ~0x18000
        return True
    if form==12:
        f.fr[n]=f.read_fr(m);return True
    if form in (6,8,9):
        address=cpu.reg(m)
        if form==6:address=(address+cpu.reg(0))&0xFFFFFFFF
        value=cpu.bus.read(address,4)
        f.fr[n]=value
        if form==9:cpu.r[m]=(address+4)&0xFFFFFFFF
        return True
    if form in (7,10,11):
        value=f.read_fr(m);base=cpu.reg(n)
        address=((base+cpu.reg(0)) if form==7 else base-4 if form==11 else base)&0xFFFFFFFF
        cpu.bus.write(address,4,value)
        if form==11:cpu.r[n]=address
        return True
    if key in (0xF08D,0xF09D):
        f.fr[n]=0 if key==0xF08D else 0x3F800000;return True
    if key==0xF01D:f.fpul=f.read_fr(n);return True
    if key==0xF00D:f.fr[n]=f.known(f.fpul,'FPUL');return True
    if key in (0xF02D,0xF03D):
        check_mode(f)
        try:
            if key==0xF02D:
                value=f.known(f.fpul,'FPUL');signed=value-(1<<32) if value&0x80000000 else value
                result=encode_truncate(Fraction(signed))
            else:
                value=decode_finite(f.read_fr(n));result=int(value)
                if not -(1<<31)<=result<(1<<31):raise ValueError('FTRC out of signed32 range')
                result &= 0xFFFFFFFF
        except (ValueError,OverflowError) as error:unsupported(str(error))
        if key==0xF02D:f.fr[n]=result
        else:f.fpul=result
        f.fpscr &= ~0x18000
        return True
    return False


def unsupported(detail):
    from .nc_boot import BootStop
    raise BootStop('unsupported_fpu_mode',detail)


def check_mode(f):
    if (f.fpscr & 0x40003)!=0x40001 or f.fpscr & 0xC00:
        unsupported('Only SH-2E fixed DN=1/RM=01 with disabled V/Z exceptions supported')


def decode_finite(bits):
    sign=-1 if bits&0x80000000 else 1
    exponent=(bits>>23)&255
    if exponent==255:raise ValueError('NaN/infinity exception cases outside bounded FPU subset')
    if exponent==0:return Fraction(0)  # fixed DN flushes signed denormals to zero
    significand=(bits&0x7FFFFF)|(1<<23)
    shift=exponent-150
    return sign*Fraction(significand*(1<<shift) if shift>=0 else significand,1 if shift>=0 else 1<<-shift)


def encode_truncate(value,negative_zero=False):
    sign=value<0 or (value==0 and negative_zero)
    value=abs(value)
    if not value:return int(sign)<<31
    exponent=value.numerator.bit_length()-value.denominator.bit_length()
    power=Fraction(1<<exponent) if exponent>=0 else Fraction(1,1<<-exponent)
    if value<power:exponent-=1
    if exponent>127:raise OverflowError('Overflow outside bounded FPU arithmetic subset')
    if exponent<-126:return int(sign)<<31
    shift=23-exponent
    scaled=value*(1<<shift) if shift>=0 else value/Fraction(1<<-shift)
    mantissa=int(scaled)-(1<<23)
    return (int(sign)<<31)|((exponent+127)<<23)|mantissa
