"""The setup wizard and the options flow.

Both walk the same steps: where the household is (a postcode resolves the
region and the gas DSO), which supplier and contract it is on, the household
facts the bill needs, and how a cubic metre of its gas becomes kWh. The
options flow starts from the stored entry and writes it back.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    DateSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
from homeassistant.util import dt as dt_util

from . import calorific, postcodes
from .bill import month_key
from .compare import IndexCache, OwnContract, Quote, quote_contract, rank
from .compare_table import quote_table
from .const import (
    CALIBERS,
    CONF_ANNUAL_CONSUMPTION_KWH,
    CONF_CALIBER,
    CONF_CARD_ARCHIVE,
    CONF_CONTRACT,
    CONF_CONTRACT_END_DATE,
    CONF_CONTRACT_START_DATE,
    CONF_CONVERSION_FACTOR,
    CONF_CONVERSION_MODE,
    CONF_CUSTOM_CONNECTION_FEE,
    CONF_CUSTOM_CONTRIBUTION,
    CONF_CUSTOM_EXCISE_HIGH,
    CONF_CUSTOM_EXCISE_LOW,
    CONF_CUSTOM_FEE,
    CONF_CUSTOM_LEVY,
    CONF_CUSTOM_METERING,
    CONF_CUSTOM_PRICE,
    CONF_CUSTOM_T1_FIXED,
    CONF_CUSTOM_T1_PROP,
    CONF_CUSTOM_T2_FIXED,
    CONF_CUSTOM_T2_PROP,
    CONF_CUSTOM_TRANSPORT,
    CONF_DAILY_COMPARE,
    CONF_DSO,
    CONF_GAS_METER,
    CONF_MANUAL_BASE,
    CONF_MANUAL_FACTOR,
    CONF_MANUAL_FEE,
    CONF_MANUAL_PRICE,
    CONF_POSTCODE,
    CONF_REGION,
    CONF_STATION,
    CONF_SUPPLIER,
    CONF_SWITCH_DATE,
    CONF_TARIFF_CARD_DATE,
    CONF_YTD_FROM_CONTRACT_START,
    CONVERSION_MANUAL,
    CONVERSION_MODES,
    CONVERSION_STATION,
    CUSTOM_KEYS,
    DEFAULT_ANNUAL_CONSUMPTION_KWH,
    DEFAULT_CALIBER,
    DEFAULT_CARD_ARCHIVE,
    DEFAULT_CONVERSION_MODE,
    DEFAULT_DAILY_COMPARE,
    DOMAIN,
    DSO_CHOICES,
    MANUAL_RATE_KEYS,
    REGION_BRUSSELS,
    REGION_WALLONIA,
    REGIONS,
    SUPPLIER_CUSTOM,
)
from .contract_periods import parse_date, periods_this_year, previous_contracts, record_switch
from .providers import all_extractors
from .providers import get as get_extractor
from .providers._rates import Contract
from .providers.base import ExtractorError
from .providers.custom import build_snapshot as build_custom_snapshot
from .running_costs import Household

# How long the ranked comparison spends fetching before it shows what it has.
COMPARE_BUDGET_S = 120.0

# The date fields a household may blank to remove.
_DATE_FIELDS = (CONF_CONTRACT_START_DATE, CONF_TARIFF_CARD_DATE, CONF_CONTRACT_END_DATE)


def _suppliers_for(region: str) -> list[SelectOptionDict]:
    return sorted(
        (
            SelectOptionDict(value=extractor.id, label=extractor.label)
            for extractor in all_extractors()
            if region in extractor.regions() and extractor.deprecated_until is None
        ),
        # The expert escape hatch goes last whatever its label.
        key=lambda option: (option["value"] == SUPPLIER_CUSTOM, option["label"].lower()),
    )


def _contracts_for(supplier: str, region: str) -> list[Contract]:
    return [c for c in get_extractor(supplier).contracts if region in c.regions]


def _dso_options(region: str, candidates: tuple[str, ...]) -> list[SelectOptionDict]:
    choices = DSO_CHOICES[region]
    if candidates:
        choices = tuple(choice for choice in choices if choice[0] in candidates) or choices
    return [SelectOptionDict(value=key, label=label) for key, label in choices]


def _select(
    options: list[SelectOptionDict] | list[str], translation_key: str | None = None
) -> SelectSelector:
    config = SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
    if translation_key is not None:
        config["translation_key"] = translation_key
    return SelectSelector(config)


def _default(data: dict[str, Any], key: str, fallback: Any = vol.UNDEFINED) -> Any:
    return data.get(key, fallback)


async def _stations(hass: HomeAssistant) -> list[calorific.Station]:
    """The reception stations Atrias published a value for in either of its
    two latest months, by name: a station listed at 0 for a month is out of
    use for it only."""
    session = async_get_clientsession(hass)
    context = await hass.async_add_executor_job(calorific.build_ssl_context)
    key = await calorific.subscription_key(session)
    months = await calorific.list_months(session, context, key)
    stations: dict[str, calorific.Station] = {}
    failure: calorific.CalorificError | None = None
    for month in sorted(months)[-2:]:
        # Each month on its own: a file that cannot be read must not hide
        # the other's stations.
        try:
            values = await calorific.fetch_month(session, context, key, months[month])
        except calorific.CalorificError as err:
            failure = err
            continue
        for station in values:
            stations[station.ean] = station
    if failure is not None and not stations:
        raise failure
    return sorted(stations.values(), key=lambda station: station.name)


class _FlowSteps:
    """The steps both flows walk, over ``self._data``."""

    _data: dict[str, Any]
    _candidates: tuple[str, ...]
    _stations_cache: list[calorific.Station] | None

    if TYPE_CHECKING:
        hass: HomeAssistant

        def async_show_form(self, **kwargs: Any) -> ConfigFlowResult: ...
        def add_suggested_values_to_schema(
            self, data_schema: vol.Schema, suggested_values: Any
        ) -> vol.Schema: ...
        async def _async_finish(self) -> ConfigFlowResult: ...

    async def async_step_postcode(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            code = str(user_input.get(CONF_POSTCODE, "")).strip()
            if not code:
                self._data.pop(CONF_POSTCODE, None)
                self._candidates = ()
                return await self.async_step_region()
            match = postcodes.resolve(code)
            if match is None:
                errors[CONF_POSTCODE] = "unknown_postcode"
            elif not match.dsos:
                errors[CONF_POSTCODE] = "no_gas_network"
            else:
                self._data[CONF_POSTCODE] = code
                self._data[CONF_REGION] = match.region
                self._candidates = match.dsos
                if match.unpriced:
                    return await self.async_step_unpriced_network()
                return await self.async_step_supplier()
        # Suggested rather than a default, so a cleared field reaches here
        # empty and leads to the region instead of coming back as the old
        # postcode. A refused one is shown as typed and is not kept.
        schema = self.add_suggested_values_to_schema(
            vol.Schema({vol.Optional(CONF_POSTCODE): TextSelector()}),
            {CONF_POSTCODE: self._data.get(CONF_POSTCODE)} if user_input is None else user_input,
        )
        return self.async_show_form(step_id="postcode", data_schema=schema, errors=errors)

    async def async_step_unpriced_network(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Part of the postcode is on a network no card prices (Baarle-Hertog's
        Enexis): say so before going on with its Belgian operator."""
        if user_input is not None:
            return await self.async_step_supplier()
        code = str(self._data[CONF_POSTCODE])
        match = postcodes.resolve(code)
        assert match is not None
        labels = dict(DSO_CHOICES[match.region])
        return self.async_show_form(
            step_id="unpriced_network",
            data_schema=vol.Schema({}),
            description_placeholders={
                "postcode": code,
                "operators": ", ".join(match.unpriced),
                "dsos": ", ".join(labels[dso] for dso in match.dsos),
            },
        )

    async def async_step_region(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            if user_input[CONF_REGION] != self._data.get(CONF_REGION):
                self._data.pop(CONF_DSO, None)
            self._data[CONF_REGION] = user_input[CONF_REGION]
            return await self.async_step_supplier()
        schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=_default(self._data, CONF_REGION)): _select(
                    list(REGIONS), translation_key="region"
                )
            }
        )
        return self.async_show_form(step_id="region", data_schema=schema)

    async def async_step_supplier(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        region = self._data[CONF_REGION]
        options = _suppliers_for(region)
        if user_input is not None:
            if user_input[CONF_SUPPLIER] != self._data.get(CONF_SUPPLIER):
                self._data.pop(CONF_CONTRACT, None)
            self._data[CONF_SUPPLIER] = user_input[CONF_SUPPLIER]
            return await self.async_step_contract()
        current = self._data.get(CONF_SUPPLIER)
        default = current if any(o["value"] == current for o in options) else vol.UNDEFINED
        schema = vol.Schema({vol.Required(CONF_SUPPLIER, default=default): _select(options)})
        return self.async_show_form(step_id="supplier", data_schema=schema)

    async def async_step_contract(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        contracts = _contracts_for(self._data[CONF_SUPPLIER], self._data[CONF_REGION])
        errors: dict[str, str] = {}
        # With a change of contract recorded this year, the year's cost starts
        # with the earlier contract: counting from this one's start would
        # leave its days out, so the choice is not offered.
        switched = bool(periods_this_year(self._data, dt_util.now().date()))
        if user_input is not None:
            start = user_input.get(CONF_CONTRACT_START_DATE)
            end = user_input.get(CONF_CONTRACT_END_DATE)
            if start and end and str(end) <= str(start):
                errors[CONF_CONTRACT_END_DATE] = "end_before_start"
            else:
                for key in _DATE_FIELDS:
                    if not user_input.get(key):
                        self._data.pop(key, None)
                self._data.update({k: v for k, v in user_input.items() if v not in (None, "")})
                if not self._data.get(CONF_CONTRACT_START_DATE) or switched:
                    self._data.pop(CONF_YTD_FROM_CONTRACT_START, None)
                # The custom card is the household's own figures already.
                if self._data[CONF_SUPPLIER] != SUPPLIER_CUSTOM and (
                    self._data.get(CONF_CONTRACT_START_DATE)
                    or self._data.get(CONF_TARIFF_CARD_DATE)
                ):
                    return await self.async_step_signed_rate()
                for key in MANUAL_RATE_KEYS:
                    self._data.pop(key, None)
                return await self.async_step_dso()
        current = self._data.get(CONF_CONTRACT)
        default = current if any(c.id == current for c in contracts) else vol.UNDEFINED
        fields: dict[Any, Any] = {
            vol.Required(CONF_CONTRACT, default=default): SelectSelector(
                SelectSelectorConfig(
                    options=[SelectOptionDict(value=c.id, label=c.label) for c in contracts],
                    mode=SelectSelectorMode.LIST,
                )
            ),
            vol.Optional(CONF_CONTRACT_START_DATE): DateSelector(),
            vol.Optional(CONF_TARIFF_CARD_DATE): DateSelector(),
            vol.Optional(CONF_CONTRACT_END_DATE): DateSelector(),
        }
        if not switched:
            fields[
                vol.Optional(
                    CONF_YTD_FROM_CONTRACT_START,
                    default=bool(self._data.get(CONF_YTD_FROM_CONTRACT_START, False)),
                )
            ] = BooleanSelector()
        schema = self.add_suggested_values_to_schema(
            vol.Schema(fields),
            {key: self._data.get(key) for key in _DATE_FIELDS}
            if user_input is None
            else user_input,
        )
        return self.async_show_form(step_id="contract", data_schema=schema, errors=errors)

    async def async_step_signed_rate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """The figures the household signed at, for when the signing card
        cannot be read or the offer had figures of its own. All optional:
        left blank, the signing month's card gives them."""
        contract = next(
            (
                c
                for c in _contracts_for(self._data[CONF_SUPPLIER], self._data[CONF_REGION])
                if c.id == self._data.get(CONF_CONTRACT)
            ),
            None,
        )
        if user_input is not None:
            for key in MANUAL_RATE_KEYS:
                if user_input.get(key) is None:
                    self._data.pop(key, None)
                else:
                    self._data[key] = float(user_input[key])
            return await self.async_step_dso()
        number = NumberSelector(
            NumberSelectorConfig(min=0, max=1000, step="any", mode=NumberSelectorMode.BOX)
        )
        keys: tuple[str, ...] = (CONF_MANUAL_FEE,)
        if contract is not None and contract.kind == "fixed":
            keys = (CONF_MANUAL_PRICE, CONF_MANUAL_FEE)
        elif contract is not None and contract.kind == "indexed":
            keys = (CONF_MANUAL_FACTOR, CONF_MANUAL_BASE, CONF_MANUAL_FEE)
        schema = self.add_suggested_values_to_schema(
            vol.Schema({vol.Optional(key): number for key in keys}),
            {key: self._data.get(key) for key in keys},
        )
        return self.async_show_form(step_id="signed_rate", data_schema=schema)

    async def async_step_dso(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        region = self._data[CONF_REGION]
        options = _dso_options(region, getattr(self, "_candidates", ()))
        if user_input is not None:
            self._data[CONF_DSO] = user_input[CONF_DSO]
            if self._data[CONF_SUPPLIER] == SUPPLIER_CUSTOM:
                return await self.async_step_custom_energy()
            for key in CUSTOM_KEYS:
                self._data.pop(key, None)
            return await self.async_step_household()
        current = self._data.get(CONF_DSO)
        valid = [o["value"] for o in options]
        default = current if current in valid else (valid[0] if len(valid) == 1 else vol.UNDEFINED)
        schema = vol.Schema({vol.Required(CONF_DSO, default=default): _select(options)})
        return self.async_show_form(step_id="dso", data_schema=schema)

    def _custom_form(self, step_id: str, keys: tuple[str, ...]) -> ConfigFlowResult:
        number = NumberSelector(
            NumberSelectorConfig(min=0, max=10_000, step="any", mode=NumberSelectorMode.BOX)
        )
        schema = self.add_suggested_values_to_schema(
            vol.Schema({vol.Required(key): number for key in keys}),
            {key: self._data.get(key) for key in keys},
        )
        return self.async_show_form(step_id=step_id, data_schema=schema)

    async def async_step_custom_energy(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data.update({k: float(v) for k, v in user_input.items()})
            return await self.async_step_custom_network()
        return self._custom_form("custom_energy", (CONF_CUSTOM_PRICE, CONF_CUSTOM_FEE))

    async def async_step_custom_network(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        region = self._data[CONF_REGION]
        keys: tuple[str, ...] = (
            CONF_CUSTOM_T1_FIXED,
            CONF_CUSTOM_T1_PROP,
            CONF_CUSTOM_T2_FIXED,
            CONF_CUSTOM_T2_PROP,
            CONF_CUSTOM_TRANSPORT,
            CONF_CUSTOM_METERING,
            CONF_CUSTOM_EXCISE_LOW,
            CONF_CUSTOM_EXCISE_HIGH,
            CONF_CUSTOM_CONTRIBUTION,
        )
        if region == REGION_WALLONIA:
            keys += (CONF_CUSTOM_CONNECTION_FEE,)
        if region == REGION_BRUSSELS:
            keys += (CONF_CUSTOM_LEVY,)
        if user_input is not None:
            for key in CUSTOM_KEYS:
                if key in (CONF_CUSTOM_PRICE, CONF_CUSTOM_FEE):
                    continue
                if key in user_input:
                    self._data[key] = float(user_input[key])
                else:
                    self._data.pop(key, None)
            return await self.async_step_household()
        return self._custom_form("custom_network", keys)

    async def async_step_household(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        brussels = self._data[CONF_REGION] == REGION_BRUSSELS
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_GAS_METER):
                self._data.pop(CONF_GAS_METER, None)
            self._data.update(user_input)
        if user_input is not None and (
            get_extractor(self._data[CONF_SUPPLIER]).images_only
            and not user_input.get(CONF_CARD_ARCHIVE)
        ):
            # Its cards are page images: the archive's reading is the only
            # card the entry can be priced on. The form comes back with the
            # rest as entered.
            errors[CONF_CARD_ARCHIVE] = "card_archive_needed"
        elif user_input is not None:
            if not brussels:
                self._data.pop(CONF_CALIBER, None)
            if self._data[CONF_CONVERSION_MODE] == CONVERSION_MANUAL:
                return await self.async_step_factor()
            return await self.async_step_station()
        fields: dict[Any, Any] = {
            vol.Required(
                CONF_ANNUAL_CONSUMPTION_KWH,
                default=float(
                    self._data.get(CONF_ANNUAL_CONSUMPTION_KWH, DEFAULT_ANNUAL_CONSUMPTION_KWH)
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=1_000_000,
                    step=100,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="kWh",
                )
            ),
        }
        if brussels:
            fields[
                vol.Required(CONF_CALIBER, default=self._data.get(CONF_CALIBER, DEFAULT_CALIBER))
            ] = _select(list(CALIBERS), translation_key="caliber")
        fields[vol.Optional(CONF_GAS_METER)] = EntitySelector(
            EntitySelectorConfig(domain=Platform.SENSOR, device_class=["gas", "energy"])
        )
        fields[
            vol.Required(
                CONF_CONVERSION_MODE,
                default=self._data.get(CONF_CONVERSION_MODE, DEFAULT_CONVERSION_MODE),
            )
        ] = _select(list(CONVERSION_MODES), translation_key="conversion_mode")
        fields[
            vol.Required(
                CONF_CARD_ARCHIVE,
                default=bool(self._data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE)),
            )
        ] = BooleanSelector()
        fields[
            vol.Required(
                CONF_DAILY_COMPARE,
                default=bool(self._data.get(CONF_DAILY_COMPARE, DEFAULT_DAILY_COMPARE)),
            )
        ] = BooleanSelector()
        schema = self.add_suggested_values_to_schema(
            vol.Schema(fields), {CONF_GAS_METER: self._data.get(CONF_GAS_METER)}
        )
        return self.async_show_form(step_id="household", data_schema=schema, errors=errors)

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data[CONF_STATION] = user_input[CONF_STATION]
            self._data.pop(CONF_CONVERSION_FACTOR, None)
            return await self._async_finish()
        if getattr(self, "_stations_cache", None) is None:
            try:
                async with asyncio.timeout(60):
                    self._stations_cache = await _stations(self.hass)
            except (calorific.CalorificError, TimeoutError):
                self._stations_cache = None
                errors["base"] = "stations_unavailable"
        if not self._stations_cache and self._data.get(CONF_STATION):
            # Atrias could not be read, but the entry names its station
            # already: the list is only needed to pick another, so its
            # settings save with the one it has.
            self._data.pop(CONF_CONVERSION_FACTOR, None)
            return await self._async_finish()
        if not self._stations_cache:
            # Atrias could not be read: a factor from the bill still works.
            self._data[CONF_CONVERSION_MODE] = CONVERSION_MANUAL
            return await self.async_step_factor(errors=errors or {"base": "stations_unavailable"})
        options = [
            SelectOptionDict(value=station.ean, label=station.name)
            for station in self._stations_cache
        ]
        current = self._data.get(CONF_STATION)
        if current and not any(o["value"] == current for o in options):
            # Out of use lately: still the entry's, priced on its last value,
            # and kept on offer so its settings save without another pick.
            options.append(SelectOptionDict(value=current, label=current))
        default = current or vol.UNDEFINED
        schema = vol.Schema({vol.Required(CONF_STATION, default=default): _select(options)})
        return self.async_show_form(step_id="station", data_schema=schema, errors=errors)

    async def async_step_factor(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, str] | None = None,
    ) -> ConfigFlowResult:
        if user_input is not None:
            if user_input.get(CONF_CONVERSION_FACTOR) is None:
                # No bill at hand: the station list, the forms having no way
                # back to the mode picked on the household step.
                self._data[CONF_CONVERSION_MODE] = CONVERSION_STATION
                return await self.async_step_station()
            self._data[CONF_CONVERSION_FACTOR] = float(user_input[CONF_CONVERSION_FACTOR])
            self._data[CONF_CONVERSION_MODE] = CONVERSION_MANUAL
            self._data.pop(CONF_STATION, None)
            return await self._async_finish()
        schema = vol.Schema(
            {
                vol.Optional(CONF_CONVERSION_FACTOR): NumberSelector(
                    NumberSelectorConfig(
                        min=9.0,
                        max=13.0,
                        step="any",
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="kWh/m³",
                    )
                )
            }
        )
        # Suggested rather than a default, so a cleared field reaches here
        # empty instead of coming back as the old factor.
        schema = self.add_suggested_values_to_schema(
            schema, {CONF_CONVERSION_FACTOR: self._data.get(CONF_CONVERSION_FACTOR)}
        )
        return self.async_show_form(step_id="factor", data_schema=schema, errors=errors or {})


def _title(data: dict[str, Any]) -> str:
    """The title the wizard gives an entry: its contract's label, that of a
    contract the supplier withdrew included."""
    extractor = get_extractor(data[CONF_SUPPLIER])
    return extractor.contract_label(data[CONF_CONTRACT]) or extractor.label


class BeGasPricesConfigFlow(_FlowSteps, ConfigFlow, domain=DOMAIN):
    """The setup wizard."""

    VERSION = 1

    def __init__(self) -> None:
        self._data = {}
        self._candidates = ()
        self._stations_cache = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self.async_step_postcode(user_input)

    async def _async_finish(self) -> ConfigFlowResult:
        return self.async_create_entry(title=_title(self._data), data=self._data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BeGasPricesOptionsFlow()


class BeGasPricesOptionsFlow(_FlowSteps, OptionsFlow):
    """Edit the settings, compare contracts, or record a supplier switch."""

    def __init__(self) -> None:
        self._candidates = ()
        self._stations_cache = None
        self._compare_supplier: str | None = None
        self._quotes: tuple[Quote, Quote] | None = None
        self._ranking: tuple[list[Quote], int] | None = None
        self._rank_task: asyncio.Task[tuple[list[Quote], int]] | None = None
        self._switch_date: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["settings", "compare", "compare_all", "switch"]
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._data = dict(self.config_entry.data)
        code = self._data.get(CONF_POSTCODE)
        match = postcodes.resolve(str(code)) if code else None
        self._candidates = () if match is None else match.dsos
        return await self.async_step_postcode()

    async def _async_finish(self) -> ConfigFlowResult:
        entry = self.config_entry
        # The title the wizard gave follows the contract; one the user typed
        # is theirs and stays.
        try:
            made = entry.title == _title(dict(entry.data))
        except ExtractorError:
            made = False
        title = _title(self._data) if made else entry.title
        self.hass.config_entries.async_update_entry(entry, data=self._data, title=title)
        if entry.state is not ConfigEntryState.LOADED:
            # An entry stopped at setup (a contract its supplier withdrew)
            # has no update listener yet to set it up again.
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
        return self.async_create_entry(data={})

    # ---- comparison ----------------------------------------------------------

    def _household(self) -> Household:
        coordinator = getattr(self.config_entry, "runtime_data", None)
        measured = getattr(coordinator, "household", None)
        if isinstance(measured, Household):
            return measured
        data = self.config_entry.data
        return Household(
            dso=str(data[CONF_DSO]),
            caliber=str(data.get(CONF_CALIBER, DEFAULT_CALIBER)),
            annual_kwh=float(data.get(CONF_ANNUAL_CONSUMPTION_KWH, DEFAULT_ANNUAL_CONSUMPTION_KWH)),
        )

    def _own_contract(self) -> OwnContract | None:
        """The household's contract as the comparisons quote it: on the card
        the loaded entry holds, with the energy leg it is billed on, else a
        custom entry's typed card; None leaves it to the card of the month."""
        own_contract = getattr(
            getattr(self.config_entry, "runtime_data", None), "own_contract", None
        )
        held = own_contract() if callable(own_contract) else None
        if isinstance(held, OwnContract):
            return held
        data = self.config_entry.data
        if data[CONF_SUPPLIER] != SUPPLIER_CUSTOM:
            return None
        return OwnContract(
            get_extractor(SUPPLIER_CUSTOM),
            str(data[CONF_CONTRACT]),
            build_custom_snapshot(dict(data)),
        )

    async def async_step_compare(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        region = self.config_entry.data[CONF_REGION]
        if user_input is not None:
            self._compare_supplier = user_input[CONF_SUPPLIER]
            return await self.async_step_compare_contract()
        # The custom supplier has no card of its own to quote.
        options = [o for o in _suppliers_for(region) if o["value"] != SUPPLIER_CUSTOM]
        schema = vol.Schema({vol.Required(CONF_SUPPLIER): _select(options)})
        return self.async_show_form(step_id="compare", data_schema=schema)

    async def async_step_compare_contract(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        data = self.config_entry.data
        region = data[CONF_REGION]
        supplier = self._compare_supplier or data[CONF_SUPPLIER]
        contracts = _contracts_for(supplier, region)
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            household = self._household()
            month = month_key(dt_util.now().date())
            use_archive = bool(data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE))
            held = self._own_contract()
            indices = IndexCache(held)
            mine = quote_contract(
                session,
                get_extractor(data[CONF_SUPPLIER]),
                data[CONF_CONTRACT],
                region,
                household,
                month,
                indices,
                use_archive=use_archive,
                card=None if held is None else held.card,
                read_by_ocr=held is not None and held.read_by_ocr,
            )
            if (supplier, user_input[CONF_CONTRACT]) == (data[CONF_SUPPLIER], data[CONF_CONTRACT]):
                # The household's own contract: one quote, at what it pays.
                own = await mine
                other = own
            else:
                other, own = await asyncio.gather(
                    quote_contract(
                        session,
                        get_extractor(supplier),
                        user_input[CONF_CONTRACT],
                        region,
                        household,
                        month,
                        indices,
                        use_archive=use_archive,
                    ),
                    mine,
                )
            self._quotes = (own, other)
            return await self.async_step_compare_result()
        schema = vol.Schema(
            {
                vol.Required(CONF_CONTRACT): SelectSelector(
                    SelectSelectorConfig(
                        options=[SelectOptionDict(value=c.id, label=c.label) for c in contracts],
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="compare_contract", data_schema=schema)

    async def async_step_compare_result(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None or self._quotes is None:
            return self.async_abort(reason="compare_done")
        own, other = self._quotes
        return self.async_show_form(
            step_id="compare_result",
            data_schema=vol.Schema({}),
            description_placeholders={
                "table": quote_table([own] if other is own else [own, other], own=own),
                "annual_kwh": f"{self._household().annual_kwh:.0f}",
            },
        )

    async def async_step_compare_all(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._rank_task is None:
            data = self.config_entry.data
            self._rank_task = self.hass.async_create_task(
                rank(
                    async_get_clientsession(self.hass),
                    data[CONF_REGION],
                    self._household(),
                    month_key(dt_util.now().date()),
                    use_archive=bool(data.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE)),
                    budget_s=COMPARE_BUDGET_S,
                    own=self._own_contract(),
                )
            )
        if not self._rank_task.done():
            return self.async_show_progress(
                step_id="compare_all",
                progress_action="compare_all",
                progress_task=self._rank_task,
            )
        self._ranking = self._rank_task.result()
        return self.async_show_progress_done(next_step_id="compare_all_result")

    async def async_step_compare_all_result(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None or self._ranking is None:
            return self.async_abort(reason="compare_done")
        quotes, skipped = self._ranking
        data = self.config_entry.data
        own = next(
            (
                q
                for q in quotes
                if (q.supplier, q.contract) == (data[CONF_SUPPLIER], data[CONF_CONTRACT])
            ),
            None,
        )
        return self.async_show_form(
            step_id="compare_all_result",
            data_schema=vol.Schema({}),
            description_placeholders={
                "table": quote_table(quotes, own=own),
                "annual_kwh": f"{self._household().annual_kwh:.0f}",
                "skipped": str(skipped),
            },
        )

    # ---- supplier switch -------------------------------------------------------

    async def async_step_switch(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Record that the household changed contract this year: the current
        settings become an earlier contract billed up to the day before the
        switch, and the steps that follow set up the new one."""
        errors: dict[str, str] = {}
        today = dt_util.now().date()
        if user_input is not None:
            switched = date.fromisoformat(str(user_input[CONF_SWITCH_DATE]))
            data = self.config_entry.data
            # The contract the change closes must have supplied a day of this
            # year: from 1 January, the day after the last change recorded,
            # or its own start, whichever comes last.
            began = parse_date(data.get(CONF_CONTRACT_START_DATE))
            first = max(
                [date(today.year, 1, 1)]
                + [
                    date.fromisoformat(p["until"]) + timedelta(days=1)
                    for p in previous_contracts(data)
                ]
                + ([] if began is None else [began])
            )
            if not first < switched <= today:
                errors[CONF_SWITCH_DATE] = "switch_date_invalid"
            else:
                self._data = record_switch(dict(self.config_entry.data), switched)
                self._candidates = ()
                code = self._data.get(CONF_POSTCODE)
                match = postcodes.resolve(str(code)) if code else None
                self._candidates = () if match is None else match.dsos
                return await self.async_step_supplier()
        schema = vol.Schema({vol.Required(CONF_SWITCH_DATE): DateSelector()})
        return self.async_show_form(step_id="switch", data_schema=schema, errors=errors)
