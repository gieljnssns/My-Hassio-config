"""Diagnostics support for Huawei Solar."""

from __future__ import annotations

from importlib.metadata import version
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from huawei_solar import HuaweiSolarBridge

from . import HuaweiSolarUpdateCoordinators
from .const import DATA_UPDATE_COORDINATORS, DOMAIN

TO_REDACT = {CONF_PASSWORD}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinators: list[HuaweiSolarUpdateCoordinators] = hass.data[DOMAIN][
        entry.entry_id
    ][DATA_UPDATE_COORDINATORS]

    diagnostics_data = {
        "config_entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "pymodbus_version": version("pymodbus"),
    }
    for ucs in coordinators:
        diagnostics_data[
            f"slave_{ucs.bridge.slave_id}"
        ] = await _build_bridge_diagnostics_info(ucs.bridge)

        diagnostics_data[f"slave_{ucs.bridge.slave_id}_inverter_data"] = (
            ucs.inverter_update_coordinator.data
        )

        if ucs.power_meter_update_coordinator:
            diagnostics_data[f"slave_{ucs.bridge.slave_id}_power_meter_data"] = (
                ucs.power_meter_update_coordinator.data
            )

        if ucs.energy_storage_update_coordinator:
            diagnostics_data[f"slave_{ucs.bridge.slave_id}_battery_data"] = (
                ucs.energy_storage_update_coordinator.data
            )

        if ucs.configuration_update_coordinator:
            diagnostics_data[f"slave_{ucs.bridge.slave_id}_config_data"] = (
                ucs.configuration_update_coordinator.data
            )

        if ucs.optimizer_update_coordinator:
            diagnostics_data[f"slave_{ucs.bridge.slave_id}_optimizer_data"] = (
                ucs.optimizer_update_coordinator.data
            )

    return diagnostics_data


async def _build_bridge_diagnostics_info(bridge: HuaweiSolarBridge) -> dict[str, Any]:
    diagnostics_data = {
        "model_name": bridge.model_name,
        "firmware_version": bridge.firmware_version,
        "software_version": bridge.software_version,
        "pv_string_count": bridge.pv_string_count,
        "has_optimizers": bridge.has_optimizers,
        "battery_type": bridge.battery_type,
        "battery_1_type": bridge.battery_1_type,
        "battery_2_type": bridge.battery_2_type,
        "power_meter_type": bridge.power_meter_type,
        "supports_capacity_control": bridge.supports_capacity_control,
    }

    return diagnostics_data
