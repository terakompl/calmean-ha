from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from .entity import CalmeanEntity, setup_entities
from .models import matched_zone, zones_for_device

async def async_setup_entry(hass, entry, async_add_entities):
    setup_entities(entry, async_add_entities, lambda c, i: [CalmeanTracker(c, i, "tracker")])

class CalmeanTracker(CalmeanEntity, TrackerEntity):
    _attr_name = None
    _attr_icon = "mdi:watch"
    @property
    def source_type(self):
        return SourceType.GPS
    @property
    def available(self):
        return super().available and self.device.has_position
    @property
    def latitude(self):
        return self.device.latitude if self.device else None
    @property
    def longitude(self):
        return self.device.longitude if self.device else None
    @property
    def location_name(self):
        if not self.device:
            return None
        zones = zones_for_device(self.coordinator.entry.options, self.device_id)
        if not zones:
            return None
        zone = matched_zone(self.device, zones)
        if zone:
            return "home" if zone["kind"] == "home" else zone["name"]
        return "not_home"
    @property
    def extra_state_attributes(self):
        return {"position_updated_at": self.device.updated_at.isoformat() if self.device and self.device.updated_at else None}
