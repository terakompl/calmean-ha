"""Synthetic fixtures only; no account data or network calls."""
import importlib.util
from pathlib import Path
import sys
import unittest

spec = importlib.util.spec_from_file_location('calmean_models', Path(__file__).parents[1] / 'custom_components/calmean/models.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

class ModelTests(unittest.TestCase):
    def device(self, **changes):
        record = dict(deviceId='synthetic-watch', name='Demo', latitude=0, longitude=0,
                      battery=50, active=True, localizationType='GPS', createTime='2026-01-01T00:00:00Z')
        record.update(changes)
        return m.parse_devices({'data': {'devices': [record]}})['synthetic-watch']

    def test_nested_wrapper_and_multiple_devices(self):
        records = [{'deviceId': 'demo-a'}, {'deviceId': 'demo-b'}]
        self.assertEqual(set(m.parse_devices({'data': records})), {'demo-a', 'demo-b'})

    def test_zero_coordinates_are_valid(self):
        self.assertTrue(self.device().has_position)

    def test_invalid_coordinates_do_not_become_zero(self):
        for invalid in (None, '', 'invalid', float('nan'), 91, True):
            self.assertFalse(self.device(latitude=invalid).has_position)

    def test_no_position_means_unknown_presence(self):
        self.assertIsNone(m.presence(self.device(latitude=None), {}))

    def test_home_school_away_and_overlap_priority(self):
        zones = {'home': {'latitude': 0, 'longitude': 0, 'radius': 100},
                 'school': {'latitude': 0, 'longitude': 0.01, 'radius': 100}}
        self.assertEqual(m.presence(self.device(), zones), 'home')
        self.assertEqual(m.presence(self.device(longitude=0.01), zones), 'school')
        self.assertEqual(m.presence(self.device(longitude=0.1), zones), 'away')
        zones['school'] = zones['home']
        self.assertEqual(m.presence(self.device(), zones), 'home')

    def test_radius_boundary(self):
        point = self.device(longitude=0.001)
        radius = m.distance_m(0, 0, 0, 0.001)
        zones = {'home': {'latitude': 0, 'longitude': 0, 'radius': radius}}
        self.assertEqual(m.presence(point, zones), 'home')
        zones['home']['radius'] = radius - 0.001
        self.assertEqual(m.presence(point, zones), 'away')

    def test_timestamps(self):
        expected = m.timestamp('2026-01-01T00:00:00Z')
        self.assertEqual(m.timestamp(1767225600), expected)
        self.assertEqual(m.timestamp(1767225600000), expected)
        self.assertIsNone(m.timestamp('2026-01-01T00:00:00'))
        self.assertIsNone(m.timestamp('invalid'))

    def test_unknown_fields_stay_unknown(self):
        device = self.device(active='unknown', battery=101, localizationType=None)
        self.assertIsNone(device.active)
        self.assertIsNone(device.battery)
        self.assertIsNone(device.localization_type)

    def test_reject_unrecognized_and_invalid_ids(self):
        for payload in ({'error': 'denied'}, [], None, {'deviceId': None}):
            with self.assertRaises(m.InvalidResponse):
                m.parse_devices(payload)

    def test_validate_zones(self):
        self.assertEqual(m.validate_zone({'latitude': '0', 'longitude': '0', 'radius': '100'})['radius'], 100)
        for radius in (0, float('nan'), 5001):
            with self.assertRaises(ValueError):
                m.validate_zone({'latitude': 0, 'longitude': 0, 'radius': radius})

if __name__ == '__main__':
    unittest.main()
