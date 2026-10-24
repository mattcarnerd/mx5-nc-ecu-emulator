import unittest
from test_sh2_branch import program
from ecu_workbench.known_bits import KnownBits

class PartialExtensionTests(unittest.TestCase):
    def test_extensions_match_all_concrete_completions(self):
        for width,code in ((1,12),(2,13)):
            low=(1<<(width*8))-1
            for signed in (False,True):
                for alias in (False,True):
                    for bit in (0,3,width*8-1):
                        mask=0xFFFFFFFF^(1<<bit);base=0xA581A581
                        source=KnownBits(base,mask)
                        dest=0 if alias else 1
                        op=0x6000|(dest<<8)|(code+2 if signed else code)
                        d=program(op);d.r[0]=source;d.t=True;d.execute()
                        actual=d.transport_bits(dest)
                        possible=[]
                        for extra in (0,1<<bit):
                            v=(source.value|extra)&low
                            if signed and v&(1<<(width*8-1)):v|=0xFFFFFFFF^low
                            possible.append(v)
                        expected_mask=0xFFFFFFFF^(possible[0]^possible[1])
                        self.assertEqual(actual,KnownBits(possible[0],expected_mask))
                        self.assertTrue(d.t)

    def test_fully_unknown_can_be_zero_extended_without_becoming_known(self):
        d=program(0x610D);d.execute()
        self.assertEqual(d.r[1],KnownBits(0,0xFFFF0000))
