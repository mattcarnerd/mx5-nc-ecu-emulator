import unittest
from test_sh2_branch import program
from ecu_workbench.nc_boot import PCDR_ADDRESS,PCIOR_ADDRESS,BootBus,BootStop

class OutputTests(unittest.TestCase):
    def test_firmware_latch_transitions_timestamp_without_pin_claim(self):
        d=program(0x2101,0xE002,0x2101,0x2101)
        d.r[1]=PCDR_ADDRESS;d.r[0]=1;d.bus.write(PCIOR_ADDRESS,2,3)
        result=d.run(4);events=result['raw_gpio_commands']
        self.assertEqual([e['tick'] for e in events],[0,2,3])
        self.assertEqual(events[1]['changed_known_mask'],3)
        self.assertEqual(events[2]['changed_known_mask'],0)
        self.assertTrue(all(e['physical_pin_level'] is None for e in events))
        self.assertTrue(all(e['ECU_function']=='unknown_board_mapping' for e in events))
        self.assertEqual(events[1]['output_direction_mask'],3)

    def test_byte_lanes_faults_unknown_prior_and_bounded_events(self):
        b=BootBus(program(0x0009).bus.image,power_on=False)
        b.write(PCDR_ADDRESS+1,1,1);e=b.raw_gpio_commands[-1]
        self.assertEqual(e['newly_known_mask'],31);self.assertIsNone(e['tick'])
        self.assertIsNone(e['output_direction_mask'])
        with self.assertRaises(BootStop):b.write(PCDR_ADDRESS,2,0xFFFF)
        self.assertEqual(len(b.raw_gpio_commands),1)
        for _ in range(110):b.write(PCDR_ADDRESS,1,0)
        self.assertEqual(len(b.raw_gpio_commands),100)
