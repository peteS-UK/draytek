"""DataUpdateCoordinator for the Squeezebox integration."""

from __future__ import annotations

import logging
from asyncio import timeout

# from . import DraytekConfigEntry
from dataclasses import dataclass
from datetime import timedelta
from struct import unpack

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyasn1.codec.ber import decoder
from pysnmp.error import PySnmpError
from pysnmp.hlapi.asyncio import (
    CommunityData,
    Udp6TransportTarget,
    UdpTransportTarget,
    UsmUserData,
    getCmd,
)
from pysnmp.proto.rfc1902 import Opaque
from pysnmp.proto.rfc1905 import NoSuchObject


from .const import CONF_COMMUNITY, OID
from .util import async_create_request_cmd_args

DEFAULT_TIMEOUT = 10


@dataclass
class DraytekData:
    """SqueezeboxData data class."""

    coordinator: DraytekDataUpdateCoordinator


type DraytekConfigEntry = ConfigEntry[DraytekData]


_LOGGER = logging.getLogger(__name__)


class DraytekDataUpdateCoordinator(DataUpdateCoordinator):
    """Draytek custom coordinator."""

    config_entry: DraytekConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: DraytekConfigEntry) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Draytek",
            config_entry=config_entry,
            update_interval=timedelta(seconds=30),
            always_update=False,
        )
        self.hass = hass
        self.config_entry = config_entry

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        try:
            # Try IPv4 first.
            self.target = UdpTransportTarget(
                (self.config_entry.data[CONF_HOST], self.config_entry.data[CONF_PORT]),
                timeout=DEFAULT_TIMEOUT,
            )
        except PySnmpError:
            # Then try IPv6.
            try:
                self.target = Udp6TransportTarget(
                    (
                        self.config_entry.data[CONF_HOST],
                        self.config_entry.data[CONF_PORT],
                    ),
                    timeout=DEFAULT_TIMEOUT,
                )
            except PySnmpError as err:
                _LOGGER.error("Invalid SNMP host: %s", err)
                return

        self.auth_data = CommunityData(self.config_entry.data[CONF_COMMUNITY])

        self._uuid = await self.async_get_snmp_value("1.3.6.1.2.1.1.2.0")

    @property
    def uuid(self):
        return self._uuid

    async def _async_update_data(self):
        """Fetch data from API endpoint."""

        data: dict = {}

        for key, oid in OID.items():
            result = await self.async_get_snmp_value(oid)
            data[key] = result

        _LOGGER.critical("result %s", data)

        if not data:
            raise UpdateFailed("No data from status poll")

        _LOGGER.debug("Raw SNMP Data %s", data)

        return data

    async def async_get_snmp_value(self, baseoid: str):
        request_args = await async_create_request_cmd_args(
            self.hass, self.auth_data, self.target, baseoid
        )
        get_result = await getCmd(*request_args)

        errindication, errstatus, errindex, restable = get_result

        if errindication and not self._accept_errors:
            _LOGGER.error("SNMP error: %s", errindication)
        elif errstatus and not self._accept_errors:
            _LOGGER.error(
                "SNMP error: %s at %s",
                errstatus.prettyPrint(),
                restable[-1][int(errindex) - 1] if errindex else "?",
            )
        elif (errindication or errstatus) and self._accept_errors:
            self.value = self._default_value
        else:
            for resrow in restable:
                self.value = self._decode_value(resrow[-1])
        return self.value

    def _decode_value(self, value):
        """Decode the different results we could get into strings."""

        _LOGGER.debug(
            "SNMP OID %s received type=%s and data %s",
            # self._baseoid,
            type(value),
            value,
        )
        if isinstance(value, NoSuchObject):
            _LOGGER.error(
                "SNMP error for OID %s: No Such Object currently exists at this OID",
                self._baseoid,
            )
            return self._default_value

        if isinstance(value, Opaque):
            # Float data type is not supported by the pyasn1 library,
            # so we need to decode this type ourselves based on:
            # https://tools.ietf.org/html/draft-perkins-opaque-01
            if bytes(value).startswith(b"\x9f\x78"):
                return str(unpack("!f", bytes(value)[3:])[0])
            # Otherwise Opaque types should be asn1 encoded
            try:
                decoded_value, _ = decoder.decode(bytes(value))
                return str(decoded_value)
            except Exception as decode_exception:  # noqa: BLE001
                _LOGGER.error(
                    "SNMP error in decoding opaque type: %s", decode_exception
                )
                return self._default_value
        return str(value)
