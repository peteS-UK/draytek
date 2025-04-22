"""Base class for Squeezebox Sensor entities."""

import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DraytekSensorDescription, DOMAIN
from .coordinator import DraytekDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class DraytekSensorEntity(CoordinatorEntity[DraytekDataUpdateCoordinator]):
    """Defines a base status sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DraytekDataUpdateCoordinator,
        description: DraytekSensorDescription,
        name: str,
    ) -> None:
        """Initialize status sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_translation_key = description.key.replace(" ", "_")

        self._attr_unique_id = f"{description.key}"
        self._attr_name = f"{name} {description.display_name}"

        _LOGGER.critical("uuid %s", coordinator.uuid)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.uuid)},
            name=name,
            manufacturer="Draytek",
        )
