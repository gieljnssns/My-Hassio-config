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

"""Per-utility extractor protocol and shared dataclasses.

Each utility module under ``providers/`` exposes a top-level
``EXTRACTOR: WaterExtractor`` whose ``fetch`` callable returns one
:class:`WaterTariff`. The coordinator combines that with the user's
configured consumption / household size to produce the projected annual
cost. No EUR values live in Python source -- everything in
:class:`WaterTariff` comes from a live fetch of the utility's own
publication.

All EUR figures stored in :class:`WaterTariff` are **ex-VAT**. Belgian
water is residentially taxed at 6 %; ``vat_rate`` carries the rate so
the cost engine can re-apply it once at the end. Utilities that publish
VAT-incl numbers (VIVAQUA does) divide by ``1 + vat_rate`` at parse
time.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Protocol
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    import aiohttp

# Resolved once, at import: the registry is built off the event loop, and
# the lookup reads the zone file.
_BELGIUM = ZoneInfo("Europe/Brussels")


def belgian_today() -> date:
    """Today's date in Belgium, whatever zone the process clock is in.

    The operators turn their cards over on the Belgian calendar, and the
    coordinator judges a card by Home Assistant's own date. date.today()
    follows the process clock instead, which Home Assistant never moves to
    its configured zone: in a container started without TZ it runs on UTC,
    so for the first hour of 1 January every extractor still asked for
    last year's card, and the coordinator found it stale on arrival.
    """
    return datetime.now(_BELGIUM).date()


@dataclass(frozen=True, kw_only=True)
class WaterTariff:
    """One year's worth of tariff data for one utility."""

    utility: str
    region: str  # see const.REGIONS
    valid_from: date
    valid_until: date | None
    publication_label: str
    source_url: str

    yearly_fixed_fee: float  # EUR/year, ex-VAT
    # Flanders applies a per-resident discount on the vastrecht (-10 EUR per
    # gedomicilieerde, max 5 persons). Other regions leave at 0.
    yearly_fixed_fee_per_resident_discount: float = 0.0

    # Volumetric components (EUR/m³, ex-VAT). Shape differs by region:
    #   Flanders : basis (block 1) + comfort (block 2)
    #   Brussels : linear single rate (basis = comfort = None)
    #   Wallonia : linear single rate via cvd_eur_per_m3 + national CVA + FSE;
    #              tier math (50 % CVD on the first 30 m³) lives in pricing
    basis_eur_per_m3: float | None = None
    comfort_eur_per_m3: float | None = None
    linear_eur_per_m3: float | None = None

    # Sewerage / wastewater (EUR/m³, ex-VAT). Names follow the regional
    # vocabulary; only the ones relevant to the utility's region are non-zero.
    sanering_bovengemeentelijk_eur_per_m3: float = 0.0  # Flanders, to Aquafin
    sanering_gemeentelijk_eur_per_m3: float = 0.0  # Flanders, to commune
    cvd_eur_per_m3: float = 0.0  # Wallonia, per-distributor
    cva_eur_per_m3: float = 0.0  # Wallonia, national (SPGE constant)
    fse_eur_per_m3: float = 0.0  # Wallonia, national (Fonds Social de l'Eau)

    vat_rate: float = 0.06


if TYPE_CHECKING:
    WaterTariffFetcher = Callable[[aiohttp.ClientSession], Awaitable[WaterTariff]]
    CommuneFetcher = Callable[[aiohttp.ClientSession, str], Awaitable[WaterTariff]]
    CommuneLister = Callable[[aiohttp.ClientSession], Awaitable[tuple["CommuneOption", ...]]]
    CommuneForPostcode = Callable[[str], str | None]


@dataclass(frozen=True, kw_only=True)
class CommuneOption:
    """One commune the user can pick for a per-commune utility."""

    id: str  # opaque utility-internal identifier (GUID, integer, name)
    label: str  # human-readable, typically "<postcode> - <commune>"


@dataclass(frozen=True, kw_only=True)
class WaterExtractor:
    """Registry entry for one utility.

    Per-commune utilities (where saneringsbijdragen vary commune-by-
    commune within the same operator -- De Watergroep, Farys,
    Water-link) set ``list_communes`` and ``fetch_for_commune``. The
    coordinator routes through ``fetch_for_commune`` when the user
    picks a commune in the OptionsFlow; ``fetch`` remains the default
    fallback (used for the "no commune configured" path and for the
    daily live_check).
    """

    id: str
    label: str
    region: str
    fetch: WaterTariffFetcher
    fetch_for_commune: CommuneFetcher | None = None
    list_communes: CommuneLister | None = None
    # Some postcodes inside a per-commune operator's area are not billed at
    # its default commune's rate. Water-link's card puts 2070 in the ring
    # group, not in Antwerpen, and a household that never opened the
    # dropdown was billed 66 EUR a year too little. Where an operator can
    # say which commune a postcode belongs to, the config flow pre-selects
    # it instead of leaving the default to stand in silence.
    commune_for_postcode: CommuneForPostcode | None = None

    @property
    def supports_communes(self) -> bool:
        return self.fetch_for_commune is not None and self.list_communes is not None


class WaterExtractorProtocol(Protocol):
    """Each utility module must expose a top-level ``EXTRACTOR`` of this shape."""

    EXTRACTOR: WaterExtractor


class ExtractorError(Exception):
    """Raised when a utility's source cannot be fetched or parsed."""


class TransientFetchError(ExtractorError):
    """A fetch failed for an infrastructure reason rather than a content one.

    Network timeouts, connection resets, and HTTP 5xx / 429 responses are
    upstream hiccups that usually clear on a retry; they do not mean the
    parser or the published page has changed. The live-check classifies
    these separately so a brief outage does not open a false GitHub issue
    (see ``scripts/live_check.py``). It subclasses :class:`ExtractorError`
    so existing ``except ExtractorError`` callers keep treating it as a
    fetch failure.
    """


def tariff_to_dict(tariff: WaterTariff) -> dict[str, Any]:
    """The tariff as JSON-ready values, its dates as ISO strings.

    What the card archive writes for a month and what its reader gets
    back, so the two cannot drift apart.
    """
    out: dict[str, Any] = dataclasses.asdict(tariff)
    out["valid_from"] = tariff.valid_from.isoformat()
    out["valid_until"] = None if tariff.valid_until is None else tariff.valid_until.isoformat()
    return out


def tariff_from_dict(data: Mapping[str, Any]) -> WaterTariff:
    """The inverse of :func:`tariff_to_dict`. Keys the dataclass has no
    field for are ignored, so a stored row can carry its own metadata
    beside the tariff."""
    names = {f.name for f in dataclasses.fields(WaterTariff)}
    values: dict[str, Any] = {k: v for k, v in data.items() if k in names}
    values["valid_from"] = date.fromisoformat(values["valid_from"])
    until = values.get("valid_until")
    values["valid_until"] = None if until is None else date.fromisoformat(until)
    return WaterTariff(**values)


def carry_prior_year_card(tariff: WaterTariff, target_year: int) -> WaterTariff:
    """Let last year's card stand in until 31 March of ``target_year``.

    Publishers run weeks late in January, and every extractor serves the
    prior card in that window rather than going blank. Served with its
    own 31 December it counted as stale from the first day of the year,
    so the Repair card stood for however long the utility took. The
    grace period ends on 31 March, after which staleness is real.
    """
    if tariff.valid_from.year >= target_year:
        return tariff
    return dataclasses.replace(tariff, valid_until=date(target_year, 3, 31))


def relabel_with_human_commune(
    tariff: WaterTariff, *, commune_id: str, commune_label: str | None
) -> WaterTariff:
    """Swap an opaque commune id for its human label in publication_label.

    Per-commune extractors embed the commune they were called with
    inside ``publication_label`` as ``"... (<commune>)"``. Farys uses
    a numeric id (``25071``) and De Watergroep a GUID; neither makes
    sense to a human reading the diagnostics dump or the sensor
    attribute. The OptionsFlow saves the chosen commune's display
    label as ``CONF_COMMUNE_LABEL`` so the coordinator can substitute
    it back in here without changing the extractor protocol.
    """
    if not commune_label or commune_label == commune_id:
        return tariff
    needle = f"({commune_id})"
    if needle not in tariff.publication_label:
        return tariff
    return dataclasses.replace(
        tariff,
        publication_label=tariff.publication_label.replace(needle, f"({commune_label})", 1),
    )
