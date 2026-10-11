"""Authenticated map configuration. No secrets in the public static asset."""
from pathlib import Path
from copy import deepcopy
try:
    import probatio as vol
except ImportError:
    import voluptuous as vol
from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback
from .const import DOMAIN
from .models import matched_zone, validate_device_zones, zones_for_device

PANEL_PATH = 'calmean-map'

async def async_setup_panel_api(hass):
    state = hass.data.setdefault(DOMAIN, {'entries': {}})
    if state.get('panel_api_ready'):
        return
    await hass.http.async_register_static_paths([
        StaticPathConfig('/calmean_static', str(Path(__file__).parent / 'frontend'), False)
    ])
    websocket_api.async_register_command(hass, websocket_map)
    websocket_api.async_register_command(hass, websocket_save_zones)
    state['panel_api_ready'] = True

async def async_add_map_panel(hass):
    if hass.data[DOMAIN].get('panel_registered'):
        return
    await panel_custom.async_register_panel(
        hass, frontend_url_path=PANEL_PATH, webcomponent_name='calmean-map-panel',
        sidebar_title='Mapa CALMEAN', sidebar_icon='mdi:map-marker-radius',
        module_url='/calmean_static/calmean-map.js?v=0.2.1',
        require_admin=True,
    )
    hass.data[DOMAIN]['panel_registered'] = True

@websocket_api.websocket_command({'type': 'calmean/map'})
@websocket_api.require_admin
@callback
def websocket_map(hass, connection, msg):
    devices = []
    for entry_id, coordinator in hass.data.get(DOMAIN, {}).get('entries', {}).items():
        for device in (coordinator.data or {}).values():
            zones = zones_for_device(coordinator.entry.options, device.id)
            zone = matched_zone(device, zones)
            devices.append({
                'entry_id': entry_id, 'id': device.id, 'name': device.name,
                'latitude': device.latitude, 'longitude': device.longitude,
                'battery': device.battery, 'active': device.active,
                'updated_at': device.updated_at.isoformat() if device.updated_at else None,
                'localization_type': device.localization_type,
                'available': coordinator.last_update_success,
                'place': zone['name'] if zone else ('Poza domem' if device.has_position else None),
                'zones': deepcopy(zones),
                'revision': coordinator.entry.options.get('zone_revision', 0),
            })
    connection.send_result(msg['id'], {'devices': devices})

@websocket_api.websocket_command({
    'type': 'calmean/zones/save',
    vol.Required('entry_id'): str,
    vol.Required('device_id'): str,
    vol.Required('revision'): vol.All(vol.Coerce(int), vol.Range(min=0)),
    vol.Required('zones'): list,
})
@websocket_api.require_admin
@callback
def websocket_save_zones(hass, connection, msg):
    coordinator = hass.data.get(DOMAIN, {}).get('entries', {}).get(msg['entry_id'])
    if coordinator is None or msg['device_id'] not in (coordinator.data or {}):
        connection.send_error(msg['id'], 'not_found', 'Device unavailable')
        return
    entry = coordinator.entry
    revision = entry.options.get('zone_revision', 0)
    if msg['revision'] != revision:
        connection.send_error(msg['id'], 'conflict', 'Zone configuration changed. Reload before saving.')
        return
    try:
        zones = validate_device_zones(msg['zones'])
    except (ValueError, TypeError):
        connection.send_error(msg['id'], 'invalid_zones', 'Invalid zones: names must be unique; radius 50–5000 m.')
        return
    options = deepcopy(dict(entry.options))
    options.setdefault('device_zones', {})[msg['device_id']] = zones
    options['zone_revision'] = revision + 1
    hass.config_entries.async_update_entry(entry, options=options)
    # Publish the new place immediately without waiting for the next API request.
    coordinator.async_update_listeners()
    connection.send_result(msg['id'], {'revision': revision + 1})
