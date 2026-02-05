import sys
import unittest

sys.path.insert(0, 'backend')

from simulator import ProtocolSimulator


def _robot_config():
    return {
        'labware': [
            {
                'slot': '10',
                'label': 'nest_1_reservoir_195ml',
                'loadName': 'nest_1_reservoir_195ml'
            },
            {
                'slot': '1',
                'label': 'corning_96_wellplate_360ul_flat',
                'loadName': 'corning_96_wellplate_360ul_flat'
            }
        ]
    }


class StepParsingTests(unittest.TestCase):
    def setUp(self):
        self.sim = ProtocolSimulator('dummy.py')
        self.robot_config = _robot_config()

    def _normalize(self, text, idx=1):
        log_entry = {'payload': {'text': text}}
        return self.sim._normalize_command(idx, log_entry, self.robot_config)

    def test_distribute_parses_source_and_dest(self):
        text = (
            'Distributing 100.0 from A1 of NEST 1 Well Reservoir 195 mL on slot 10 '
            'to A1 of Corning 96 Well Plate 360 uL Flat on slot 1'
        )
        step = self._normalize(text)
        self.assertEqual(step['type'], 'distribute')
        self.assertEqual(step['source']['labware'], 'nest_1_reservoir_195ml')
        self.assertEqual(step['source']['well'], 'A1')
        self.assertEqual(step['dest']['labware'], 'corning_96_wellplate_360ul_flat')
        self.assertEqual(step['dest']['well'], 'A1')

    def test_transfer_parses_source_and_dest(self):
        text = (
            'Transferring 50.0 from B2 of NEST 1 Well Reservoir 195 mL on slot 10 '
            'to C3 of Corning 96 Well Plate 360 uL Flat on slot 1'
        )
        step = self._normalize(text, idx=2)
        self.assertEqual(step['type'], 'transfer')
        self.assertEqual(step['source']['labware'], 'nest_1_reservoir_195ml')
        self.assertEqual(step['source']['well'], 'B2')
        self.assertEqual(step['dest']['labware'], 'corning_96_wellplate_360ul_flat')
        self.assertEqual(step['dest']['well'], 'C3')


if __name__ == '__main__':
    unittest.main()
