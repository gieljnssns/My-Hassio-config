# Copyright (c) 2026, Renaud Allard <renaud@allard.it>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Sensor platform for the Belgian Gas Prices integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CONTRACT,
    CONF_CONTRACT_END_DATE,
    CONF_DAILY_COMPARE,
    DEFAULT_DAILY_COMPARE,
    DOMAIN,
)
from .coordinator import GasCoordinator
from .coordinator_data import CoordinatorData

_EUR_PER_KWH = "EUR/kWh"
_EUR_PER_M3 = "EUR/m³"


@dataclass(frozen=True, kw_only=True)
class GasSensorDescription(SensorEntityDescription):
    """A sensor with a pure value extractor."""

    value_fn: Callable[[CoordinatorData], float | datetime | None]
    attributes_fn: Callable[[CoordinatorData], dict[str, Any]] | None = None


def _money(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def _price_attributes(data: CoordinatorData) -> dict[str, Any]:
    snapshot = data.snapshot
    attrs: dict[str, Any] = {
        "tier": data.tier,
        "annual_kwh": round(data.annual_kwh),
        "annual_kwh_measured": data.annual_kwh_measured,
        "price_provisional": data.price_provisional,
        "card_source": data.card_source,
        "snapshot_age_hours": (
            None if data.snapshot_age_hours is None else round(data.snapshot_age_hours, 1)
        ),
        "snapshot_stale": data.snapshot_stale,
        "last_error": data.last_error,
    }
    if snapshot is not None:
        attrs["card_month"] = snapshot.publication_label
        attrs["valid_until"] = (
            None if snapshot.valid_until is None else snapshot.valid_until.isoformat()
        )
        attrs["source_url"] = snapshot.source_url
    if data.index is not None:
        attrs["index_value"] = data.index.value
        attrs["index_month"] = data.index.month
    return attrs


def _conversion_attributes(data: CoordinatorData) -> dict[str, Any]:
    return {
        "conversion_source": data.conversion.source,
        "conversion_month": data.conversion.month,
        "conversion_factor": data.conversion.factor,
    }


def _fixed_attributes(data: CoordinatorData) -> dict[str, Any]:
    fixed = data.fixed
    if fixed is None:
        return {}
    return {
        "supplier_eur": round(fixed.supplier, 2),
        "distribution_eur": round(fixed.distribution, 2),
        "metering_eur": round(fixed.metering, 2),
        "levy_eur": round(fixed.levy, 2),
    }


def _year_attributes(data: CoordinatorData) -> dict[str, Any]:
    return {
        "ytd_kwh": None if data.ytd_kwh is None else round(data.ytd_kwh, 1),
        "months": [
            {
                "month": bill.month,
                "kwh": round(bill.kwh, 1),
                "energy_eur": round(bill.energy_cost, 2),
                "network_eur": round(bill.network_cost, 2),
                "taxes_eur": round(bill.taxes_cost, 2),
                "fixed_eur": round(bill.fixed_cost, 2),
                "provisional": bill.provisional,
            }
            for bill in data.months
        ],
        "months_on_current_card": list(data.months_on_current_card),
        # Earlier contracts of the year whose supplier or card could not
        # price them: their days are not in the cost.
        "unpriced_contracts": list(data.unpriced_periods),
        "meter": data.meter,
    }


def _month_attributes(data: CoordinatorData) -> dict[str, Any]:
    """The running month's bills, every contract that supplied in it, as
    the state adds them up."""
    if not data.months:
        return {}
    month = data.months[-1].month
    bills = [bill for bill in data.months if bill.month == month]
    return {
        "kwh": round(sum(bill.kwh for bill in bills), 1),
        "energy_eur": round(sum(bill.energy_cost for bill in bills), 2),
        "network_eur": round(sum(bill.network_cost for bill in bills), 2),
        "taxes_eur": round(sum(bill.taxes_cost for bill in bills), 2),
        "fixed_eur": round(sum(bill.fixed_cost for bill in bills), 2),
        "provisional": any(bill.provisional for bill in bills),
    }


def _component(name: str) -> Callable[[CoordinatorData], float | None]:
    def value(data: CoordinatorData) -> float | None:
        return None if data.breakdown is None else getattr(data.breakdown, name)

    return value


SENSORS: tuple[GasSensorDescription, ...] = (
    GasSensorDescription(
        key="current_price",
        translation_key="current_price",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_EUR_PER_KWH,
        suggested_display_precision=4,
        value_fn=_component("all_in"),
        attributes_fn=_price_attributes,
    ),
    GasSensorDescription(
        key="current_price_m3",
        translation_key="current_price_m3",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_EUR_PER_M3,
        suggested_display_precision=4,
        value_fn=lambda d: d.price_m3,
        attributes_fn=_conversion_attributes,
    ),
    GasSensorDescription(
        key="energy_component",
        translation_key="energy_component",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_EUR_PER_KWH,
        suggested_display_precision=4,
        value_fn=_component("energy"),
    ),
    GasSensorDescription(
        key="network_component",
        translation_key="network_component",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_EUR_PER_KWH,
        suggested_display_precision=4,
        value_fn=_component("network"),
    ),
    GasSensorDescription(
        key="taxes_component",
        translation_key="taxes_component",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_EUR_PER_KWH,
        suggested_display_precision=4,
        value_fn=_component("taxes"),
    ),
    GasSensorDescription(
        key="fixed_costs_eur_per_year",
        translation_key="fixed_costs_eur_per_year",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="EUR",
        suggested_display_precision=2,
        value_fn=lambda d: None if d.fixed is None else _money(d.fixed.total),
        attributes_fn=_fixed_attributes,
    ),
    GasSensorDescription(
        key="supplier_fixed_fee_eur_per_year",
        translation_key="supplier_fixed_fee_eur_per_year",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="EUR",
        suggested_display_precision=2,
        value_fn=lambda d: None if d.fixed is None else _money(d.fixed.supplier),
    ),
    GasSensorDescription(
        key="conversion_factor",
        translation_key="conversion_factor",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="kWh/m³",
        suggested_display_precision=4,
        value_fn=lambda d: d.conversion.factor,
        attributes_fn=_conversion_attributes,
    ),
    GasSensorDescription(
        key="current_year_cost",
        translation_key="current_year_cost",
        # TOTAL with last_reset at the start of the window lets the
        # statistics engine keep each calendar year as its own period, and
        # MONETARY lets the Energy dashboard offer it as a cost entity.
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        suggested_display_precision=2,
        value_fn=lambda d: _money(d.current_year_cost),
        attributes_fn=_year_attributes,
    ),
    GasSensorDescription(
        key="current_month_cost",
        translation_key="current_month_cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        suggested_display_precision=2,
        value_fn=lambda d: _money(d.current_month_cost),
        attributes_fn=_month_attributes,
    ),
    GasSensorDescription(
        key="year_to_date_consumption",
        translation_key="year_to_date_consumption",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="kWh",
        suggested_display_precision=0,
        value_fn=lambda d: d.ytd_kwh,
    ),
    GasSensorDescription(
        key="projected_year_cost",
        translation_key="projected_year_cost",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="EUR",
        suggested_display_precision=2,
        value_fn=lambda d: _money(d.projected_year_cost),
    ),
    GasSensorDescription(
        key="projected_year_end_cost",
        translation_key="projected_year_end_cost",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="EUR",
        suggested_display_precision=2,
        value_fn=lambda d: _money(d.projected_year_end_cost),
    ),
    GasSensorDescription(
        key="projected_year_consumption",
        translation_key="projected_year_consumption",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="kWh",
        suggested_display_precision=0,
        value_fn=lambda d: d.projected_year_kwh,
    ),
    GasSensorDescription(
        key="rolling_year_consumption",
        translation_key="rolling_year_consumption",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="kWh",
        suggested_display_precision=0,
        value_fn=lambda d: d.rolling_year_kwh,
    ),
)

_POTENTIAL_SAVING = GasSensorDescription(
    key="potential_saving",
    translation_key="potential_saving",
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="EUR",
    suggested_display_precision=2,
    value_fn=lambda d: None,
)

_CONTRACT_END = GasSensorDescription(
    key="contract_end_date",
    translation_key="contract_end_date",
    device_class=SensorDeviceClass.TIMESTAMP,
    value_fn=lambda d: None,
)


def device_info(entry: ConfigEntry, label: str) -> DeviceInfo:
    """The one device every entity of an entry hangs off."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer=label,
        model=str(entry.data.get(CONF_CONTRACT, "")),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GasCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [GasSensor(coordinator, description) for description in SENSORS]
    registry = er.async_get(hass)
    optional = (
        (_CONTRACT_END, ContractEndSensor, bool(entry.data.get(CONF_CONTRACT_END_DATE))),
        (
            _POTENTIAL_SAVING,
            PotentialSavingSensor,
            bool(entry.data.get(CONF_DAILY_COMPARE, DEFAULT_DAILY_COMPARE)),
        ),
    )
    for description, sensor, wanted in optional:
        if wanted:
            entities.append(sensor(coordinator, description))
            continue
        # The option was turned off: its sensor goes, rather than staying
        # in the registry as a restored entity nothing updates.
        stale = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_{description.key}"
        )
        if stale is not None:
            registry.async_remove(stale)
    async_add_entities(entities)


class GasSensor(CoordinatorEntity[GasCoordinator], SensorEntity):
    """One figure off the coordinator's record."""

    _attr_has_entity_name = True
    # Attributes that change every tick without the state moving are kept
    # out of the recorder, which would otherwise write a row per tick.
    _unrecorded_attributes = frozenset(
        {
            "snapshot_age_hours",
            "last_error",
            "months",
            "months_on_current_card",
            "ytd_kwh",
            "ranking",
        }
    )
    entity_description: GasSensorDescription

    def __init__(self, coordinator: GasCoordinator, description: GasSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = device_info(coordinator.entry, coordinator.extractor.label)

    @property
    def native_value(self) -> float | datetime | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def last_reset(self) -> datetime | None:
        if self.entity_description.state_class != SensorStateClass.TOTAL:
            return None
        data = self.coordinator.data
        today = dt_util.now().date() if data is None else data.day
        if self.entity_description.key == "current_month_cost":
            return dt_util.start_of_local_day(date(today.year, today.month, 1))
        return dt_util.start_of_local_day(self.coordinator.window_start(today))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        attributes_fn = self.entity_description.attributes_fn
        if data is None or attributes_fn is None:
            return None
        return attributes_fn(data)


class ContractEndSensor(GasSensor):
    """When the contract ends, for a renewal reminder; it prices nothing."""

    @property
    def native_value(self) -> datetime | None:
        value = self.coordinator.entry.data.get(CONF_CONTRACT_END_DATE)
        if not value:
            return None
        try:
            return dt_util.start_of_local_day(date.fromisoformat(str(value)))
        except ValueError:
            return None

    @property
    def available(self) -> bool:
        # A date the user typed stays readable when the supplier is not.
        return True


class PotentialSavingSensor(GasSensor):
    """What the cheapest contract in the daily ranking would save a year."""

    @property
    def native_value(self) -> float | None:
        ranking = self.coordinator.daily_ranking
        saving = None if ranking is None else ranking.saving
        return None if saving is None else round(saving, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        ranking = self.coordinator.daily_ranking
        if ranking is None:
            return None
        return {
            "day": ranking.day.isoformat(),
            "own_annual_cost": ranking.own_cost,
            "ranking": [
                {
                    "supplier": row.supplier,
                    "contract": row.contract,
                    "label": row.label,
                    "annual_cost": round(row.annual_cost, 2),
                }
                for row in ranking.rows
            ],
        }
