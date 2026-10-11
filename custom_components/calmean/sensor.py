from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE
from .entity import CalmeanEntity, setup_entities
from .models import matched_zone, zones_for_device

KINDS = ("battery", "localization_type", "updated_at", "presence")
async def async_setup_entry(hass, entry, async_add_entities):
    setup_entities(entry, async_add_entities, lambda c, i: [CalmeanSensor(c, i, k) for k in KINDS])

class CalmeanSensor(CalmeanEntity, SensorEntity):
    def __init__(self, coordinator, device_id, kind):
        super().__init__(coordinator, device_id, kind)
        self.kind = kind
        self._attr_translation_key = kind
        if kind == "battery":
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif kind == "updated_at":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
    @property
    def native_value(self):
        if not self.device:
            return None
        if self.kind == "presence":
            if not self.device.has_position:
                return None
            zone = matched_zone(self.device, zones_for_device(self.coordinator.entry.options, self.device_id))
            return zone["name"] if zone else "Poza domem"
        return getattr(self.device, self.kind)
