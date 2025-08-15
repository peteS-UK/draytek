"""Constants for the Draytek Router integration."""

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntityDescription

DOMAIN = "draytek"
CONF_COMMUNITY = "community"


@dataclass
class DraytekSensorDescription(SensorEntityDescription):
    display_name: str | None = None
    baseoid: str | None = None


OID = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "system": "1.3.6.1.2.1.1.1.1",
}
