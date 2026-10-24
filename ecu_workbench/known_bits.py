"""Conservative independent-bit 32-bit values; never select unknown bits."""
from dataclasses import dataclass
MASK=0xFFFFFFFF

@dataclass(frozen=True)
class KnownBits:
    value: int
    mask: int

    def __post_init__(self):
        object.__setattr__(self,'mask',self.mask & MASK)
        object.__setattr__(self,'value',self.value & self.mask & MASK)

    @classmethod
    def exact(cls,value):
        return cls(value,MASK)

    def concrete(self):
        if self.mask!=MASK:raise ValueError('Value contains unknown bits')
        return self.value

    def compact(self):
        return self.value if self.mask==MASK else self

    def sign_extend_word(self):
        value=self.value & 0xFFFF
        mask=self.mask & 0xFFFF
        if mask & 0x8000:
            mask|=0xFFFF0000
            if value & 0x8000:value|=0xFFFF0000
        return KnownBits(value,mask)

    def bit_and(self,other):
        known_zero=(self.mask & ~self.value)|(other.mask & ~other.value)
        known_one=self.value & other.value
        return KnownBits(known_one,known_zero|known_one)

    def bit_or(self,other):
        known_one=self.value|other.value
        known_zero=self.mask & other.mask & ~self.value & ~other.value
        return KnownBits(known_one,known_zero|known_one)

    def bit_xor(self,other):
        mask=self.mask & other.mask
        return KnownBits(self.value ^ other.value,mask)

    def is_zero(self):
        if self.value:return False
        return True if self.mask==MASK else None
