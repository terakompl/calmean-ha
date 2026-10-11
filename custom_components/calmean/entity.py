from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

class CalmeanEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, device_id, suffix):
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{device_id}_{suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_{device_id}")},
            name=coordinator.data[device_id].name, manufacturer="CALMEAN")

    @property
    def device(self):
        return self.coordinator.data.get(self.device_id)

    @property
    def available(self):
        return super().available and self.device is not None

def setup_entities(entry, async_add_entities, factory):
    """Discover devices on every refresh; missing devices become unavailable."""
    coordinator = entry.runtime_data
    known = set()
    def discover():
        new = set(coordinator.data or {}) - known
        if new:
            async_add_entities([entity for identifier in sorted(new) for entity in factory(coordinator, identifier)])
            known.update(new)
    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))
