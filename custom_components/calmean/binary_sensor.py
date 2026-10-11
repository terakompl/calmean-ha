from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .entity import CalmeanEntity, setup_entities

async def async_setup_entry(hass, entry, async_add_entities):
    setup_entities(entry, async_add_entities, lambda c, i: [CalmeanOnline(c, i, "active")])

class CalmeanOnline(CalmeanEntity, BinarySensorEntity):
    _attr_translation_key = "active"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    @property
    def is_on(self):
        return self.device.active if self.device else None
