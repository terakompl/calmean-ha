"""CALMEAN custom integration."""
from datetime import timedelta
from homeassistant.components import frontend
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, DEFAULT_INTERVAL, PLATFORMS
from .coordinator import CalmeanCoordinator
from .models import migrate_shared_zones
from .panel import PANEL_PATH, async_setup_panel_api, async_add_map_panel

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup(hass, config):
    await async_setup_panel_api(hass)
    return True

async def async_setup_entry(hass, entry):
    await async_setup_panel_api(hass)
    coordinator = CalmeanCoordinator(hass, entry, async_get_clientsession(hass))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    # Copy existing shared zones once to each current watch; retain entity IDs/token.
    if 'zones' in entry.options:
        options = migrate_shared_zones(entry.options, coordinator.data)
        hass.config_entries.async_update_entry(entry, options=options)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.data[DOMAIN]['entries'][entry.entry_id] = coordinator
    await async_add_map_panel(hass)
    entry.async_on_unload(entry.add_update_listener(async_options_updated))
    return True

async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        state = hass.data.get(DOMAIN, {})
        state.get('entries', {}).pop(entry.entry_id, None)
        if not state.get('entries') and state.get('panel_registered'):
            frontend.async_remove_panel(hass, PANEL_PATH)
            state['panel_registered'] = False
    return unloaded

async def async_options_updated(hass, entry):
    coordinator = entry.runtime_data
    coordinator.update_interval = timedelta(seconds=entry.options.get('interval', DEFAULT_INTERVAL))
    # Keep unavailable entities unavailable while recalculating zone states.
    coordinator.async_update_listeners()
