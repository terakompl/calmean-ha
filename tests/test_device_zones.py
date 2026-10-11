"""Per-device geofencing and migration regression tests."""
from test_models import m
import unittest

class DeviceZoneTests(unittest.TestCase):
    def zone(self, **changes):
        result=dict(id='home',name='Dom',kind='home',latitude=0,longitude=0,radius=50)
        result.update(changes)
        return result
    def device(self, longitude=0):
        return m.parse_devices([dict(deviceId='demo',latitude=0,longitude=longitude)])['demo']

    def test_minimum_radius_and_validation(self):
        self.assertEqual(m.validate_device_zones([self.zone()])[0]['radius'], 50)
        for value in (49, 5001, float('nan'), None):
            with self.assertRaises(ValueError):
                m.validate_device_zones([self.zone(radius=value)])

    def test_devices_use_independent_schools(self):
        options={'device_zones':{'demo-a':[self.zone(name='Szkoła A',kind='school')],
                                 'demo-b':[self.zone(name='Szkoła B',kind='school',longitude=.01)]}}
        a=m.zones_for_device(options,'demo-a');b=m.zones_for_device(options,'demo-b')
        self.assertEqual(m.presence(self.device(),a),'Szkoła A')
        self.assertEqual(m.presence(self.device(),b),'away')
        self.assertEqual(m.presence(self.device(.01),b),'Szkoła B')

    def test_fifty_metre_boundary(self):
        # At the equator, use a point corresponding to 49 m, then 51 m.
        inside=49/6_371_000*180/3.141592653589793
        outside=51/6_371_000*180/3.141592653589793
        self.assertEqual(m.presence(self.device(inside),[self.zone()]),'Dom')
        self.assertEqual(m.presence(self.device(outside),[self.zone()]),'away')

    def test_overlap_follows_order(self):
        zones=[self.zone(id='one',name='Dziadkowie',kind='custom'),self.zone(id='two')]
        self.assertEqual(m.matched_zone(self.device(),zones)['id'],'one')
        self.assertEqual(m.matched_zone(self.device(),list(reversed(zones)))['id'],'two')

    def test_remove_all_device_zones_does_not_restore_shared_defaults(self):
        options={'zones':{'home':self.zone()},'device_zones':{'demo':[]}}
        self.assertEqual(m.zones_for_device(options,'demo'),[])

    def test_migration_copies_zones_and_preserves_other_settings(self):
        options={'interval':120,'zones':{'home':dict(latitude=0,longitude=0,radius=100)}}
        migrated=m.migrate_shared_zones(options,['demo-a','demo-b'])
        self.assertEqual(migrated['interval'],120)
        self.assertNotIn('zones',migrated)
        self.assertEqual(migrated['device_zones']['demo-a'][0]['name'],'Dom')
        migrated['device_zones']['demo-a'][0]['name']='Zmienione'
        self.assertEqual(migrated['device_zones']['demo-b'][0]['name'],'Dom')
        self.assertIn('zones',options)

    def test_migration_does_not_replace_existing_device_config(self):
        options={'zones':{'home':self.zone()},'device_zones':{'demo-a':[]}}
        migrated=m.migrate_shared_zones(options,['demo-a','demo-b'])
        self.assertEqual(migrated['device_zones']['demo-a'],[])
        self.assertTrue(migrated['device_zones']['demo-b'])
        self.assertEqual(m.migrate_shared_zones(migrated,['new']),migrated)

    def test_duplicate_names_ids_and_reserved_states(self):
        invalid=[
            [self.zone(),self.zone(id='different',name='dom')],
            [self.zone(),self.zone(name='Inna')],
            [self.zone(name='Poza domem')],
            [self.zone(kind='unsupported')],
            [self.zone(name=' ')],
            [self.zone(id='')],
            [self.zone()]*31,
        ]
        for zones in invalid:
            with self.assertRaises(ValueError):m.validate_device_zones(zones)

    def test_unknown_position_remains_unknown(self):
        device=m.parse_devices([{'deviceId':'demo'}])['demo']
        self.assertIsNone(m.presence(device,[self.zone()]))
        self.assertIsNone(m.matched_zone(device,[self.zone()]))
