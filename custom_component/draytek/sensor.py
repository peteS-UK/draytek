"""Platform for sensor integration for squeezebox."""

from __future__ import annotations

import logging
from typing import cast

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import DraytekConfigEntry
from .entity import DraytekSensorEntity
from .const import DraytekSensorDescription, OID

_LOGGER = logging.getLogger(__name__)


SENSORS: tuple[DraytekSensorDescription, ...] = [
    DraytekSensorDescription(
        key="sysDescr",
        # state_class=SensorStateClass.TOTAL,
        display_name="System Description",
        baseoid=OID["sysDescr"],
    ),
    DraytekSensorDescription(
        key="sysUpTime",
        state_class=SensorStateClass.MEASUREMENT,
        display_name="System Up Time",
        baseoid=OID["sysUpTime"],
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DraytekConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Platform setup using common elements."""

    async_add_entities(
        DraytekSensor(
            coordinator=entry.runtime_data.coordinator,
            description=description,
            name=entry.runtime_data.name,
        )
        for description in SENSORS
    )


class DraytekSensor(DraytekSensorEntity, SensorEntity):
    """Draytek Status based sensor from LMS via cooridnatior."""

    @property
    def native_value(self) -> StateType:
        """Sensor from coordinator data."""
        return cast(StateType, self.coordinator.data[self.entity_description.key])
