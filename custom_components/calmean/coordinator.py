from datetime import timedelta
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging
from .api import CalmeanClient, CannotConnect, InvalidAuth
from .const import DOMAIN, DEFAULT_INTERVAL
from .models import InvalidResponse

class CalmeanCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, session):
        super().__init__(hass, logging.getLogger(__name__), name=DOMAIN, config_entry=entry,
                         update_interval=timedelta(seconds=entry.options.get("interval", DEFAULT_INTERVAL)))
        self.entry = entry
        self.client = CalmeanClient(session, entry.data["token"])

    async def _async_update_data(self):
        try:
            return await self.client.devices()
        except InvalidAuth as exc:
            raise ConfigEntryAuthFailed("CALMEAN token rejected") from exc
        except (CannotConnect, InvalidResponse) as exc:
            raise UpdateFailed("CALMEAN unavailable or unsupported response") from exc
