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

"""De Watergroep -- 167 communes / ~3.3 M customers (~49.5 % of Flanders).

Two ingestion paths share the same cookie-driven endpoint:

  - **Default fetch** (no commune configured) hits the cookie-driven
    ``/Tarief/UpdateDetailTariefJaar/<year>`` endpoint with the Halle
    GUID and labels the snapshot ``"Halle (DWG-served default)"``.
    That gives the full integrale waterprijs (drinkwater +
    gemeentelijke + bovengemeentelijke saneringsbijdragen) for one
    representative DWG-served commune. There is nothing under it: the
    news article ``over-de-watergroep/nieuws/tarieven-<year>`` used to
    be the fallback and carries the drinkwater leg alone, which bills
    355.32 EUR a year where the Halle card bills 782.73.

  - **Per-commune fetch** GETs the same endpoint with the user-picked
    ``dwg_l=<GUID>`` cookie and returns the integrale waterprijs for
    that commune, with the standard VMM 50/30/20 + 10/6/4
    vastrecht/korting structure.

Commune list discovery: scrape the dropdown on
``/nl-be/drinkwater/tarieven`` (700+ ``<option>`` entries with GUID
values).

Comforttarief is exactly ``2 ×`` the basistarief by VMM mandate; we
materialise it.
"""

from __future__ import annotations

import asyncio
import logging
import re

import aiohttp
from bs4 import BeautifulSoup

from ..const import REGION_FLANDERS
from ._flanders import build_flanders_tariff
from ._html import fetch_html
from ._pdf import USER_AGENT, _http_error, _read_text_capped, error_text, memoised_text, to_float
from .base import (
    CommuneOption,
    ExtractorError,
    TransientFetchError,
    WaterExtractor,
    WaterTariff,
    belgian_today,
    carry_prior_year_card,
)

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "de_watergroep"
LABEL = "De Watergroep"


class UnshowableLeg(ExtractorError):
    """The page prints a sentence where a saneringsbijdrage should be.

    Its own failure type because it is the one failure the per-commune
    fetch can answer with the operator default: the page is there and
    current, it just will not show one commune's number today.
    """


COMMUNE_LIST_URL = "https://www.dewatergroep.be/nl-be/drinkwater/tarieven"
COMMUNE_DETAIL_URL_FMT = "https://www.dewatergroep.be/Tarief/UpdateDetailTariefJaar/{year}"

# Default commune for the no-commune fallback. Halle (postcode 1500) is
# a representative DWG-served commune in Vlaams-Brabant, and the
# cookie-driven endpoint returns the full integrale waterprijs there
# (drinkwater + gemeentelijke + bovengemeentelijke). Saneringsbijdragen
# in Flanders vary by commune, so it still under- or over-estimates for
# a household that never picks its own: measured across all 699 commune
# pages the mean error is 0.43 EUR a year and the worst real case 58.65
# (Overijse, gemeentelijke 1,4039).
_DEFAULT_COMMUNE_GUID = "{B16A143A-49E6-4CE5-A241-1AA09BFC406A}"
_DEFAULT_COMMUNE_LABEL = "Halle (DWG-served default)"

_DRINKWATER_RE = re.compile(
    r"Waterverbruik\s+drinkwater\s*€\s*([\d]+,\d{3,5})",
    re.IGNORECASE,
)
_AFVOER_RE = re.compile(
    r"Afvoer\s+van\s+afvalwater\s*€\s*([\d]+,\d{3,5})",
    re.IGNORECASE,
)
_ZUIVERING_RE = re.compile(
    r"Zuivering\s+van\s+afvalwater\s*€\s*([\d]+,\d{3,5})",
    re.IGNORECASE,
)

# What De Watergroep prints in place of an amount it cannot render. It is
# a statement that the number is unavailable, not that the leg is free,
# and reading it as 0.00 EUR/m3 under-states a bill by the whole leg:
# 3660 Opglabbeek billed 575.26 EUR a year instead of 782.73 on
# 2026-09-08. The two cases have to be told apart, so the sentence is
# matched next to the label it replaced.
# Matched word by word rather than as one literal: the page wraps the
# sentence where the column happens to end, and get_text keeps a
# string's own newlines, so a literal with hard single spaces stopped
# matching the moment the layout moved.
_UNAVAILABLE = r"\s+".join(("de", "kostprijs", "kan", "momenteel", "niet", "getoond", "worden"))
_AFVOER_UNAVAILABLE_RE = re.compile(rf"Afvoer\s+van\s+afvalwater\s*{_UNAVAILABLE}", re.IGNORECASE)
_ZUIVERING_UNAVAILABLE_RE = re.compile(
    rf"Zuivering\s+van\s+afvalwater\s*{_UNAVAILABLE}", re.IGNORECASE
)


def _basis_per_m3_block(text: str) -> str | None:
    """Return the slice of ``text`` belonging to the Basistarief per m³ table.

    Bounded on the right by the next section marker (Basistarief per
    liter, Comforttarief, ...) so the row regexes can't reach into the
    Comforttarief block and silently match its Afvoer / Zuivering rows
    when the Basistarief block has an empty row.

    If the anchor appears more than once on the page (e.g. DWG ever
    inlines an explainer / comparison heading above the live table),
    the first occurrence whose slice contains the data row
    "Waterverbruik drinkwater" wins. A pure-heading first hit no
    longer truncates the parser to navigation text.
    """
    pos = 0
    while True:
        start = text.find("Basistarief per m³", pos)
        if start < 0:
            return None
        next_markers = (
            text.find("Basistarief per liter", start + 1),
            text.find("Comforttarief", start + 1),
        )
        end = min((m for m in next_markers if m > 0), default=len(text))
        block = text[start:end]
        if "Waterverbruik drinkwater" in block:
            return block
        pos = start + 1


def parse_commune_tariff(
    html: str,
    *,
    year: int,
    commune_label: str,
) -> WaterTariff:
    """Parse the per-commune AJAX response (full integrale waterprijs).

    A leg can be missing for two reasons and they are not the same. When
    De Watergroep cannot render the amount it says so in words, and
    reading that as 0.00 EUR/m3 drops the whole leg from the bill: on
    2026-09-08 that billed 3660 Opglabbeek 575.26 EUR a year against
    782.73. That case raises, so the coordinator keeps the last good
    snapshot and the stale-snapshot Repair goes up.

    A bare label with no amount and no such sentence still counts as a
    commune that levies nothing. Sinaai used to be cited here as the
    example of one, wrongly: it publishes EUR 1,9114 today, and the
    committed fixture had merely caught the page in the same state. There
    is no confirmed example either way, so the reading is left as it was
    rather than swapped for a guess.

    Drinkwater stays required: without it there is no tariff at all.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    block = _basis_per_m3_block(text)
    if block is None:
        raise ExtractorError("could not locate De Watergroep 'Basistarief per m³' section")

    drinkwater = _DRINKWATER_RE.search(block)
    if drinkwater is None:
        raise ExtractorError("could not parse De Watergroep per-commune drinkwater basistarief")
    basis = to_float(drinkwater.group(1))
    for pattern, leg in (
        (_AFVOER_UNAVAILABLE_RE, "gemeentelijke"),
        (_ZUIVERING_UNAVAILABLE_RE, "bovengemeentelijke"),
    ):
        if pattern.search(block) is not None:
            raise UnshowableLeg(
                f"De Watergroep says the {leg} saneringsbijdrage cannot be shown "
                f"for this commune; refusing to bill it as 0.00 EUR/m3"
            )
    # A row that is not there is not a leg that is not levied. All 699
    # communes print both, 698 of them as an amount and Opglabbeek as the
    # sentence above, so there is no commune a zero would be right for and
    # every way of missing the row is a parser problem. Read as 0.00 it
    # cost 207.47 EUR a year on an 80 m3 bill, which is what the check on
    # the sentence alone was left to catch.
    legs: dict[str, float] = {}
    for pattern, leg, label in (
        (_AFVOER_RE, "gemeentelijke", "Afvoer van afvalwater"),
        (_ZUIVERING_RE, "bovengemeentelijke", "Zuivering van afvalwater"),
    ):
        match = pattern.search(block)
        if match is None:
            raise ExtractorError(
                f"De Watergroep printed no {leg} saneringsbijdrage for this commune "
                f"(no {label!r} row); refusing to bill it as 0.00 EUR/m3"
            )
        legs[leg] = to_float(match.group(1))
    san_gem = legs["gemeentelijke"]
    san_bov = legs["bovengemeentelijke"]

    return build_flanders_tariff(
        utility_id=UTILITY_ID,
        year=year,
        publication_label=f"De Watergroep tarieven {year} ({commune_label})",
        source_url=COMMUNE_DETAIL_URL_FMT.format(year=year),
        basis=basis,
        comfort=2.0 * basis,  # VMM-mandated 2× rule
        sanering_gemeentelijk=san_gem,
        sanering_bovengemeentelijk=san_bov,
    )


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    """No-commune fetch: the full integrale waterprijs for a default commune.

    Hits the cookie-driven per-commune endpoint with a known DWG-served
    commune (Halle, postcode 1500), which is the only source that carries
    all three legs.

    There is no fallback under it. The news article was one, and it
    carries the drinkwater leg alone: where the Halle card bills 782.73
    EUR a year at 80 m3, the article's card bills 355.32, and nothing on
    the entry says which of the two is on screen. A card that is 55 %
    short is worse than no card, because the coordinator keeps serving
    the last good snapshot and raises the stale-snapshot Repair when a
    fetch fails, and the daily live check opens an issue. Both of those
    are how a De Watergroep outage should look.
    """
    return await _newest_commune_card(session, _DEFAULT_COMMUNE_GUID, _DEFAULT_COMMUNE_LABEL)


# The year switcher in the answer marks the tab it served, whichever year
# the URL asked for.
_SERVED_YEAR_RE = re.compile(
    r'UpdateDetailTariefJaar/(20\d\d)/hh-tarieven"\s+class="active"\s+'
    r'title="Huishoudelijke tarieven (20\d\d)"'
)


def _served_year(text: str, asked: int) -> int:
    """The year the answer's active tab names, else the year asked for.

    Asked for a year it has not published, the endpoint can answer with
    the newest card it has, and stamping that with the year in the URL
    served last year's card as this year's, never stale.
    """
    match = _SERVED_YEAR_RE.search(text)
    if match is None or match.group(1) != match.group(2):
        return asked
    return int(match.group(1))


async def _fetch_commune_ajax(
    session: aiohttp.ClientSession, commune: str, year: int | None = None
) -> tuple[str, int]:
    """GET the UpdateDetailTariefJaar AJAX response for ``commune``.

    Returns the response body and the year it carries: the one its
    active tab names, or failing that the one the URL asked for. Raised
    errors are :class:`ExtractorError`; the caller decides what to
    label the parsed tariff with.
    """
    target = year or belgian_today().year
    url = COMMUNE_DETAIL_URL_FMT.format(year=target)

    async def read() -> str:
        try:
            async with session.get(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Cookie": f"dwg_l={commune}",
                    "X-Requested-With": "XMLHttpRequest",
                },
                timeout=aiohttp.ClientTimeout(total=30),
                # The commune cookie must not travel to wherever a redirect
                # points; a moved endpoint is a failure to look at.
                allow_redirects=False,
            ) as resp:
                if not 200 <= resp.status < 300:
                    raise _http_error(url, resp.status)
                return await _read_text_capped(resp, url)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise TransientFetchError(
                f"network error fetching De Watergroep AJAX endpoint: {error_text(err)}"
            ) from err
        finally:
            # The session is shared, and aiohttp merges its jar into the Cookie
            # header it sends. A dwg_l the endpoint set on an earlier request
            # would then travel with the next one and could answer for a
            # commune nobody asked about, with nothing in the answer to reveal
            # it: the commune is not named anywhere in the body. Drop it again
            # so each request carries only the one it was given.
            session.cookie_jar.clear(lambda cookie: cookie.key == "dwg_l")

    # The commune is not in the URL, so the memo key carries it.
    text = await memoised_text(f"{url}#dwg_l={commune}", read)
    if not text.strip() or "Basistarief" not in text:
        raise ExtractorError(
            f"De Watergroep returned an empty body for commune {commune!r} "
            "(probably an invalid GUID)"
        )
    return text, _served_year(text, target)


async def _commune_card(
    session: aiohttp.ClientSession, commune: str, label: str, target: int, year: int | None = None
) -> WaterTariff:
    text, served = await _fetch_commune_ajax(session, commune, year)
    tariff = await asyncio.to_thread(parse_commune_tariff, text, year=served, commune_label=label)
    return carry_prior_year_card(tariff, target)


async def _newest_commune_card(
    session: aiohttp.ClientSession, commune: str, label: str
) -> WaterTariff:
    """This year's card for ``commune``, or last year's until 31 March.

    In January the endpoint for the new year can fail outright until the
    card is published; last year's endpoint still answers, and its card
    stands in like every other utility's prior-year fallback.
    """
    target = belgian_today().year
    try:
        return await _commune_card(session, commune, label, target)
    except TransientFetchError:
        raise
    except ExtractorError as err:
        _LOGGER.info("De Watergroep %d card unavailable (%s); trying %d", target, err, target - 1)
        return await _commune_card(session, commune, label, target, year=target - 1)


async def fetch_for_commune(session: aiohttp.ClientSession, commune: str) -> WaterTariff:
    """Per-commune fetch via the cookie-driven UpdateDetailTariefJaar endpoint.

    A commune whose page cannot show one of its saneringsbijdragen is
    served the operator-wide default card instead of nothing at all.
    3660 Opglabbeek has printed "De kostprijs kan momenteel niet getoond
    worden" for months, and refusing outright left that household unable
    to finish setup with no way of knowing that leaving the commune blank
    is what works. The default is a real, current De Watergroep card and
    across all 699 communes it is 0.43 EUR a year out on average; for
    Opglabbeek in particular it is the figure the bill was calculated at.

    The label says which commune the card is really for, so the swap is
    visible on the entity and in diagnostics rather than silent, and only
    this one failure is caught: anything else is still a failure.
    """
    try:
        return await _newest_commune_card(session, commune, commune)
    except UnshowableLeg as err:
        if commune == _DEFAULT_COMMUNE_GUID:
            raise
        _LOGGER.warning(
            "%s; serving the %s card instead, which is about 0.43 EUR a year out "
            "across De Watergroep's communes. Pick another commune in the options "
            "if that is not close enough",
            err,
            _DEFAULT_COMMUNE_LABEL,
        )
    return await _newest_commune_card(session, _DEFAULT_COMMUNE_GUID, _DEFAULT_COMMUNE_LABEL)


# The gap between the tag and the label is not padded with \\s* on
# either side: three ways to split the same run of whitespace makes
# the engine enumerate every split when the match fails, which is
# cubic in the length of that run. .strip() below does the same job
# in linear time.
_OPTION_RE = re.compile(
    r'<option[^>]*value="(\{[0-9A-Fa-f-]+\})"[^>]*>([^<]*)</option>',
    re.IGNORECASE | re.DOTALL,
)


def _parse_commune_options(html: str) -> list[CommuneOption]:
    communes: list[CommuneOption] = []
    seen: set[str] = set()
    for match in _OPTION_RE.finditer(html):
        guid = match.group(1)
        label = match.group(2).strip()
        if not label or guid in seen:
            continue
        seen.add(guid)
        communes.append(CommuneOption(id=guid, label=label))
    return communes


async def list_communes(session: aiohttp.ClientSession) -> tuple[CommuneOption, ...]:
    """Discover the 700 De Watergroep communes by scraping the dropdown."""
    html = await fetch_html(session, COMMUNE_LIST_URL)
    # Same reasoning as farys.list_communes: this is reached from the
    # config flow on the event loop, and every other parse in this
    # module goes through a thread.
    communes = await asyncio.to_thread(_parse_commune_options, html)
    if not communes:
        raise ExtractorError("could not discover any De Watergroep communes from the dropdown")
    return tuple(communes)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_FLANDERS,
    fetch=fetch,
    fetch_for_commune=fetch_for_commune,
    list_communes=list_communes,
)
