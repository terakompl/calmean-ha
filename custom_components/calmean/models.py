"""Pure normalization and geofencing; no Home Assistant dependencies."""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from math import asin, cos, isfinite, radians, sin, sqrt

class InvalidResponse(ValueError):
    """API schema cannot be recognized."""

def number(value, minimum, maximum):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) and minimum <= result <= maximum else None

def timestamp(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            epoch = float(value)
            if epoch > 100_000_000_000:
                epoch /= 1000
            return datetime.fromtimestamp(epoch, timezone.utc)
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        # Never guess a timezone for undocumented local times.
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (ValueError, TypeError, OverflowError, OSError):
        return None

def boolean(value):
    if value in (True, 1, "true", "1"):
        return True
    if value in (False, 0, "false", "0"):
        return False
    return None

@dataclass(frozen=True)
class Device:
    id: str
    name: str
    latitude: float | None
    longitude: float | None
    battery: float | None
    active: bool | None
    localization_type: str | None
    updated_at: datetime | None

    @property
    def has_position(self):
        return self.latitude is not None and self.longitude is not None

def parse_devices(payload):
    """Accept a list or nested wrappers containing flat device records.

    Unknown nonempty structures fail explicitly, rather than presenting no devices.
    Nested location records require a verified schema before adding adapters.
    """
    result = {}
    def visit(node):
        if isinstance(node, list):
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            if "deviceId" in node:
                identifier = node["deviceId"]
                if identifier is None or isinstance(identifier, (dict, list, bool)) or not str(identifier).strip():
                    raise InvalidResponse("Invalid device identifier")
                identifier = str(identifier)
                result[identifier] = Device(
                    identifier, str(node.get("name") or f"CALMEAN {identifier}"),
                    number(node.get("latitude"), -90, 90),
                    number(node.get("longitude"), -180, 180),
                    number(node.get("battery"), 0, 100),
                    boolean(node.get("active")),
                    str(node["localizationType"]) if node.get("localizationType") is not None else None,
                    timestamp(node.get("createTime")),
                )
            else:
                for value in node.values():
                    if isinstance(value, (dict, list)):
                        visit(value)
    visit(payload)
    if not result:
        raise InvalidResponse("No recognizable device records")
    return result

def distance_m(lat1, lon1, lat2, lon2):
    a, b = radians(lat1), radians(lat2)
    dlat, dlon = b-a, radians(lon2-lon1)
    h = sin(dlat/2)**2 + cos(a)*cos(b)*sin(dlon/2)**2
    return 6_371_000 * 2 * asin(sqrt(min(1.0, max(0.0, h))))

def validate_zone(zone):
    if not isinstance(zone, dict):
        raise ValueError("Invalid zone")
    result = {key: number(zone.get(key), low, high) for key, low, high in (
        ("latitude", -90, 90), ("longitude", -180, 180), ("radius", 10, 5000))}
    if any(value is None for value in result.values()):
        raise ValueError("Invalid zone")
    return result

def zones_for_device(options, device_id):
    """Explicit device configuration overrides the legacy shared defaults."""
    mapping = options.get("device_zones", {})
    if device_id in mapping:
        return mapping[device_id]
    return [dict(zone, id=key, name={"home": "Dom", "school": "Szkoła"}.get(key, key), kind=key)
            for key, zone in options.get("zones", {}).items()]

def migrate_shared_zones(options, device_ids):
    """Copy legacy fences once, without mutating the stored configuration."""
    migrated = deepcopy(dict(options))
    if "zones" not in options:
        return migrated
    mapping = migrated.setdefault("device_zones", {})
    for device_id in device_ids:
        if device_id not in mapping:
            mapping[device_id] = zones_for_device(options, device_id)
    migrated.pop("zones", None)
    migrated.setdefault("zone_revision", 0)
    return migrated

def validate_device_zones(zones):
    """Normalize a device's ordered geofences; first matching zone wins."""
    if not isinstance(zones, list) or len(zones) > 30:
        raise ValueError("Expected up to 30 zones")
    result, identifiers, names = [], set(), set()
    for item in zones:
        coordinates = validate_zone(item)
        # Retain legacy radii below 50 during migration; new UI uses >=50.
        if coordinates["radius"] < 50:
            raise ValueError("Minimum radius is 50 m")
        identifier = item.get("id")
        name = item.get("name")
        kind = item.get("kind", "custom")
        if not isinstance(identifier, str) or not identifier or len(identifier) > 80:
            raise ValueError("Invalid zone ID")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            raise ValueError("Invalid zone name")
        name = name.strip()
        if identifier in identifiers or name.casefold() in names or kind not in ("home", "school", "custom"):
            raise ValueError("Duplicate or invalid zone")
        if name.casefold() in ("poza domem", "away", "unknown", "unavailable", "nieznane"):
            raise ValueError("Reserved zone name")
        identifiers.add(identifier)
        names.add(name.casefold())
        result.append(dict(coordinates, id=identifier, name=name, kind=kind))
    return result

def matched_zone(device, zones):
    if not device.has_position:
        return None
    for zone in zones:
        if distance_m(device.latitude, device.longitude, zone["latitude"], zone["longitude"]) <= zone["radius"]:
            return zone
    return None

def presence(device, zones):
    # Compatibility for legacy callers and fixtures.
    if not device.has_position:
        return None
    if isinstance(zones, dict):
        zones = [dict(zone, id=key, name=key, kind=key) for key, zone in zones.items()]
    zone = matched_zone(device, zones)
    return zone["name"] if zone else "away"
