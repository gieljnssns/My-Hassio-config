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

"""Config + options flow for be_water_prices.

Initial setup walks three steps:

  1. ``user``     -- ask for a postcode and resolve it through
                     ``providers/_postcodes`` (the ranges, the Walloon
                     per-postcode table and the Flemish carve-outs). A
                     postcode no supported operator serves falls through
                     to ``manual``.
  2. ``manual``   -- shown when the postcode does not resolve. User
                     picks a utility from the dropdown built from the
                     registry.
  3. ``options``  -- annual consumption (m³/yr) for everyone, plus
                     Flanders-only ``gedomicilieerd_persons`` (0-20)
                     and ``social_tariff`` (boolean) when the chosen
                     utility is Flemish. Block-tariff math relies on
                     persons; social tariff applies the VMM 80 %
                     reduction post-calc.

A ``reconfigure`` flow (Settings → Devices & services → entry → ⋯ →
Reconfigure) opens a menu offering two paths: re-prompt the postcode
(``reconfigure_postcode``) or pick the operator directly from the
dropdown (``reconfigure_manual``). The manual path is the escape hatch
for users whose postcode resolves to the wrong operator -- e.g. a
Pidpa ring commune that defaults to Pidpa but is actually served by
Water-link. If either path resolves to a per-commune operator (DWG /
Farys / Pidpa / Water-link), a third step (``reconfigure_commune``)
shows the commune dropdown so the user can pick their commune in the
same flow rather than needing a follow-up OptionsFlow. The dropdown
pre-fills with the saved commune when the resolved utility matches
the entry's current utility. Every path runs through
``_async_finish_reconfigure``, which rewrites the entry in place;
commune-tied options are dropped on a utility change because operator
A's commune IDs mean nothing to operator B. Annual consumption /
persons / social tariff / meter carry over.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    UnknownEntry,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    BooleanSelector,
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
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CARD_ARCHIVE,
    CONF_COMMUNE,
    CONF_COMMUNE_LABEL,
    CONF_CONSUMPTION_M3_PER_YEAR,
    CONF_PERSONS,
    CONF_POSTCODE,
    CONF_SOCIAL_TARIFF,
    CONF_UTILITY,
    CONF_WATER_METER_SENSOR,
    DEFAULT_CARD_ARCHIVE,
    DEFAULT_CONSUMPTION_M3,
    DEFAULT_PERSONS,
    DOMAIN,
    MAX_CONSUMPTION_M3,
    MAX_PERSONS,
    MIN_CONSUMPTION_M3,
    MIN_PERSONS,
    REGION_FLANDERS,
)
from .providers import all_extractors, async_load, get
from .providers._postcodes import resolve_candidates as _resolve_candidates
from .providers.base import CommuneOption

_LOGGER = logging.getLogger(__name__)


def _utility_options() -> list[SelectOptionDict]:
    return [SelectOptionDict(value=e.id, label=e.label) for e in all_extractors()]


_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_POSTCODE): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
    }
)


def _manual_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_UTILITY): SelectSelector(
                SelectSelectorConfig(
                    options=_utility_options(),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _choose_schema(candidates: tuple[str, ...]) -> vol.Schema:
    """Operator picker limited to a curated candidate list.

    Used when ``resolve_candidates`` returns more than one operator
    because the postcode is genuinely split at street level.
    """
    return vol.Schema(
        {
            vol.Required(CONF_UTILITY): SelectSelector(
                SelectSelectorConfig(
                    options=[SelectOptionDict(value=c, label=get(c).label) for c in candidates],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _commune_for_postcode(utility_id: str, postcode: str | None) -> str | None:
    """The commune an operator bills ``postcode`` at, when it says.

    Three operators do today. Water-link's card bills 2070, Zwijndrecht and
    Burcht, and Hove, Mortsel and Edegem in the ring group rather than at
    the Antwerpen default the no-commune path would otherwise serve.
    Pidpa's Nijlen, Wommelgem and Kasterlee publish a lower gemeentelijke
    saneringsbijdrage than the other 60 communes its Geel default stands
    for. Farys bills Drogenbos and the four Zaventem cards away from its
    Gent-centrum default.
    """
    if not postcode:
        return None
    hook = get(utility_id).commune_for_postcode
    return None if hook is None else hook(postcode)


def _options_schema(
    current: dict[str, Any],
    *,
    flanders: bool,
    communes: tuple[CommuneOption, ...] = (),
    suggested_commune: str | None = None,
) -> vol.Schema:
    fields: dict[Any, Any] = {
        vol.Required(
            CONF_CONSUMPTION_M3_PER_YEAR,
            default=current.get(CONF_CONSUMPTION_M3_PER_YEAR, DEFAULT_CONSUMPTION_M3),
        ): NumberSelector(
            NumberSelectorConfig(
                min=MIN_CONSUMPTION_M3,
                max=MAX_CONSUMPTION_M3,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        ),
    }
    if flanders:
        fields[
            vol.Required(
                CONF_PERSONS,
                default=current.get(CONF_PERSONS, DEFAULT_PERSONS),
            )
        ] = NumberSelector(
            NumberSelectorConfig(
                min=MIN_PERSONS,
                max=MAX_PERSONS,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        )
        fields[
            vol.Required(
                CONF_SOCIAL_TARIFF,
                default=current.get(CONF_SOCIAL_TARIFF, False),
            )
        ] = BooleanSelector()

    # Per-commune utilities (De Watergroep, Farys, Pidpa, Water-link) get a
    # commune dropdown. The id is the utility's internal opaque
    # identifier (GUID for DWG, integer for Farys, name for Water-link).
    if communes:
        commune_default = current.get(CONF_COMMUNE) or suggested_commune
        fields[
            vol.Optional(
                CONF_COMMUNE,
                description={"suggested_value": commune_default} if commune_default else None,
            )
        ] = SelectSelector(
            SelectSelectorConfig(
                options=[SelectOptionDict(value=c.id, label=c.label) for c in communes],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )

    # Optional: a water-meter sensor (cumulative m³) that powers the
    # ``current_year_cost`` YTD sensor. Filtered to entities whose
    # device_class is ``water`` so the dropdown only surfaces sensors
    # the integration actually knows how to read.
    meter_default = current.get(CONF_WATER_METER_SENSOR)
    fields[
        vol.Optional(
            CONF_WATER_METER_SENSOR,
            description={"suggested_value": meter_default} if meter_default else None,
        )
    ] = EntitySelector(
        EntitySelectorConfig(
            domain="sensor",
            device_class=SensorDeviceClass.WATER,
        )
    )
    # Whether a refresh that fails with nothing fresh to serve may take
    # the card the project's daily archive holds for this utility and
    # commune. The request names both, so it is the household's call.
    fields[
        vol.Required(
            CONF_CARD_ARCHIVE,
            default=current.get(CONF_CARD_ARCHIVE, DEFAULT_CARD_ARCHIVE),
        )
    ] = BooleanSelector()
    return vol.Schema(fields)


def _is_flanders(utility_id: str) -> bool:
    return get(utility_id).region == REGION_FLANDERS


async def _async_communes(hass: HomeAssistant, utility_id: str) -> tuple[CommuneOption, ...]:
    """Return the commune list for a per-commune utility, or () otherwise.

    Network failures are swallowed -- the OptionsFlow falls back to
    no commune selector rather than blocking the user.
    """
    extractor = get(utility_id)
    if not extractor.supports_communes:
        return ()
    assert extractor.list_communes is not None
    try:
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        session = async_get_clientsession(hass)
        return await extractor.list_communes(session)
    except Exception:  # network or parser failure: degrade gracefully
        _LOGGER.exception("could not fetch commune list for %s", utility_id)
        return ()


def _warn_stale_commune(utility_id: str) -> None:
    """Say that a saved commune is being dropped, without naming it.

    The setup-time sweep says so when a blocklisted commune goes; the
    two flow-side drops, a saved commune no longer in the operator's
    live list, moved the bill to the operator-wide default in silence.
    The commune stays out of the log, as everywhere else.
    """
    _LOGGER.warning(
        "%s: the saved commune is no longer in the operator's list; it is dropped and "
        "the operator-wide default is priced until a commune is picked again",
        get(utility_id).label,
    )


class BeWaterPricesConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg, unused-ignore]
    VERSION = 2

    def __init__(self) -> None:
        self._utility: str | None = None
        # The postcode the user entered (when they came through the
        # postcode path). Carried into the entry's options so future
        # migrations can re-route on resolver changes.
        self._postcode: str | None = None
        # Candidate operators for a postcode that resolves to multiple
        # utilities (street-level splits). Populated in
        # ``async_step_user`` / ``async_step_reconfigure_postcode`` when
        # the resolver returns >1 candidate; consumed by
        # ``async_step_choose`` / ``async_step_reconfigure_choose``.
        self._candidates: tuple[str, ...] = ()
        # Carry a manual-picker reconfigure commune choice across steps so
        # ``_async_finish_reconfigure`` can layer it on top of the trimmed
        # options when the user picked a per-commune operator.
        self._reconfigure_commune: str | None = None
        self._reconfigure_commune_label: str | None = None
        # Whether the commune step was actually rendered and submitted.
        # Without it a cleared selection is indistinguishable from the
        # step never having been shown.
        self._reconfigure_commune_submitted: bool = False
        # Set by ``async_step_reconfigure_commune`` when the saved
        # commune is no longer in the live list (phantom blocklist
        # addition, operator renumber). Forces ``_async_finish_reconfigure``
        # to drop the stale commune even if the user submits the form
        # without picking a replacement.
        self._drop_stale_reconfigure_commune: bool = False
        # Residents and social tariff, asked for on a move into Flanders.
        self._household: dict[str, Any] | None = None
        # Cache the live commune list across form-render / form-submit
        # within one flow instance. Without this each step makes two
        # HTTP calls to the operator's dropdown page, and a transient
        # second-call failure silently drops the user's commune pick.
        self._communes_cache: dict[str, tuple[CommuneOption, ...]] = {}

    async def _async_communes_cached(self, utility_id: str) -> tuple[CommuneOption, ...]:
        """``_async_communes`` memoised per flow instance + utility.

        Only caches non-empty results. A transient network / parser
        failure inside ``_async_communes`` collapses to an empty tuple;
        caching that would lock the flow into an empty dropdown for
        its entire lifetime even though a follow-up retry might
        succeed. Non-per-commune operators also return ``()`` quickly
        without a network call so re-checking them is cheap.
        """
        cached = self._communes_cache.get(utility_id)
        if cached:
            return cached
        fresh = await _async_communes(self.hass, utility_id)
        if fresh:
            self._communes_cache[utility_id] = fresh
        return fresh

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            # Warm the extractor registry off-loop before the chained
            # steps call get() / all_extractors(); importing the provider
            # modules is blocking work HA forbids on the loop.
            await async_load(self.hass)
            postcode = user_input[CONF_POSTCODE].strip()
            self._postcode = postcode
            candidates = _resolve_candidates(postcode)
            if len(candidates) == 1:
                self._utility = candidates[0]
                return await self.async_step_options()
            if len(candidates) > 1:
                self._candidates = candidates
                return await self.async_step_choose()
            return await self.async_step_manual()
        return self.async_show_form(step_id="user", data_schema=_USER_SCHEMA)

    async def async_step_choose(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Operator chooser shown when the postcode is split.

        The user picks one of the two operators that genuinely
        share the postcode at street level (e.g. 8400 Oostende, where
        DWG serves Stene and Farys serves Mariakerke).
        """
        if not self._candidates:
            return self.async_abort(reason="invalid_flow_state")
        if user_input is not None:
            self._utility = user_input[CONF_UTILITY]
            return await self.async_step_options()
        return self.async_show_form(step_id="choose", data_schema=_choose_schema(self._candidates))

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._utility = user_input[CONF_UTILITY]
            return await self.async_step_options()
        return self.async_show_form(step_id="manual", data_schema=_manual_schema())

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._utility is None:
            return self.async_abort(reason="invalid_flow_state")
        await self.async_set_unique_id(f"{DOMAIN}_{self._utility}")
        self._abort_if_unique_id_configured()

        communes = await self._async_communes_cached(self._utility)
        if user_input is not None:
            final = dict(user_input)
            if self._postcode is not None:
                final[CONF_POSTCODE] = self._postcode
            # An empty-string commune id can only come from a UI / API
            # path that fed back an unset SelectSelector default; treat
            # it as "no selection" before label resolution so we don't
            # persist "" and later crash fetch_for_commune("").
            if final.get(CONF_COMMUNE) == "":
                final.pop(CONF_COMMUNE, None)
            chosen = final.get(CONF_COMMUNE)
            if chosen is not None:
                # Resolve the opaque commune id to its display label so the
                # very first publication_label / diagnostics dump shows
                # "Gent" rather than the bare GUID; the OptionsFlow does
                # the same on later edits.
                for option in communes:
                    if option.id == chosen:
                        final[CONF_COMMUNE_LABEL] = option.label
                        break
            return self.async_create_entry(
                title=get(self._utility).label,
                data={CONF_UTILITY: self._utility},
                options=final,
            )
        return self.async_show_form(
            step_id="options",
            data_schema=_options_schema(
                {},
                flanders=_is_flanders(self._utility),
                communes=communes,
                suggested_commune=_commune_for_postcode(self._utility, self._postcode),
            ),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Reconfigure entry point: offer postcode re-resolve or manual pick.

        Surfaced as Settings → Devices & services → entry → ⋯ →
        Reconfigure. Two paths:

        * ``reconfigure_postcode`` re-prompts the postcode and re-runs
          the resolver (useful after a move).
        * ``reconfigure_manual`` jumps straight to the utility dropdown
          (useful when the postcode resolves to the wrong operator,
          e.g. a Pidpa ring commune actually served by Water-link).
        """
        # Warm the extractor registry off-loop: the reconfigure sub-steps
        # call get() / all_extractors(), and importing the provider modules
        # is blocking work HA forbids on the loop. The build is cached, so
        # warming once here covers every sub-step in this flow.
        await async_load(self.hass)
        # Reset every cross-step instance var so a user backing out of
        # a previous reconfigure attempt and re-entering does not see
        # a leftover commune choice / stale-drop flag from the prior
        # attempt. HA reuses the same flow instance until the menu
        # step is re-entered, so this is the natural reset point.
        self._utility = None
        self._postcode = None
        self._candidates = ()
        self._reconfigure_commune = None
        self._reconfigure_commune_label = None
        self._reconfigure_commune_submitted = False
        self._drop_stale_reconfigure_commune = False
        self._household = None
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=["reconfigure_postcode", "reconfigure_manual"],
        )

    async def async_step_reconfigure_postcode(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Re-prompt for the postcode and re-run the utility resolver.

        Per-commune resolutions chain into ``reconfigure_commune`` so
        the user can confirm or re-pick the commune in the same flow
        (the commune dropdown is pre-filled with the current commune
        when the resolved utility matches the saved one). Split
        postcodes chain into ``reconfigure_choose`` instead.
        """
        if user_input is not None:
            postcode = user_input[CONF_POSTCODE].strip()
            self._postcode = postcode
            candidates = _resolve_candidates(postcode)
            if len(candidates) == 1:
                self._utility = candidates[0]
                if get(self._utility).supports_communes:
                    return await self.async_step_reconfigure_commune()
                return await self._async_finish_reconfigure()
            if len(candidates) > 1:
                self._candidates = candidates
                return await self.async_step_reconfigure_choose()
            return await self.async_step_reconfigure_manual()
        return self.async_show_form(step_id="reconfigure_postcode", data_schema=_USER_SCHEMA)

    async def async_step_reconfigure_choose(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Operator chooser for the reconfigure flow's postcode path."""
        if not self._candidates:
            return self.async_abort(reason="invalid_flow_state")
        if user_input is not None:
            self._utility = user_input[CONF_UTILITY]
            if get(self._utility).supports_communes:
                return await self.async_step_reconfigure_commune()
            return await self._async_finish_reconfigure()
        return self.async_show_form(
            step_id="reconfigure_choose", data_schema=_choose_schema(self._candidates)
        )

    async def async_step_reconfigure_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manual utility picker for the reconfigure flow.

        Per-commune operators (DWG / Farys / Pidpa / Water-link) chain
        into ``reconfigure_commune`` so the user can pick their commune
        in the same flow instead of needing a follow-up OptionsFlow.
        """
        if user_input is not None:
            self._utility = user_input[CONF_UTILITY]
            if get(self._utility).supports_communes:
                return await self.async_step_reconfigure_commune()
            return await self._async_finish_reconfigure()
        return self.async_show_form(step_id="reconfigure_manual", data_schema=_manual_schema())

    async def async_step_reconfigure_commune(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Commune picker shown after the manual or postcode pick.

        Pre-fills the dropdown with the saved commune when the resolved
        utility matches the entry's current utility, so the user can
        submit as-is to keep their commune. A postcode the operator bills
        on a commune of its own pre-fills that commune instead when the
        postcode has changed, or when nothing is saved to pre-fill.

        Skips itself when the commune list cannot be fetched (transient
        network / parser failure); the entry then loads on the
        operator-wide default and the user can pick a commune later via
        OptionsFlow.
        """
        if self._utility is None:
            return self.async_abort(reason="invalid_flow_state")
        communes = await self._async_communes_cached(self._utility)
        if not communes:
            return await self._async_finish_reconfigure()
        if user_input is not None:
            chosen = user_input.get(CONF_COMMUNE)
            # Treat empty-string commune as "no selection" (defensive
            # against UI / API paths that surface an unset SelectSelector
            # default as ""); without this we'd persist "" into the
            # entry options and later crash fetch_for_commune.
            if chosen == "":
                chosen = None
            # Record that this step was rendered and submitted, so a
            # cleared selection is read as "drop the commune" rather
            # than falling through to whatever was saved before. The
            # step's own text offers exactly that choice.
            self._reconfigure_commune_submitted = True
            if chosen is not None:
                self._reconfigure_commune = chosen
                for option in communes:
                    if option.id == chosen:
                        self._reconfigure_commune_label = option.label
                        break
            return await self._async_finish_reconfigure()
        entry = self._entry_under_reconfigure()
        if entry is None:
            return self.async_abort(reason="entry_removed")
        live_ids = {c.id for c in communes}
        saved = entry.options.get(CONF_COMMUNE)
        # Only suggest the saved commune when it is still in the live
        # list AND the resolved utility is unchanged. If a stored
        # commune has been filtered out (phantom blocklist addition,
        # operator renumber, etc.) we must NOT suggest it back -- a
        # user submitting the form unchanged would otherwise propagate
        # the stale id forward.
        suggested = (
            saved if entry.data.get(CONF_UTILITY) == self._utility and saved in live_ids else None
        )
        # The commune the operator bills the postcode on, as the config and
        # options flows suggest it. It wins over the saved commune when the
        # postcode has changed: that commune belongs to the old address, and
        # once submitted setup never revisits it. Moving from Geel to Nijlen
        # kept Pidpa's Geel card, 27.06 EUR a year too much.
        saved_postcode = entry.options.get(CONF_POSTCODE) or entry.data.get(CONF_POSTCODE)
        billed = _commune_for_postcode(self._utility, self._postcode or saved_postcode)
        moved = self._postcode is not None and self._postcode != saved_postcode
        if billed in live_ids and (moved or suggested is None):
            suggested = billed
        if saved is not None and saved not in live_ids:
            # The form will load with no selection; explicitly tell
            # _async_finish_reconfigure to drop the stale commune even
            # if the user submits the form unchanged.
            self._drop_stale_reconfigure_commune = True
        commune_field = (
            vol.Optional(CONF_COMMUNE, description={"suggested_value": suggested})
            if suggested
            else vol.Optional(CONF_COMMUNE)
        )
        schema = vol.Schema(
            {
                commune_field: SelectSelector(
                    SelectSelectorConfig(
                        options=[SelectOptionDict(value=c.id, label=c.label) for c in communes],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="reconfigure_commune", data_schema=schema)

    async def async_step_reconfigure_household(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the Flemish household settings on a move into Flanders.

        The Flemish tariff prices on the number of registered residents
        and the social tariff, which an entry moving in from Brussels or
        Wallonia has never been asked for. Left unasked, the projection
        priced on a household of one with nothing saying so.
        """
        if user_input is not None:
            self._household = {
                CONF_PERSONS: int(user_input[CONF_PERSONS]),
                CONF_SOCIAL_TARIFF: bool(user_input[CONF_SOCIAL_TARIFF]),
            }
            return await self._async_finish_reconfigure()
        schema = vol.Schema(
            {
                vol.Required(CONF_PERSONS, default=DEFAULT_PERSONS): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_PERSONS, max=MAX_PERSONS, step=1, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_SOCIAL_TARIFF, default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="reconfigure_household", data_schema=schema)

    def _entry_under_reconfigure(self) -> ConfigEntry | None:
        """The entry this flow reconfigures, or None once it has been removed.

        The dialog outlives a removal of the entry, and the next submit
        then raised UnknownEntry out of the flow instead of ending it.
        """
        try:
            return self._get_reconfigure_entry()
        except UnknownEntry:
            return None

    async def _async_finish_reconfigure(self) -> ConfigFlowResult:
        """Apply the reconfigure to the existing entry and reload it.

        When the resolved utility differs from the saved one, drop the
        commune-tied options: ``CONF_COMMUNE`` and ``CONF_COMMUNE_LABEL``
        carry an opaque, operator-specific identifier (DWG GUID, Farys
        numeric, Pidpa slug, Water-link name) that means nothing to a
        different operator. The other options (consumption, persons,
        social tariff, meter) carry over. If the user picked a commune
        in the manual flow (``async_step_reconfigure_commune``), layer
        it on top.
        """
        if self._utility is None:
            return self.async_abort(reason="invalid_flow_state")
        entry = self._entry_under_reconfigure()
        if entry is None:
            return self.async_abort(reason="entry_removed")
        new_utility = self._utility
        old_utility = entry.data[CONF_UTILITY]

        new_unique_id = f"{DOMAIN}_{new_utility}"
        existing = await self.async_set_unique_id(new_unique_id)
        if existing is not None and existing.entry_id != entry.entry_id:
            return self.async_abort(reason="already_configured")
        # After the check above: a household form is not asked of a
        # move that is about to be refused.
        if (
            _is_flanders(new_utility)
            and not _is_flanders(old_utility)
            and CONF_PERSONS not in entry.options
            and self._household is None
        ):
            return await self.async_step_reconfigure_household()

        new_options = dict(entry.options)
        if new_utility != old_utility or self._drop_stale_reconfigure_commune:
            new_options.pop(CONF_COMMUNE, None)
            new_options.pop(CONF_COMMUNE_LABEL, None)
        if (
            new_utility == old_utility
            and self._drop_stale_reconfigure_commune
            and self._reconfigure_commune is None
        ):
            # Said here, where the drop happens: said when the form was
            # rendered, opening and cancelling the dialog logged a drop
            # that never took place.
            _warn_stale_commune(new_utility)
        if new_utility != old_utility and not _is_flanders(new_utility):
            # ``social_tariff`` and ``gedomicilieerd_persons`` only enter
            # the Flanders pricing branch. The OptionsFlow hides both for
            # Brussels / Wallonia entries, so a stale value would linger
            # unseen: the user would believe the discount is honoured
            # while pricing.py drops it, and an old household size would
            # come back as the default on a later move to a Flemish
            # operator. Strip both, as the reconfigure text promises.
            new_options.pop(CONF_SOCIAL_TARIFF, None)
            new_options.pop(CONF_PERSONS, None)
        if self._household is not None:
            new_options.update(self._household)
        if self._reconfigure_commune is not None:
            new_options[CONF_COMMUNE] = self._reconfigure_commune
            if self._reconfigure_commune_label is not None:
                new_options[CONF_COMMUNE_LABEL] = self._reconfigure_commune_label
        elif self._reconfigure_commune_submitted:
            # The step was shown and came back with nothing selected.
            # Keeping the old commune would contradict the form, and on
            # a utility whose commune list has moved on it would keep
            # feeding a value the operator no longer knows.
            new_options.pop(CONF_COMMUNE, None)
            new_options.pop(CONF_COMMUNE_LABEL, None)
        if self._postcode is not None:
            new_options[CONF_POSTCODE] = self._postcode

        if new_utility == old_utility and new_options == dict(entry.options):
            # No-op rewrite (postcode resolved to the same utility we
            # already have, no commune change). Reload the entry anyway
            # so the user sees a fresh fetch on the next sensor tick.
            return self.async_update_reload_and_abort(entry)

        # A branch that changes something leaves the reload to the update
        # listener __init__ registers. Asking for one here as well ran
        # async_setup_entry twice over, each time re-fetching the tariff
        # live, on top of the one the backfill gate already costs. An
        # entry whose setup failed has no listener, so it is reloaded
        # here: written and left alone, it kept its failed state with
        # the new data, while the text said "updated and reloaded". An
        # entry that was never loaded is left as it is.
        update = (
            self.async_update_reload_and_abort
            if entry.state in (ConfigEntryState.SETUP_ERROR, ConfigEntryState.SETUP_RETRY)
            else self.async_update_and_abort
        )
        if new_utility == old_utility:
            # Same utility but commune changed via the manual flow.
            return update(entry, options=new_options)

        return update(
            entry,
            unique_id=new_unique_id,
            title=get(new_utility).label,
            data_updates={CONF_UTILITY: new_utility},
            options=new_options,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BeWaterPricesOptionsFlow()


class BeWaterPricesOptionsFlow(OptionsFlow):
    # ``config_entry`` is a read-only property exposed by HA's OptionsFlow base
    # class; assigning to it from __init__ raises in modern HA. Inherit the
    # default no-arg constructor and use ``self.config_entry`` directly.

    def __init__(self) -> None:
        # Cache the live commune list across form-render / form-submit
        # within one options flow. Same rationale as the ConfigFlow's
        # cache: HA calls async_step_init twice per user click-through
        # and a transient second-call failure silently drops the user's
        # selection.
        self._communes_cache: dict[str, tuple[CommuneOption, ...]] = {}

    async def _async_communes_cached(self, utility_id: str) -> tuple[CommuneOption, ...]:
        # Cache by key presence -- including an empty / failed result --
        # so the form-render and form-submit calls within one flow see the
        # same list. Caching only successes meant a render-time fetch
        # failure (empty -> no commune field) followed by a submit-time
        # success would treat the absent field as an explicit deselect and
        # wipe the saved commune.
        if utility_id in self._communes_cache:
            return self._communes_cache[utility_id]
        fresh = await _async_communes(self.hass, utility_id)
        self._communes_cache[utility_id] = fresh
        return fresh

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        # Warm the extractor registry off-loop before _is_flanders() /
        # get() run; importing the provider modules is blocking work HA
        # forbids on the loop.
        await async_load(self.hass)
        utility_id = self.config_entry.data[CONF_UTILITY]
        communes = await self._async_communes_cached(utility_id)
        if user_input is not None:
            final = dict(user_input)
            # Empty-string commune id -> treat as "no selection" before
            # label resolution so we don't persist "" and later crash
            # fetch_for_commune("").
            if final.get(CONF_COMMUNE) == "":
                final.pop(CONF_COMMUNE, None)
            chosen = final.get(CONF_COMMUNE)
            if chosen is not None:
                # Resolve the opaque commune id back to its display label so
                # downstream surfaces (publication_label, diagnostics) show
                # "Gent" rather than the bare "25071" or GUID.
                for option in communes:
                    if option.id == chosen:
                        final[CONF_COMMUNE_LABEL] = option.label
                        break
            elif not communes:
                # Could not fetch the commune list (transient network /
                # parser failure). The form did not render the commune
                # field, so user_input cannot carry it. Preserve the
                # previously-saved commune so a transient outage does
                # not silently wipe the user's selection back to the
                # operator-wide default.
                existing = self.config_entry.options
                if existing.get(CONF_COMMUNE):
                    final[CONF_COMMUNE] = existing[CONF_COMMUNE]
                if existing.get(CONF_COMMUNE_LABEL):
                    final[CONF_COMMUNE_LABEL] = existing[CONF_COMMUNE_LABEL]
            # CONF_POSTCODE is not surfaced in the options schema, so it
            # cannot ride in via user_input. Reattach the stored value;
            # otherwise every options save would wipe the postcode that
            # the initial and reconfigure flows persist.
            if CONF_POSTCODE not in final and self.config_entry.options.get(CONF_POSTCODE):
                final[CONF_POSTCODE] = self.config_entry.options[CONF_POSTCODE]
            saved = self.config_entry.options.get(CONF_COMMUNE)
            if communes and saved is not None and saved not in {c.id for c in communes}:
                # The saved commune could not be offered, so this save
                # drops it; said here rather than when the form rendered.
                _warn_stale_commune(utility_id)
            return self.async_create_entry(title="", data=final)
        current = dict(self.config_entry.options)
        saved_commune = current.get(CONF_COMMUNE)
        if communes and saved_commune is not None and saved_commune not in {c.id for c in communes}:
            # A saved commune no longer in the live list (phantom blocklist
            # addition, operator renumber) must not be prefilled as an
            # unselectable value -- submitting it unchanged would raise a
            # form error or silently drop. Strip it from the defaults so the
            # user re-picks, mirroring the reconfigure flow's stale drop.
            current.pop(CONF_COMMUNE, None)
            current.pop(CONF_COMMUNE_LABEL, None)
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(
                current,
                flanders=_is_flanders(utility_id),
                communes=communes,
                suggested_commune=_commune_for_postcode(utility_id, current.get(CONF_POSTCODE)),
            ),
        )
