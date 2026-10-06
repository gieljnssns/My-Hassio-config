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

"""Water-link -- Antwerp city + ring (~200 k customers).

Source PDF (one per year), linked from the Antwerpen tariff page:
    https://water-link.be/sites/default/files/<YYYY>-<MM>/<YYYY>%20HH.pdf

The upload directory carries the month the card was published, so the link
is read off the tariff page rather than templated, and the January path is
kept only as a fallback. The page also links the "andere" and "NHH"
(non-household) cards, so the anchor has to reject those.

The watertarieven HTML page exposes 22 unlabelled rate tables and is
brittle to parse for "the current year"; the PDF link surfaced through
the same page (in the "Publicaties" sidebar) is much cleaner. It carries
one canonical set of rates for the year, broken down per commune::

    Tarieven Water-Link
    Geldig vanaf 1 januari 2026
                                          Water  Afvoer  Zuivering  Totaal
    Vastrecht per wooneenheid             50,0   30,0    20,0       100,0
    Korting per gedomicilieerde inwoner   -10,0  -6,0    -4,0       -20,0
    ...
    Integrale waterprijs basistarief
        Antwerpen                         1.6692 1.3345  1.7019     4.7056
        Beveren-Kruibeke-Zwijndrecht      1.6692 1.9572  1.7019     5.3283
        Edegem                            1.6692 1.9572  1.7019     5.3283
        ...

Drinkwater (Water column) and zuivering (Zuivering column) are uniform
across the service area; only the gemeentelijke afvoer differs by
commune (Antwerpen sits lower at 1.3345 €/m³, the four ring communes
at 1.9572 €/m³). The PDF carries one BASISTARIEF row per commune --
five in 2026: Antwerpen, Beveren-Kruibeke-Zwijndrecht, Edegem, Hove,
Mortsel. The extractor stores **Antwerpen's rates** as the default
since it is the city Water-link is named after and accounts for the
bulk of customers; ring-commune users pick their commune via the
OptionsFlow to get the right sanering rate.

Comforttarief is exactly 2× basis per VMM mandate; we cross-check.
"""

from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import urljoin, urlparse

import aiohttp

from ..const import REGION_FLANDERS
from ._flanders import build_flanders_tariff
from ._html import fetch_and_parse
from ._pdf import fetch_pdf_text_layout, stated_card_year, to_float
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

UTILITY_ID = "water_link"
LABEL = "Water-link"
# The Drupal upload directory carries the year and month the card was
# published, so it cannot be templated: a card uploaded in December or in
# February sits under a different path and this URL would 404. Kept as the
# fallback because every card so far has landed in January, but the link is
# read off the tariff page first.
SOURCE_URL_FMT = "https://water-link.be/sites/default/files/{year}-01/{year}%20HH.pdf"
TARIFF_PAGE_URL = "https://water-link.be/informatie/tarieven-en-kortingen/tarieven/antwerpen"
_PDF_HOST = "water-link.be"
# Bind the year to the filename, not to anywhere in the href: the upload
# directory carries a year too, so a loose match would read
# ".../2026-12/2027 HH.pdf" as the 2026 card and serve next year's rates.
# The page also links "<year> andere.pdf" and "<year> NHH_0.pdf" (non-
# household), which the required "<year><sep>HH.pdf" shape excludes.
# Drupal appends "_0", "_1", ... when a file is re-uploaded under the
# same name, which is how a corrected card would arrive; the suffix is
# allowed so that card is found rather than the January template or
# last year's.
_PDF_HREF_RE_FMT = r'href=["\']?([^"\'>\s]*{year}(?:%20|[\s_-])?HH(?:_\d+)?\.pdf[^"\'>\s]*)'

# Commune to anchor the rate row on. Antwerpen is the largest customer
# block; ring communes share the same drinkwater/zuivering numbers but
# carry a higher gemeentelijke afvoer rate (1.9572 vs Antwerpen's 1.3345
# in 2026).
_DEFAULT_COMMUNE = "Antwerpen"

# Postcodes inside Water-link's area that its card does not bill at the
# Antwerpen rate. 2070 is Zwijndrecht and Burcht, across the Scheldt,
# which the card puts in the Beveren-Kruibeke-Zwijndrecht row at a
# gemeentelijke afvoer of 1,9572 against Antwerpen's 1,3345: 66 EUR a
# year on an 80 m3 household that left the commune dropdown alone.
_POSTCODE_COMMUNES: dict[str, str] = {
    "2070": "Beveren-Kruibeke-Zwijndrecht",
    # Hove, Mortsel and Edegem are communes of their own with a row of
    # their own, all three at the ring rate. The nine city-district
    # postcodes above 2070 need no entry: the card bills the whole city
    # on the Antwerpen row, which is the default.
    "2540": "Hove",
    "2640": "Mortsel",
    "2650": "Edegem",
}


def commune_for_postcode(postcode: str) -> str | None:
    """The commune Water-link bills ``postcode`` at, when it is not the default."""
    return _POSTCODE_COMMUNES.get(postcode.strip())


# Anchored on "<commune>  N,NNNN  N,NNNN  N,NNNN  N,NNNN  N,NNNN" -- five
# columns: Water, Afvoer, Zuivering, Totaal-ex-BTW, Totaal-incl-BTW. The
# fourth is read too: it is the sum of the first three, so a row that
# lost or gained a column, which shifts every field, no longer adds up.
_RATE_ROW_RE_FMT = (
    r"^{commune}\s+([\d]+,\d{{3,5}})\s+([\d]+,\d{{3,5}})\s+([\d]+,\d{{3,5}})\s+([\d]+,\d{{3,5}})"
)


def _parse_commune_row(
    text: str, commune: str, after_marker: str
) -> tuple[float, float, float] | None:
    """Find the first occurrence of ``after_marker`` then the next line
    that starts with ``commune`` followed by the four EUR amounts. Returns
    ``(water, afvoer, zuivering)`` or ``None`` if not found; raises when
    the three do not make the printed total.
    """
    cut = text.find(after_marker)
    if cut < 0:
        return None
    pattern = re.compile(_RATE_ROW_RE_FMT.format(commune=re.escape(commune)), re.MULTILINE)
    match = pattern.search(text, cut)
    if match is None:
        return None
    water, afvoer, zuivering, total = (to_float(match.group(i)) for i in range(1, 5))
    if abs(water + afvoer + zuivering - total) > 5e-5:
        raise ExtractorError(
            f"Water-link row for {commune} does not add up: "
            f"{water} + {afvoer} + {zuivering} != {total}"
        )
    return (water, afvoer, zuivering)


def parse_tariff(
    text: str,
    year: int | None = None,
    commune: str = _DEFAULT_COMMUNE,
    source_url: str | None = None,
) -> WaterTariff:
    """Parse a captured Water-link huishoudelijk PDF.

    ``source_url`` cites the PDF actually read. It defaults to the
    templated January path for callers that only have the text, such as
    the fixture tests and the drift check.
    """
    target = year or belgian_today().year
    # The card states the year it applies from. Dating it from the file
    # name or the page URL alone meant a link left pointing at an older
    # card was served as this year's, and carry_prior_year_card and the
    # staleness check could never retire it.
    stated = stated_card_year(text)
    if stated is not None and stated != target:
        raise ExtractorError(
            f"Water-link card states it applies from 1 January {stated}, "
            f"not {target} as its link says"
        )
    basis = _parse_commune_row(text, commune, "BASISTARIEF")
    comfort = _parse_commune_row(text, commune, "COMFORTTARIEF")
    if basis is None:
        raise ExtractorError(f"could not find Water-link basistarief row for {commune!r}")
    if comfort is None:
        raise ExtractorError(f"could not find Water-link comforttarief row for {commune!r}")

    water_basis, afvoer_basis, zuivering_basis = basis
    water_comfort = comfort[0]
    if abs(water_comfort - 2.0 * water_basis) > 0.01:
        raise ExtractorError(
            f"Water-link comforttarief {water_comfort} is not 2× basistarief {water_basis} (VMM 2× rule)"
        )

    return build_flanders_tariff(
        utility_id=UTILITY_ID,
        year=target,
        publication_label=f"Water-link tarieven huishoudelijk {target} ({commune})",
        source_url=source_url or SOURCE_URL_FMT.format(year=target),
        basis=water_basis,
        comfort=water_comfort,
        sanering_gemeentelijk=afvoer_basis,
        sanering_bovengemeentelijk=zuivering_basis,
    )


def _find_pdf_href(html: str, year: int) -> str:
    """Pull the household tariff PDF link for ``year`` out of the page."""
    m = re.search(_PDF_HREF_RE_FMT.format(year=year), html, re.IGNORECASE)
    if m is None:
        raise ExtractorError(f"no {year} household tariff PDF link on the Water-link page")
    return m.group(1)


async def _pdf_url_for(session: aiohttp.ClientSession, year: int) -> str:
    """Return the URL of ``year``'s household tariff PDF.

    Read off the tariff page so a card uploaded outside January is still
    found. A page that does not carry the link (the prior-year fallback
    asks for a year the page no longer lists) falls back to the templated
    January path, which is where every card has landed so far.
    """
    try:
        href = await fetch_and_parse(session, TARIFF_PAGE_URL, _find_pdf_href, year)
    except TransientFetchError:
        raise
    except ExtractorError as err:
        _LOGGER.info(
            "Water-link %d PDF link not on the tariff page (%s); using the January path", year, err
        )
        return SOURCE_URL_FMT.format(year=year)
    url = urljoin(TARIFF_PAGE_URL, href)
    host = (urlparse(url).hostname or "").lower()
    if urlparse(url).scheme != "https" or (
        host != _PDF_HOST and not host.endswith(f".{_PDF_HOST}")
    ):
        raise ExtractorError(f"Water-link tariff PDF link points off-site: {url}")
    return url


async def _fetch_pdf_text(session: aiohttp.ClientSession) -> tuple[str, int, str]:
    """Fetch this year's PDF, falling back to last year.

    Returns ``(text, year, url)``; the URL is the one actually read, which
    is not the templated path whenever the card was uploaded outside
    January.
    """
    target = belgian_today().year
    try:
        url = await _pdf_url_for(session, target)
        return await fetch_pdf_text_layout(session, url), target, url
    except ExtractorError as err:
        if isinstance(err, TransientFetchError):
            # A transient blip (5xx / 429 / timeout) on this year's URL must
            # propagate so live_check classifies it as TRANSIENT instead of
            # being masked by silently serving last year's prices.
            raise
        _LOGGER.info("Water-link %d PDF unavailable (%s); trying %d", target, err, target - 1)
        url = await _pdf_url_for(session, target - 1)
        return await fetch_pdf_text_layout(session, url), target - 1, url


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    text, year, url = await _fetch_pdf_text(session)
    tariff = await asyncio.to_thread(parse_tariff, text, year=year, source_url=url)
    return carry_prior_year_card(tariff, belgian_today().year)


async def fetch_for_commune(session: aiohttp.ClientSession, commune: str) -> WaterTariff:
    text, year, url = await _fetch_pdf_text(session)
    tariff = await asyncio.to_thread(parse_tariff, text, year=year, commune=commune, source_url=url)
    return carry_prior_year_card(tariff, belgian_today().year)


# Anchored on the start-of-line: each commune row in the PDF starts at
# column 0 followed by 5 EUR amounts (Water, Afvoer, Zuivering, Total ex,
# Total incl). We extract the commune name token (everything before the
# first run of digits-comma) and use it as both the id and the label.
# The name is words joined by single spaces. A space inside the lazy
# class, followed by `\s+`, let the engine split a run of spaces every
# way it could before giving up, which is quadratic in the run, and this
# scan used to run on the event loop from the config flow.
_COMMUNE_LINE_RE = re.compile(
    r"^([A-Z][A-Za-zÀ-ÿ-]*(?: [A-Za-zÀ-ÿ-]+)*)"
    r"\s+\d+,\d{3,5}\s+\d+,\d{3,5}\s+\d+,\d{3,5}\s+\d+,\d{3,5}\s+\d+,\d{3,5}\s*$",
    re.MULTILINE,
)


def _parse_commune_lines(text: str) -> tuple[CommuneOption, ...]:
    """The communes named in the BASISTARIEF block of a household card."""
    cut = text.find("BASISTARIEF")
    end = text.find("COMFORTTARIEF", cut) if cut >= 0 else -1
    if cut < 0 or end < 0:
        raise ExtractorError("could not isolate the Water-link BASISTARIEF block")
    block = text[cut:end]
    communes: list[CommuneOption] = []
    seen: set[str] = set()
    for match in _COMMUNE_LINE_RE.finditer(block):
        name = match.group(1).strip()
        if name in seen or name.lower() in {"basistarief", "comforttarief"}:
            continue
        seen.add(name)
        communes.append(CommuneOption(id=name, label=name))
    if not communes:
        raise ExtractorError("Water-link BASISTARIEF block had no commune rows")
    return tuple(communes)


async def list_communes(session: aiohttp.ClientSession) -> tuple[CommuneOption, ...]:
    """Discover the communes Water-link serves from the BASISTARIEF block.

    Reached from the config flow on the event loop, so the scan goes to a
    thread like every other parse in this package.
    """
    text, _year, _url = await _fetch_pdf_text(session)
    return await asyncio.to_thread(_parse_commune_lines, text)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_FLANDERS,
    fetch=fetch,
    fetch_for_commune=fetch_for_commune,
    list_communes=list_communes,
    commune_for_postcode=commune_for_postcode,
)
