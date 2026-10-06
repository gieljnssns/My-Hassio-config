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

"""Farys (TMVW) -- biggest remaining Flemish operator (~1.5 M, ~22 % of Flanders).

Farys's `farys.be/nl/watertarieven` page is JS-rendered: the static
HTML carries only a 290-option commune dropdown and no rates. Selecting
a commune fires a Drupal AJAX form POST to
`/nl/watertarieven?ajax_form=1`; the response is a JSON envelope
containing an `insert` command whose `data` field is HTML markup with
the full per-commune integrale waterprijs structure (drinkwater +
gemeentelijke + bovengemeentelijke saneringsbijdragen, with the
standard VMM 50/30/20 + 10/6/4 vastrecht/korting split).

The extractor calls that endpoint directly with the commune ID baked
in (Gent-centrum = 25071 by default) and parses the rates out of the
`insert` command's HTML payload. The `form_build_id` field is
optional; the endpoint accepts a POST without it.

Per-commune data is real and varies (Gent-centrum's drinkwater is
3.0058 EUR/m³ in 2026, other communes differ). Gent-centrum is the
default since Gent is Farys's namesake city and the largest commune
in its Oost-Vl. heartland; users override via the OptionsFlow
commune dropdown.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

import aiohttp
from bs4 import BeautifulSoup

from .._phantom_blocklists import (
    FARYS_UNSERVABLE_IDS as _UNSERVABLE_COMMUNE_IDS,
)
from .._phantom_blocklists import (
    FARYS_UNSERVABLE_LABELS as _UNSERVABLE_COMMUNE_LABELS,
)
from ..const import DEFAULT_VAT_RATE, REGION_FLANDERS
from ._flanders import build_flanders_tariff
from ._pdf import (
    USER_AGENT,
    _http_error,
    _read_text_capped,
    error_text,
    fetch_text,
    memoised_text,
    to_float,
)
from .base import (
    CommuneOption,
    ExtractorError,
    TransientFetchError,
    WaterExtractor,
    WaterTariff,
    belgian_today,
    carry_prior_year_card,
)

# Re-exported so ``async_migrate_entry`` and the test suite can read
# them under their existing names without knowing about the dep-free
# leaf module.
__all__ = ("EXTRACTOR", "_UNSERVABLE_COMMUNE_IDS", "_UNSERVABLE_COMMUNE_LABELS")

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "farys"
LABEL = "Farys"
ENDPOINT_URL = "https://www.farys.be/nl/watertarieven?ajax_form=1"
PAGE_URL = "https://www.farys.be/nl/watertarieven"
DEFAULT_MUNICIPALITY_ID = "25071"  # Gent-centrum
DEFAULT_MUNICIPALITY_LABEL = "Gent-centrum"

# The five communes whose card is not the one the Gent-centrum default
# carries, checked against all 266 commune pages on 2026-09-09: Drogenbos
# levies a gemeentelijke saneringsbijdrage of 1,4903 against the other
# 265 at 1,9572, and the four Zaventem cards net a gemeentelijke
# tussenkomst off the drinkwater leg, leaving 2,9251 against the other
# 262 at 3,0058. Left to the default, Drogenbos was over-charged 49.49
# EUR a year and the Zaventem communes 8.55. Nossegem shares postcode
# 1930 with Zaventem and is billed identically, so one entry covers both.
_POSTCODE_COMMUNES: dict[str, str] = {
    "1620": "25906",  # Drogenbos
    "1930": "25926",  # Zaventem (and Nossegem)
    "1932": "25931",  # Sint-Stevens-Woluwe
    "1933": "25936",  # Sterrebeek
    "1935": "25926",  # Zaventem, which Farys lists under 1930
}


def commune_for_postcode(postcode: str) -> str | None:
    """The commune id for a postcode Farys does not bill at the default rate."""
    return _POSTCODE_COMMUNES.get(postcode.strip())


_CURRENT_PAGE_NID = "20471"

# Match "Basistarief drinkwater (per m³) € N,NNNN" and the matching
# comforttarief / sanering rows. The HTML has the labels broken across
# inline tags but the text-collapsed version is stable.
# Each row prints the rate twice, ex-VAT then with 6 % VAT, and both are
# read: a row that lost its ex-VAT cell would otherwise hand the VAT
# figure over as the rate, six percent high and shaped like a price.
_PAIR = r"\s*€\s*([\d]+,\d{3,5})\s*€\s*([\d]+,\d{3,5})"
_BASIS_DRINKWATER_RE = re.compile(r"Basistarief\s+drinkwater\s*\(per\s*m³\)" + _PAIR, re.IGNORECASE)
_COMFORT_DRINKWATER_RE = re.compile(
    r"Comforttarief\s+drinkwater\s*\(per\s*m³\)" + _PAIR, re.IGNORECASE
)
# Spelled out to the closing "(per m³)" rather than bridged with a
# permissive gap. "[^€]+" only stops at the first euro sign, so a row
# whose ex-VAT cell is empty let the match run past the row boundary and
# return the comforttarief on the next line -- exactly twice the right
# number, and plausible enough to ship.
_BASIS_GEMEENTELIJK_RE = re.compile(
    r"Basistarief\s+gemeentelijke\s+bijdrage\s*\(per\s*m³\)" + _PAIR,
    re.IGNORECASE,
)
_BASIS_BOVENGEMEENTELIJK_RE = re.compile(
    r"Basistarief\s+bovengemeentelijke\s+bijdrage\s*\(per\s*m³\)" + _PAIR,
    re.IGNORECASE,
)
# Some communes pay part of the drinkwater leg for their residents, and
# Farys prints what they cover as a negative row directly under the leg
# it applies to. Only a handful of cards carry one, so both rows are
# optional; the sign is part of the value, which is why these do not use
# _PAIR. A Unicode minus would fail to match and read as no discount,
# which the integrale-waterprijs check two rows down then refuses rather
# than letting the gross rate through.
_SIGNED_PAIR = r"\s*€\s*(-?[\d]+,\d{3,5})\s*€\s*(-?[\d]+,\d{3,5})"
_TUSSENKOMST_BASIS_RE = re.compile(
    r"Gemeentelijke\s+tussenkomst\s+op\s+basistarief\s+drinkwater\s*\(per\s*m³\)" + _SIGNED_PAIR,
    re.IGNORECASE,
)
_TUSSENKOMST_COMFORT_RE = re.compile(
    r"Gemeentelijke\s+tussenkomst\s+op\s+comforttarief\s+drinkwater\s*\(per\s*m³\)" + _SIGNED_PAIR,
    re.IGNORECASE,
)


def _active_period_year(soup: BeautifulSoup) -> int | None:
    """The tariff year Farys marks as selected, if the switcher is present.

    The payload renders one button per published period and flags the
    one it is showing with ``<li class="active">``. Reading it means a
    page that starts serving next year's card early is dated by the page
    rather than by our clock -- which is also what lets the stale-snapshot
    check notice a page still stuck on last year.
    """
    active = soup.select_one("ul.js-period-rates li.active button[value]")
    if active is None:
        return None
    value = str(active.get("value", "")).strip()
    if value.isdigit() and len(value) == 4:
        return int(value)
    # The switcher is there and says something else: the clock takes
    # over, and a page that changed shape should not do so in silence,
    # since the clock cannot tell a card stuck on last year from a
    # current one.
    _LOGGER.warning("Farys marks its period as %r, not a year; dating the card by the clock", value)
    return None


def _extract_html_payload(ajax_response_text: str) -> str:
    """Pull the `insert`-command `data` field out of a Drupal AJAX response."""
    try:
        commands = json.loads(ajax_response_text)
    except json.JSONDecodeError as err:
        raise ExtractorError(f"Farys AJAX response is not JSON: {err}") from err
    # A Drupal AJAX response is a list of command dicts. A well-formed
    # JSON value that is not that shape (an error envelope, a bare string
    # or number) would otherwise raise a raw AttributeError / TypeError;
    # report it as a parse failure instead.
    if not isinstance(commands, list):
        raise ExtractorError("Farys AJAX response was not a command list")
    for cmd in commands:
        if isinstance(cmd, dict) and cmd.get("command") == "insert":
            data = cmd.get("data")
            if isinstance(data, str) and "Basistarief" in data:
                return data
    raise ExtractorError("Farys AJAX response has no insert command with tariff data")


# Farys prints the three legs added up, two rows below them. Checking
# against it is the one guard that cannot go stale: the VMM 2x rule holds
# just as well when a leg has been read from the wrong row, and a
# Flanders-wide constant would need re-pinning every January.
_INTEGRALE_BASIS_RE = re.compile(
    r"Integrale\s+waterprijs\s+basistarief\s*\(per\s*m³\)\s*€\s*([\d.,]+)\s*€\s*([\d.,]+)",
    re.IGNORECASE,
)


def _amount(text: str, pattern: re.Pattern[str], label: str) -> float:
    match = pattern.search(text)
    if match is None:
        raise ExtractorError(f"Farys: could not find {label} in the AJAX HTML payload")
    rate, with_vat = to_float(match.group(1)), to_float(match.group(2))
    if abs(rate * (1.0 + DEFAULT_VAT_RATE) - with_vat) > 0.001:
        raise ExtractorError(
            f"Farys: {label} {rate} and its VAT-inclusive figure {with_vat} do not agree"
        )
    return rate


def _optional_amount(text: str, pattern: re.Pattern[str], label: str) -> float:
    """Read a row most cards do not print, as zero when it is absent.

    Absent means the commune grants nothing, which is the common case. A
    row that is there but malformed still goes through :func:`_amount`
    and is refused, so this only widens what parses, never what passes.
    """
    if pattern.search(text) is None:
        return 0.0
    return _amount(text, pattern, label)


def parse_tariff(
    ajax_response_text: str,
    *,
    year: int | None = None,
    municipality_label: str = DEFAULT_MUNICIPALITY_LABEL,
) -> WaterTariff:
    """Parse a captured Farys AJAX response (JSON envelope of HTML)."""
    html_payload = _extract_html_payload(ajax_response_text)
    soup = BeautifulSoup(html_payload, "html.parser")
    text = soup.get_text(" ", strip=True)

    basis = _amount(text, _BASIS_DRINKWATER_RE, "drinkwater basistarief")
    comfort = _amount(text, _COMFORT_DRINKWATER_RE, "drinkwater comforttarief")
    # What the commune covers comes off the leg it names, before the two
    # checks below. Zaventem prints 3,0058 for the drinkwater basistarief
    # and -0,0807 of gemeentelijke tussenkomst under it, and the integrale
    # waterprijs it prints two rows further down is 6,5842, not the 6,6649
    # the gross rows add up to. The rows are already negative, so they are
    # added rather than subtracted.
    basis += _optional_amount(text, _TUSSENKOMST_BASIS_RE, "tussenkomst basistarief")
    comfort += _optional_amount(text, _TUSSENKOMST_COMFORT_RE, "tussenkomst comforttarief")
    if abs(comfort - 2.0 * basis) > 0.01:
        raise ExtractorError(
            f"Farys comforttarief {comfort} is not 2× basistarief {basis} (VMM 2× rule)"
        )
    sanering_gem = _amount(text, _BASIS_GEMEENTELIJK_RE, "gemeentelijke saneringsbijdrage")
    sanering_bov = _amount(
        text, _BASIS_BOVENGEMEENTELIJK_RE, "bovengemeentelijke saneringsbijdrage"
    )

    integrale = _amount(text, _INTEGRALE_BASIS_RE, "integrale waterprijs basistarief")
    if abs(basis + sanering_gem + sanering_bov - integrale) > 0.0001:
        raise ExtractorError(
            f"Farys rows {basis} + {sanering_gem} + {sanering_bov} do not add up to "
            f"the integrale waterprijs {integrale} the page prints"
        )

    active = _active_period_year(soup)
    clock = belgian_today().year
    if year is None and active is not None and active > clock:
        # The page dates the card, so a card served early is applied as
        # published. Nothing downstream checks valid_from, so say so: the
        # alternative, refusing it, would blank every entity after a
        # restart in that window, since the cached snapshot is in memory.
        _LOGGER.warning(
            "Farys is serving its %d card while the calendar says %d; pricing on it",
            active,
            clock,
        )
    target = year or active or clock
    tariff = build_flanders_tariff(
        utility_id=UTILITY_ID,
        year=target,
        publication_label=f"Farys watertarieven {target} ({municipality_label})",
        source_url=PAGE_URL,
        basis=basis,
        comfort=comfort,
        sanering_gemeentelijk=sanering_gem,
        sanering_bovengemeentelijk=sanering_bov,
    )
    return carry_prior_year_card(tariff, year or clock)


async def _post_for_commune(session: aiohttp.ClientSession, commune_id: str) -> str:
    payload = {
        "switcher": "WaterRateInformation",
        "municipality": commune_id,
        "current_page_nid": _CURRENT_PAGE_NID,
        "form_id": "farys_municipalities_switcher_form",
        "_triggering_element_name": "municipality",
    }

    async def read() -> str:
        try:
            async with session.post(
                ENDPOINT_URL,
                data=payload,
                headers={
                    "User-Agent": USER_AGENT,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                },
                timeout=aiohttp.ClientTimeout(total=30),
                allow_redirects=False,
            ) as resp:
                if not 200 <= resp.status < 300:
                    raise _http_error(ENDPOINT_URL, resp.status)
                return await _read_text_capped(resp, ENDPOINT_URL)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise TransientFetchError(
                f"network error fetching Farys AJAX endpoint: {error_text(err)}"
            ) from err

    # The commune is a form field, not part of the URL, so the memo key
    # carries it.
    return await memoised_text(f"{ENDPOINT_URL}#municipality={commune_id}", read)


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    text = await _post_for_commune(session, DEFAULT_MUNICIPALITY_ID)
    return await asyncio.to_thread(parse_tariff, text)


async def fetch_for_commune(session: aiohttp.ClientSession, commune: str) -> WaterTariff:
    text = await _post_for_commune(session, commune)
    return await asyncio.to_thread(parse_tariff, text, municipality_label=commune)


# Each <option> is "<postcode> - <commune> (<gemeente>)" with value =
# numeric ID. We store the numeric ID as the option's id and the full
# label as its display string.
# The gap between the tag and the label is not padded with \\s* on
# either side: three ways to split the same run of whitespace makes
# the engine enumerate every split when the match fails, which is
# cubic in the length of that run. .strip() below does the same job
# in linear time.
_OPTION_RE = re.compile(
    r'<option[^>]*value="(\d+)"[^>]*>([^<]*)</option>',
    re.IGNORECASE | re.DOTALL,
)


# Phantom entries in Farys's dropdown -- the AJAX endpoint returns a
# response without an "insert" command for these, so picking them
# crashes with "no insert command with tariff data". These are split
# postcodes where DWG is the actual operator for that street/parish;
# the entry is left in Farys's UI but the back-end has no data.
# Drop them from list_communes so users can't pick them; the resolver
# falls back to Farys for the postcode (the dominant operator on the
# Farys-served half), and users in the DWG half manual-override on
# reconfigure. The data lives in ``_phantom_blocklists`` (imported at
# the top of this module) so the maintenance script can read it
# without pulling the providers package in.


def _parse_commune_options(html: str) -> list[CommuneOption]:
    communes: list[CommuneOption] = []
    seen: set[str] = set()
    for match in _OPTION_RE.finditer(html):
        commune_id = match.group(1)
        label = match.group(2).strip()
        if not label or commune_id in seen or label in _UNSERVABLE_COMMUNE_LABELS:
            continue
        seen.add(commune_id)
        communes.append(CommuneOption(id=commune_id, label=label))
    return communes


async def list_communes(session: aiohttp.ClientSession) -> tuple[CommuneOption, ...]:
    """Discover all 290+ Farys communes by scraping the watertarieven dropdown.

    Drops the 23 phantom entries Farys's UI lists without backing tariff
    data (see ``_UNSERVABLE_COMMUNE_LABELS``).
    """
    html = await fetch_text(session, PAGE_URL)
    # Scanning 290 options over a 67 KB page is milliseconds, but this
    # runs from the config flow on Home Assistant's event loop and the
    # module's own fetch_and_parse hands every other parse to a thread
    # for exactly that reason. Keep the discipline.
    communes = await asyncio.to_thread(_parse_commune_options, html)
    if not communes:
        raise ExtractorError("could not discover any Farys communes from the watertarieven page")
    return tuple(communes)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_FLANDERS,
    fetch=fetch,
    fetch_for_commune=fetch_for_commune,
    list_communes=list_communes,
    commune_for_postcode=commune_for_postcode,
)
