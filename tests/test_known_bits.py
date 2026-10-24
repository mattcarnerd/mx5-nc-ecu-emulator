import itertools,unittest
from ecu_workbench.known_bits import KnownBits,MASK

class KnownBitTests(unittest.TestCase):
    def test_normalization_immutability_and_concrete_guard(self):
        a=KnownBits(0xFFFFFFFF,0xFFBF)
        self.assertEqual(a.value,0xFFBF)
        with self.assertRaises(ValueError):a.concrete()
        with self.assertRaises(Exception):a.value=0
        self.assertEqual(KnownBits.exact(-1).concrete(),MASK)
        self.assertEqual(KnownBits(0,MASK).compact(),0)

    def test_exhaustive_two_bit_truth_tables(self):
        states=[KnownBits(v,m|0xFFFFFFFC) for m in range(4) for v in range(4) if v & ~m==0]
        for a,b in itertools.product(states,repeat=2):
            av=[v for v in range(4) if v&a.mask==a.value]
            bv=[v for v in range(4) if v&b.mask==b.value]
            for method,operation in (('bit_and',lambda x,y:x&y),('bit_or',lambda x,y:x|y),('bit_xor',lambda x,y:x^y)):
                result=getattr(a,method)(b)
                possibilities=[operation(x,y) for x,y in itertools.product(av,bv)]
                for value in possibilities:self.assertEqual(value & result.mask,result.value)
                for bit in range(32):
                    values={bool(v & (1<<bit)) for v in possibilities}
                    self.assertEqual(bool(result.mask & (1<<bit)),len(values)==1)

    def test_unknown_sign_extension_and_zero_proof(self):
        a=KnownBits(0,0x7FFF).sign_extend_word()
        self.assertEqual(a.mask,0x7FFF);self.assertIsNone(a.is_zero())
        self.assertEqual(KnownBits(0x8000,0xFFBF).sign_extend_word().mask,0xFFFFFFBF)
        self.assertEqual(KnownBits(0x8000,0xFFBF).sign_extend_word().value,0xFFFF8000)
        self.assertTrue(KnownBits.exact(0).is_zero())
        self.assertFalse(KnownBits(1,1).is_zero())
        self.assertTrue(KnownBits(0,0).bit_and(KnownBits.exact(0)).is_zero())
        self.assertEqual(KnownBits(0,0).bit_or(KnownBits.exact(MASK)).concrete(),MASK)
