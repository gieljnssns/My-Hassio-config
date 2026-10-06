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

"""Sensors exposed by be_water_prices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO, UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from ._redact import scrub_tokens, sensitive_tokens, source_url_without_commune
from .const import (
    CONF_COMMUNE,
    CONF_UTILITY,
    DOMAIN,
    REGION_FLANDERS,
)
from .coordinator import CoordinatorData, WaterCoordinator, utility_device_info
from .providers import get

# Kept under the old private name so the sensor attribute and the
# device's configuration_url redact through one helper.
_source_url_without_commune = source_url_without_commune

EUR_PER_M3 = f"{CURRENCY_EURO}/{UnitOfVolume.CUBIC_METERS}"
EUR_PER_YEAR = f"{CURRENCY_EURO}/year"

# Strips the trailing "(Commune)" suffix from publication labels so
# the sensor's extra_state_attributes don't expose the user's commune
# in screenshots, the recorder, or HA exports. Mirrors the redaction
# applied by diagnostics.py to CONF_COMMUNE_LABEL.


def _publication_label_without_commune(label: str, tokens: list[str]) -> str:
    """Return ``label`` with a trailing ``(commune)`` suffix removed.

    Only a suffix that actually names the configured commune goes. The
    parenthetical is not reserved for the commune: VIVAQUA publishes
    "Price from January 1st 2026 (VAT included 6 %)" and De Watergroep's
    drinkwater-only fallback carries its own marker, and dropping those
    told the user less about their tariff while redacting nothing.

    Walks backward counting parens so nested labels like the DWG
    default-commune fallback (``"Halle (DWG-served default)"``) are
    also stripped whole. A regex with ``[^()]+`` would match only the
    innermost paren and leave the outer commune name in place.
    """
    if not tokens or not label.endswith(")"):
        return label
    depth = 0
    for i in range(len(label) - 1, -1, -1):
        ch = label[i]
        if ch == ")":
            depth += 1
        elif ch == "(":
            depth -= 1
            if depth == 0:
                inner = label[i + 1 : -1].casefold()
                if not any(token.casefold() in inner for token in tokens):
                    return label
                # Outermost ( found; drop it plus the preceding space.
                return label[: i - 1] if i > 0 and label[i - 1] == " " else label[:i]
    return label


@dataclass(frozen=True, kw_only=True)
class WaterSensorDescription(SensorEntityDescription):
    value_fn: Callable[[CoordinatorData], float | None]
    # Optional: returns the timestamp of the last reset for ``TOTAL``
    # state-class sensors (the YTD ones). HA's long-term-statistics
    # engine uses this to bucket each reset cycle as its own period;
    # without it ``TOTAL`` falls back to detecting drops as resets,
    # which is fragile around year boundaries.
    last_reset_fn: Callable[[], datetime] | None = None


def _jan_1_local() -> datetime:
    """Return the local-timezone start of the current calendar year.

    Used as ``last_reset`` for the YTD sensors so the statistics engine
    treats each calendar year as its own bucket.
    """
    return dt_util.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _basis_or_linear(data: CoordinatorData) -> float | None:
    """Headline distributor rate per m³.

    Prefers the explicit basis (Flanders block 1) or linear (Brussels);
    falls back to the Walloon CVD when neither is set so the SWDE-style
    breakdown still surfaces something on this sensor.
    """
    t = data.tariff
    if t.basis_eur_per_m3 is not None:
        return t.basis_eur_per_m3
    if t.linear_eur_per_m3 is not None:
        return t.linear_eur_per_m3
    if t.cvd_eur_per_m3:
        return t.cvd_eur_per_m3
    return None


def _comfort(data: CoordinatorData) -> float | None:
    return data.tariff.comfort_eur_per_m3


def _sanering_total(data: CoordinatorData) -> float:
    t = data.tariff
    return (
        t.sanering_bovengemeentelijk_eur_per_m3
        + t.sanering_gemeentelijk_eur_per_m3
        + t.cva_eur_per_m3
        + t.fse_eur_per_m3
    )


def _all_in_basis(data: CoordinatorData) -> float | None:
    base = _basis_or_linear(data)
    if base is None:
        return None
    san = _sanering_total(data)
    return round((base + san) * (1.0 + data.tariff.vat_rate), 4)


def _yearly_fee(data: CoordinatorData) -> float:
    return round(data.tariff.yearly_fixed_fee, 2)


def _projected_cost(data: CoordinatorData) -> float | None:
    return data.projected_annual_cost_eur


def _current_year_cost(data: CoordinatorData) -> float | None:
    return data.current_year_cost_eur


def _ytd_consumption(data: CoordinatorData) -> float | None:
    return data.ytd_consumption_m3


def _rolling_year_consumption(data: CoordinatorData) -> float | None:
    return data.year_figures.rolling_m3


def _rolling_year_cost(data: CoordinatorData) -> float | None:
    return data.year_figures.rolling_cost_eur


def _projected_year_consumption(data: CoordinatorData) -> float | None:
    return data.year_figures.projected_m3


def _projected_year_end_cost(data: CoordinatorData) -> float | None:
    return data.year_figures.projected_end_cost_eur


SENSORS: tuple[WaterSensorDescription, ...] = (
    WaterSensorDescription(
        key="yearly_fee",
        translation_key="yearly_fee",
        native_unit_of_measurement=EUR_PER_YEAR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_yearly_fee,
    ),
    WaterSensorDescription(
        key="basis_rate",
        translation_key="basis_rate",
        native_unit_of_measurement=EUR_PER_M3,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        value_fn=_basis_or_linear,
    ),
    WaterSensorDescription(
        key="comfort_rate",
        translation_key="comfort_rate",
        native_unit_of_measurement=EUR_PER_M3,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        value_fn=_comfort,
    ),
    WaterSensorDescription(
        key="sanering_rate",
        translation_key="sanering_rate",
        native_unit_of_measurement=EUR_PER_M3,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        value_fn=_sanering_total,
    ),
    WaterSensorDescription(
        key="all_in_basis",
        translation_key="all_in_basis",
        native_unit_of_measurement=EUR_PER_M3,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        value_fn=_all_in_basis,
    ),
    WaterSensorDescription(
        key="projected_annual_cost",
        translation_key="projected_annual_cost",
        native_unit_of_measurement=EUR_PER_YEAR,
        # A projection (a level that moves with the tariff and the user's
        # consumption / persons options), not an accumulator. MONETARY +
        # TOTAL with no last_reset would make the long-term-statistics sum
        # accumulate net change since the first record -- meaningless for a
        # projection. MEASUREMENT records min/mean/max level statistics
        # instead; the EUR/year unit still conveys the monetary nature.
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_projected_cost,
    ),
    WaterSensorDescription(
        key="current_year_cost",
        translation_key="current_year_cost",
        # Running bill since Jan 1: pro-rated annual fees + YTD volumetric.
        # MONETARY rules out TOTAL_INCREASING (HA only allows None or TOTAL
        # for monetary). TOTAL with a Jan 1 last_reset lets the long-term
        # stats engine treat each year as its own bucket and tolerates the
        # natural drop on Jan 1 without flagging it as a meter reset.
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=_current_year_cost,
        last_reset_fn=_jan_1_local,
    ),
    WaterSensorDescription(
        key="ytd_consumption",
        translation_key="ytd_consumption",
        # YTD m³ resets to ~0 on Jan 1, so TOTAL + last_reset is the right
        # state-class even though WATER would also accept TOTAL_INCREASING:
        # the latter would treat the Jan 1 drop as a meter reset and emit
        # a spike in the long-term-stats deltas.
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=3,
        value_fn=_ytd_consumption,
        last_reset_fn=_jan_1_local,
    ),
    # The four below are levels revised both ways, not accumulators, so
    # MEASUREMENT for the same reason as projected_annual_cost. That rules
    # out the WATER device class on the volumes, which Home Assistant only
    # accepts with TOTAL or TOTAL_INCREASING.
    WaterSensorDescription(
        key="rolling_year_consumption",
        translation_key="rolling_year_consumption",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_rolling_year_consumption,
    ),
    WaterSensorDescription(
        key="rolling_year_cost",
        translation_key="rolling_year_cost",
        native_unit_of_measurement=EUR_PER_YEAR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_rolling_year_cost,
    ),
    WaterSensorDescription(
        key="projected_year_consumption",
        translation_key="projected_year_consumption",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_projected_year_consumption,
    ),
    WaterSensorDescription(
        key="projected_year_end_cost",
        translation_key="projected_year_end_cost",
        native_unit_of_measurement=CURRENCY_EURO,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_projected_year_end_cost,
    ),
)


def _is_applicable(desc: WaterSensorDescription, *, region: str) -> bool:
    """Filter sensors that don't apply to this entry's utility/options.

    Comfort tarief is a Flemish-only construct -- creating the entity
    for Brussels or Wallonia entries leaves it permanently ``unknown``,
    which is just noise on the device card.

    The meter-driven sensors (the YTD pair and the rolling and projected
    year) are always created: even without a configured water meter the
    entities show as ``unknown`` until the user wires one up via the
    OptionsFlow OR via the Energy dashboard. Adding the meter via the
    OptionsFlow triggers a reload; adding it via the Energy dashboard now
    also surfaces values on the next coordinator tick without requiring an
    HA restart, because the entity is already there waiting.
    """
    return not (desc.key == "comfort_rate" and region != REGION_FLANDERS)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WaterCoordinator = hass.data[DOMAIN][entry.entry_id]
    region = get(entry.data[CONF_UTILITY]).region
    applicable = [desc for desc in SENSORS if _is_applicable(desc, region=region)]
    async_add_entities(WaterSensor(coordinator, desc) for desc in applicable)


@callback
def async_remove_inapplicable_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop registry entries for sensors this operator does not produce.

    Reconfiguring a Flemish entry to Brussels or Wallonia stops the
    comfort rate being created, but the registry entry survives and Home
    Assistant shows it as restored, with the "no longer being provided"
    banner and a delete button. Tidy it away instead, the way
    statistics.py already clears the long-term rows it leaves behind.

    Called from __init__ after the backfill rather than during platform
    setup, because the statistics cleanup finds those orphan rows *by*
    the registry entry: removing it first left the rows behind forever.
    """
    region = get(entry.data[CONF_UTILITY]).region
    ent_reg = er.async_get(hass)
    keep = {desc.key for desc in SENSORS if _is_applicable(desc, region=region)}
    for desc in SENSORS:
        if desc.key in keep:
            continue
        entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{desc.key}")
        if entity_id is not None:
            ent_reg.async_remove(entity_id)


@dataclass
class _ResetGuardState(ExtraStoredData):
    """The drop-guard's memory, kept across restarts.

    Both halves matter. Without ``last_native`` the first value after a
    restart has nothing to be compared against, so a drop that happens
    over the restart goes unnoticed. Without ``reset_at`` the guard
    forgets a drop it already recorded and hands the recorder a negative
    delta for a cycle it had already closed.
    """

    reset_at: datetime | None
    last_native: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "reset_at": self.reset_at.isoformat() if self.reset_at is not None else None,
            "last_native": self.last_native,
        }


class WaterSensor(CoordinatorEntity[WaterCoordinator], SensorEntity, RestoreEntity):
    _attr_has_entity_name = True
    entity_description: WaterSensorDescription

    def __init__(
        self,
        coordinator: WaterCoordinator,
        description: WaterSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = utility_device_info(coordinator)
        # Timestamp of the last mid-cycle decrease for a TOTAL sensor, and
        # the value it was measured against. See _handle_coordinator_update.
        # Both are restored in async_added_to_hass so a restart neither
        # forgets a drop already recorded nor misses one that happens while
        # the entity is down.
        self._reset_at: datetime | None = None
        self._last_native: float | None = None

    @property
    def extra_restore_state_data(self) -> _ResetGuardState | None:
        if self.entity_description.last_reset_fn is None:
            return None
        return _ResetGuardState(self._reset_at, self._last_native)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.entity_description.last_reset_fn is None:
            return
        stored = await self.async_get_last_extra_data()
        if stored is not None:
            data = stored.as_dict()
            raw = data.get("reset_at")
            if isinstance(raw, str):
                self._reset_at = dt_util.parse_datetime(raw)
            last = data.get("last_native")
            if isinstance(last, (int, float)) and not isinstance(last, bool):
                self._last_native = float(last)
        # The platform writes the first state straight after this returns,
        # without a coordinator update, so the guard has to judge that
        # value here, restore data or not. Left to the next update, a drop
        # over the restart went out under last year's last_reset and the
        # reset then moved a second time inside the same cycle, which the
        # statistics engine counts as another whole year; and with nothing
        # restored the first value went unrecorded, so a drop right after
        # it was not a drop at all.
        value = self.native_value
        if value is not None:
            self._note_value(value)

    def _note_value(self, value: float | None) -> None:
        # A TOTAL sensor (current_year_cost / ytd_consumption) can legitimately
        # decrease mid-cycle without crossing Jan 1: a meter swap floors YTD to
        # ~0, or a tariff refresh lowers the running cost. HA only treats a drop
        # as a reset for TOTAL_INCREASING; for plain TOTAL it records the drop as
        # a negative long-term-statistics delta unless last_reset advances. Move
        # last_reset to now on a decrease so HA opens a fresh cycle instead.
        #
        # An unknown state is not a value and does not replace the last one.
        # The recorder skips it and measures the next number against the last
        # number it compiled, so a drop across it is still a drop: forgetting
        # the reference there let a meter change that went through a tick
        # with no meter at all book the whole difference as a negative delta.
        if self.entity_description.last_reset_fn is None or value is None:
            return
        if self._last_native is not None and value < self._last_native:
            self._reset_at = dt_util.now()
        self._last_native = value

    @callback
    def _handle_coordinator_update(self) -> None:
        self._note_value(self.native_value)
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def last_reset(self) -> datetime | None:
        fn = self.entity_description.last_reset_fn
        if fn is None:
            return None
        # The later of the calendar-year start and the last mid-cycle drop.
        # On the Jan 1 rollover fn() returns the new year start, which
        # supersedes a stale prior-year drop timestamp.
        base = fn()
        if self._reset_at is not None and self._reset_at > base:
            return self._reset_at
        return base

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}
        t = self.coordinator.data.tariff
        return {
            "utility": t.utility,
            "region": t.region,
            "valid_from": t.valid_from.isoformat(),
            "valid_until": t.valid_until.isoformat() if t.valid_until else None,
            "publication_label": _publication_label_without_commune(
                t.publication_label, sensitive_tokens(self.coordinator.entry)
            ),
            "source_url": _source_url_without_commune(
                t.source_url, self.coordinator.entry.options.get(CONF_COMMUNE)
            ),
            "snapshot_age_hours": round(self.coordinator.data.snapshot_age_hours, 2),
            "snapshot_stale": self.coordinator.data.snapshot_stale,
            # Fetch errors quote the URL they failed on, and the per-commune
            # URLs carry the commune, so this needs the same scrub as the
            # two attributes above rather than being published raw.
            "last_error": scrub_tokens(
                self.coordinator.data.last_error,
                sensitive_tokens(self.coordinator.entry),
                placeholder="**redacted**",
            ),
        }
