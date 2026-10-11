"""Map/save handlers with mocked HA interfaces; no real HA runtime."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from functools import wraps
from copy import deepcopy
import voluptuous as vol

class PanelBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = {name:sys.modules.get(name) for name in (
            'homeassistant','homeassistant.components','homeassistant.components.http','homeassistant.core')}
        ha=types.ModuleType('homeassistant');components=types.ModuleType('homeassistant.components')
        http=types.ModuleType('homeassistant.components.http');core=types.ModuleType('homeassistant.core')
        core.callback=lambda fn:fn
        http.StaticPathConfig=lambda *args:args
        def command(schema):
            return lambda fn:fn
        def require_admin(fn):
            @wraps(fn)
            def guarded(hass,connection,msg):
                if not connection.user.is_admin:raise PermissionError('admin required')
                return fn(hass,connection,msg)
            return guarded
        components.frontend=types.SimpleNamespace()
        components.panel_custom=types.SimpleNamespace()
        components.websocket_api=types.SimpleNamespace(websocket_command=command,require_admin=require_admin)
        for name,module in [('homeassistant',ha),('homeassistant.components',components),('homeassistant.components.http',http),('homeassistant.core',core)]:sys.modules[name]=module
        base=Path(__file__).parents[1]/'custom_components/calmean'
        pkg=types.ModuleType('calmean_test_panel');pkg.__path__=[str(base)];sys.modules[pkg.__name__]=pkg
        spec=importlib.util.spec_from_file_location(pkg.__name__+'.panel',base/'panel.py')
        cls.panel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=cls.panel;spec.loader.exec_module(cls.panel)
        # Drop fake global HA modules immediately; imported objects remain in the handler module.
        for name,previous in cls.previous.items():
            if previous is None:sys.modules.pop(name,None)
            else:sys.modules[name]=previous

    def setUp(self):
        from test_models import m
        self.entry=types.SimpleNamespace(options={'interval':60,'device_zones':{'a':[], 'b':[self.zone('b')]},'zone_revision':0},data={'token':'synthetic-secret'})
        self.coordinator=types.SimpleNamespace(entry=self.entry,data=m.parse_devices([{'deviceId':'a','latitude':0,'longitude':0},{'deviceId':'b','latitude':1,'longitude':1}]),last_update_success=False)
        self.notified=0
        def notify():self.notified+=1
        self.coordinator.async_update_listeners=notify
        def update(entry,options):entry.options=options
        self.hass=types.SimpleNamespace(data={'calmean':{'entries':{'account':self.coordinator}}},config_entries=types.SimpleNamespace(async_update_entry=update))
        self.results=[];self.errors=[]
        self.connection=types.SimpleNamespace(user=types.SimpleNamespace(is_admin=True),send_result=lambda i,data:self.results.append(data),send_error=lambda i,code,message:self.errors.append(code))

    def zone(self,name='Dom',radius=50):
        return dict(id=name,name=name,kind='custom',latitude=0,longitude=0,radius=radius)

    def message(self,**changes):
        msg=dict(id=1,type='calmean/zones/save',entry_id='account',device_id='a',revision=0,zones=[self.zone()]);msg.update(changes);return msg

    def test_save_targets_one_device_and_preserves_settings(self):
        original_b=deepcopy(self.entry.options['device_zones']['b'])
        self.panel.websocket_save_zones(self.hass,self.connection,self.message())
        self.assertEqual(self.entry.options['device_zones']['b'],original_b)
        self.assertEqual(self.entry.options['interval'],60)
        self.assertEqual(self.entry.options['zone_revision'],1)
        self.assertEqual(self.notified,1)
        self.assertFalse(self.coordinator.last_update_success)

    def test_conflicting_revision_does_not_overwrite(self):
        self.panel.websocket_save_zones(self.hass,self.connection,self.message(revision=1))
        self.assertEqual(self.errors,['conflict'])
        self.assertEqual(self.entry.options['device_zones']['a'],[])

    def test_invalid_radius_is_rejected(self):
        self.panel.websocket_save_zones(self.hass,self.connection,self.message(zones=[self.zone(radius=49)]))
        self.assertEqual(self.errors,['invalid_zones'])
        self.assertEqual(self.notified,0)

    def test_unknown_device_is_rejected(self):
        self.panel.websocket_save_zones(self.hass,self.connection,self.message(device_id='missing'))
        self.assertEqual(self.errors,['not_found'])

    def test_empty_list_removes_only_target_zones(self):
        self.panel.websocket_save_zones(self.hass,self.connection,self.message(zones=[]))
        self.assertEqual(self.entry.options['device_zones']['a'],[])
        self.assertTrue(self.entry.options['device_zones']['b'])

    def test_snapshot_omits_token_and_reports_api_failure(self):
        self.panel.websocket_map(self.hass,self.connection,{'id':1,'type':'calmean/map'})
        self.assertNotIn('synthetic-secret',str(self.results))
        self.assertFalse(self.results[0]['devices'][0]['available'])
        self.assertEqual(len(self.results[0]['devices']),2)

    def test_snapshot_zones_are_not_mutable_config_references(self):
        self.panel.websocket_map(self.hass,self.connection,{'id':1,'type':'calmean/map'})
        self.results[0]['devices'][1]['zones'].clear()
        self.assertTrue(self.entry.options['device_zones']['b'])
