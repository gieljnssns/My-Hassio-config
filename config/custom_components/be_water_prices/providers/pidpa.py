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

"""Pidpa -- water utility for the Antwerp province (~1.2 M inhabitants).

Two ingestion paths:

  1. **Per-commune** page at ``/ons-aanbod/je-gemeente/<slug>``, one
     ``<table>`` per year (2018-2026) inside a tabbed widget, carrying
     the current published rates. With no commune configured the fetch
     reads a fixed default commune's page (Geel).

     Pidpa nearly charges one rate across the province, and this module
     used to say it charged exactly one. It does not: of the 63 communes
     it serves, Nijlen, Wommelgem and Kasterlee publish a lower
     gemeentelijke saneringsbijdrage than the other 60, so the Geel
     default over-charged them by 27, 19 and 5 EUR a year. Their
     postcodes are pre-selected in the config flow through
     :data:`_POSTCODE_COMMUNES`; everywhere else the default really is
     the household's own rate.

  2. **Tariefplan PDF** (covering 2025-2030) at
     ``/sites/default/files/2024-05/Tariefplan_2025-2030_simulatie_type_gezin.pdf``,
     no longer served to anyone. It used to be the fallback when the
     commune page could not be read, and it is kept only as the drift
     check's own subject, because it is a May-2024
     projection: the drinkwater column was never indexed and the
     saneringsbijdragen paragraph is frozen at 2024, so its 2026 column
     sits about 14 % under the rate the commune pages publish. It used
     to be the default, which is how that gap shipped for months.

PDF rows::

    Tarieven Vast recht Korting/DOM
    Drinkwater € 50,00 € 10,00
    Riolering € 30,00 € 6,00
    Zuivering € 20,00 € 4,00

    Drinkwatertarief
    (excl. BTW)         2025 2026 2027 2028 2029 2030
    basistarief
    huishoudelijk       2,0462 2,0848 2,1233 2,1619 2,2004 2,239
    ( €/m³)
    comforttarief
    huishoudelijk       4,0924 4,1696 4,2466 4,3238 4,4008 4,478
    (€/m³)

The vastrecht / korting numbers are the standard VMM structure, carried
as constants; the PDF's own lines for them are not read.

Saneringsbijdragen (afvoer + zuivering) come from a separate paragraph
near the top of the PDF::

    Tarief gemeentelijke sanering (afvoer): 1,6533 €/m³ basistarief
        and 3,3066 €/m³ comforttarief.
    Tarief bovengemeentelijke sanering (zuivering): 1,1809 €/m³ basistarief
        and 2,3619 €/m³ comforttarief.

We store only the *basis* values; the cost engine doubles them in the
comfort block (the ``2 ×`` rule is a Flemish bill mandate, see
:func:`pricing.compute_annual_cost`).

Per-commune HTML rows (one 5x5 table per year, all years inlined and
toggled via CSS)::

    | (header)  | Drinkwater | Gem. afvoer  | Bov. zuivering | Integrale |
    | Vastrecht | 50 ex/53 in| 30 / 31,8    | 20 / 21,2      | 100 / 106 |
    | Korting   | 10 / 10,6  | 6  / 6,36    | 4  / 4,24      | 20  / 21,2|
    | Basis /m3 | N,NNNN ex  | N,NNNN ex    | N,NNNN ex      | sum       |
    | Comfort/m3| 2N,NNN     | 2N,NNN       | 2N,NNN         | sum       |

The year tab is identified by ``id="tabid-<hash>-tab-<year>"``; the
huishoudelijk outer tab by ``id="tabid-<hash>-tab-0"``. We pick the
``Basistarief`` row's ex-VAT amount in the Drinkwater / Afvoer /
Zuivering columns.
"""

from __future__ import annotations

import asyncio
import logging
import re

import aiohttp
from bs4 import BeautifulSoup, Tag

from .._phantom_blocklists import PIDPA_UNSERVABLE_SLUGS as _UNSERVABLE_COMMUNE_SLUGS
from ..const import REGION_FLANDERS
from ._flanders import build_flanders_tariff
from ._html import fetch_and_parse, fetch_html
from ._pdf import fetch_pdf_text_layout, to_float
from .base import (
    CommuneOption,
    ExtractorError,
    WaterExtractor,
    WaterTariff,
    belgian_today,
    carry_prior_year_card,
)

_LOGGER = logging.getLogger(__name__)

# Re-exported under the existing name so ``async_migrate_entry`` and
# the test suite stay decoupled from the leaf module.
__all__ = ("EXTRACTOR", "_UNSERVABLE_COMMUNE_SLUGS")

UTILITY_ID = "pidpa"
LABEL = "Pidpa"
SOURCE_URL = (
    "https://www.pidpa.be/sites/default/files/2024-05/Tariefplan_2025-2030_simulatie_type_gezin.pdf"
)
COMMUNE_URL_FMT = "https://www.pidpa.be/ons-aanbod/je-gemeente/{slug}"
SITEMAP_URL = "https://www.pidpa.be/sitemap.xml"

# Default commune for the no-commune fetch. Any served commune's page
# carries the rate 60 of the 63 communes pay; Geel is the one the test
# fixture captures, and the fixture_drift check already watches it.
_DEFAULT_COMMUNE_SLUG = "geel"
_DEFAULT_COMMUNE_LABEL = "Geel (Pidpa default)"

# The three communes whose gemeentelijke saneringsbijdrage is not the one
# the Geel default carries, checked against all 63 commune pages on
# 2026-09-08: Nijlen 1,7019, Wommelgem 1,7814 and Kasterlee 1,9078
# against the other 60 at 1,9572. Left to the default they were
# over-charged 27.06, 18.64 and 5.24 EUR a year.
_POSTCODE_COMMUNES: dict[str, str] = {
    "2560": "nijlen",
    "2160": "wommelgem",
    "2460": "kasterlee",
}


def commune_for_postcode(postcode: str) -> str | None:
    """The commune slug for a postcode Pidpa does not bill at the default rate."""
    return _POSTCODE_COMMUNES.get(postcode.strip())


# The PDF text extraction yields "Drinkwatertarief\n2025 2026 2027 2028 2029 2030\n(excl. BTW)\n…",
# i.e. the year header sits between the section title and "(excl. BTW)". We
# anchor on "Drinkwatertarief" + the year run, then capture the per-year
# basis row underneath and pull the column matching our target year.
_BASIS_RE = re.compile(
    r"basistarief\s+huishoudelijk\s+([\d.,]+(?:\s+[\d.,]+)+)",
    re.IGNORECASE,
)
_COMFORT_RE = re.compile(
    r"comforttarief\s+huishoudelijk\s+([\d.,]+(?:\s+[\d.,]+)+)",
    re.IGNORECASE,
)
_HEADER_RE = re.compile(
    r"Drinkwatertarief\s+(?P<years>(?:20\d{2}\s*){2,})",
    re.IGNORECASE,
)
# Anchor on the parenthesised role label ("afvoer" / "zuivering") so the
# "bovengemeentelijke" line cannot be matched by the "gemeentelijke" regex
# (which would otherwise hit on the substring "gemeentelijke" inside
# "bovengemeentelijke"). The PDF has stray whitespace ("(afvoer )" with a
# trailing space, "(zuivering) :" with a gap before the colon) so we
# tolerate spaces around the punctuation.
# The year between the label and the colon is optional on the page and
# is kept: a line for another year must not win over this year's, and
# the last line no longer wins by default.
_SAN_RE = re.compile(
    r"\(\s*(afvoer|zuivering)\s*\)\s*(\d{4})?\s*:\s*([\d.,]+)\s*€/m³",
    re.IGNORECASE,
)


def _sanering_for_year(text: str, year: int) -> dict[str, float]:
    """The afvoer / zuivering rates for ``year``.

    This year's line first, an undated one next, else the latest line
    dated up to this year: the Tariefplan PDF dates its sanering 2024
    and freezes it there, which is the frozen figure the fallback card
    documents.
    """
    found: dict[str, dict[int | None, float]] = {}
    for match in _SAN_RE.finditer(text):
        dated = int(match.group(2)) if match.group(2) else None
        found.setdefault(match.group(1).lower(), {})[dated] = to_float(match.group(3))
    chosen: dict[str, float] = {}
    for kind, by_year in found.items():
        past = [dated for dated in by_year if dated is not None and dated <= year]
        if year in by_year:
            chosen[kind] = by_year[year]
        elif None in by_year:
            chosen[kind] = by_year[None]
        elif past:
            chosen[kind] = by_year[max(past)]
    return chosen


def _column_for_year(years: list[int], values: list[float], year: int) -> float | None:
    if len(years) != len(values):
        # The year header and the value row come from the same multi-year
        # column layout in the PDF; a length mismatch means the table has
        # been redesigned. Surface it instead of silently truncating with
        # zip(strict=False) and reporting a wrong-year number under the
        # right-year label.
        raise ExtractorError(
            f"Pidpa year header has {len(years)} columns but value row has {len(values)}"
        )
    for y, v in zip(years, values, strict=True):
        if y == year:
            return v
    return None


def _parse_year_row(text: str, pattern: re.Pattern[str]) -> list[float]:
    match = pattern.search(text)
    if not match:
        return []
    return [to_float(token) for token in match.group(1).split()]


def _parse_year_header(text: str) -> list[int]:
    match = _HEADER_RE.search(text)
    if not match:
        return []
    return [int(token) for token in match.group("years").split()]


def parse_tariff(text: str, year: int | None = None) -> WaterTariff:
    """Parse a captured Pidpa Tariefplan PDF (extracted via pdfplumber)."""
    target = year or belgian_today().year
    years = _parse_year_header(text)
    if not years:
        raise ExtractorError("could not locate the (excl. BTW) year header in Pidpa PDF")

    basis_row = _parse_year_row(text, _BASIS_RE)
    comfort_row = _parse_year_row(text, _COMFORT_RE)
    if not basis_row or not comfort_row:
        raise ExtractorError("could not locate basistarief / comforttarief row in Pidpa PDF")

    asked = target
    basis = _column_for_year(years, basis_row, target)
    comfort = _column_for_year(years, comfort_row, target)
    if basis is None or comfort is None:
        # Fall back to the latest year present (the multi-year PDF stops at 2030;
        # past 2030 we serve the closing year so sensors don't go blank).
        basis = basis_row[-1]
        comfort = comfort_row[-1]
        target = years[-1]
        _LOGGER.warning("Pidpa PDF does not list %d, falling back to %d", asked, target)

    if abs(comfort - 2.0 * basis) > 0.01:
        raise ExtractorError(
            f"Pidpa comforttarief {comfort} is not 2× basistarief {basis} for {target}"
        )

    sanering = _sanering_for_year(text, target)
    if "afvoer" not in sanering or "zuivering" not in sanering:
        raise ExtractorError(
            "could not parse Pidpa saneringsbijdragen (afvoer / zuivering); "
            f"found: {sorted(sanering)}"
        )
    gemeentelijk = sanering["afvoer"]
    bovengemeentelijk = sanering["zuivering"]

    tariff = build_flanders_tariff(
        utility_id=UTILITY_ID,
        year=target,
        publication_label=f"Pidpa Tariefplan 2025-2030 column {target}",
        source_url=SOURCE_URL,
        basis=basis,
        comfort=comfort,
        sanering_gemeentelijk=gemeentelijk,
        sanering_bovengemeentelijk=bovengemeentelijk,
    )
    return carry_prior_year_card(tariff, asked)


async def fetch_tariefplan(session: aiohttp.ClientSession) -> WaterTariff:
    """The Tariefplan PDF projection. Fallback only; see the module docstring."""
    text = await fetch_pdf_text_layout(session, SOURCE_URL)
    return await asyncio.to_thread(parse_tariff, text)


# --- per-commune ingestion ---------------------------------------------------

# Cell text on the per-commune table looks like
# "2,1888 euro excl. btw - 2,3201 euro incl. btw" with optional whitespace
# (incl. NBSP) between the number and the unit; we anchor on the ex-VAT half.
_EX_VAT_AMOUNT_RE = re.compile(r"(\d+,\d+)\s*euro\s*excl", re.IGNORECASE)
# Pidpa publishes its commune slugs in the public sitemap.xml.
_COMMUNE_SLUG_RE = re.compile(r"https://www\.pidpa\.be/ons-aanbod/je-gemeente/([a-z][a-z0-9-]*)<")


def _ex_vat_amount(text: str) -> float:
    match = _EX_VAT_AMOUNT_RE.search(text)
    if match is None:
        raise ExtractorError(f"could not parse ex-VAT amount from {text!r}")
    return to_float(match.group(1))


def _is_huishoudelijk_year_tab(div: Tag, *, year: int) -> bool:
    """Return True when ``div`` is the Huishoudelijke ``year`` tariff tab.

    The page nests two layers of ``tariff-tab-content`` divs:
        outer  id="tabid-<h>-tab-0"   (Huishoudelijk)
        inner  id="tabid-<h>-tab-{year}"
    We accept ``div`` as the inner tab and walk up to confirm the
    outer is the huishoudelijk tab.
    """
    if not str(div.get("id") or "").endswith(f"-tab-{year}"):
        return False
    cur: Tag | None = div
    for _ in range(5):
        cur = cur.parent if cur is not None else None
        if cur is None or cur.name is None:
            break
        classes = list(cur.get("class") or [])
        if "tariff-tab-content" in classes and str(cur.get("id") or "").endswith("-tab-0"):
            return True
    return False


def _find_year_table(soup: BeautifulSoup, *, year: int) -> Tag | None:
    for div in soup.find_all("div", class_="tariff-tab-content"):
        if not _is_huishoudelijk_year_tab(div, year=year):
            continue
        for table in div.find_all("table"):
            if "Integrale waterprijs" in table.get_text(" ", strip=True):
                return table
    return None


_YEAR_TAB_RE = re.compile(r"-tab-(\d{4})$")


def _find_latest_year_table(soup: BeautifulSoup, *, before: int) -> tuple[Tag, int] | None:
    """Return the (table, year) of the highest huishoudelijk year tab up to ``before``.

    Used as a Jan 1 rollover fallback, mirroring the multi-year PDF path,
    so a per-commune install does not go blank before Pidpa publishes the
    new-year tab. A tab dated past the year asked for is not a fallback
    for it: with no tab for this year, next year's card would otherwise
    be served as this year's.
    """
    best: tuple[Tag, int] | None = None
    for div in soup.find_all("div", class_="tariff-tab-content"):
        match = _YEAR_TAB_RE.search(str(div.get("id") or ""))
        if match is None:
            continue
        year = int(match.group(1))
        if year > before or (best is not None and year <= best[1]):
            continue
        if not _is_huishoudelijk_year_tab(div, year=year):
            continue
        for table in div.find_all("table"):
            if "Integrale waterprijs" in table.get_text(" ", strip=True):
                best = (table, year)
                break
    return best


def parse_commune_tariff(
    html: str,
    *,
    commune_slug: str,
    year: int | None = None,
    commune_label: str | None = None,
) -> WaterTariff:
    """Parse a captured Pidpa per-commune page for ``year``.

    ``commune_label`` replaces the slug in the publication label; the
    no-commune fetch uses it to say the page stands in for the province.
    """
    target = year or belgian_today().year
    asked = target
    soup = BeautifulSoup(html, "html.parser")
    table = _find_year_table(soup, year=target)
    if table is None and year is None:
        # Production path (year not pinned): the page tops out at the
        # current year, so in the Jan 1 window before Pidpa publishes the
        # new-year tab, fall back to the latest tab present and serve the
        # still-in-force prior-year rates -- mirroring the PDF path -- so a
        # fresh per-commune install does not go blank. An explicitly
        # requested year that is absent stays an error.
        fallback = _find_latest_year_table(soup, before=target)
        if fallback is not None:
            table, fallback_year = fallback
            # The commune is the household's town: the integration
            # scrubs it everywhere it is published, so it does not go
            # into the log either.
            _LOGGER.warning(
                "Pidpa per-commune page does not list %d; falling back to %d",
                target,
                fallback_year,
            )
            target = fallback_year
    if table is None:
        raise ExtractorError(
            f"could not locate Pidpa huishoudelijk {target} table for commune {commune_slug!r}"
        )

    rows = table.find_all("tr")
    # Layout (5 rows): header / vastrecht / korting / basistarief / comforttarief.
    if len(rows) < 5:
        raise ExtractorError(
            f"Pidpa per-commune table for {commune_slug!r} has {len(rows)} rows; expected 5"
        )
    basis_cells = rows[3].find_all(["th", "td"])
    comfort_cells = rows[4].find_all(["th", "td"])
    # 5 columns: label / drinkwater / afvoer / zuivering / integrale.
    if len(basis_cells) < 4 or len(comfort_cells) < 4:
        raise ExtractorError(f"Pidpa per-commune table columns malformed for {commune_slug!r}")

    drink_basis = _ex_vat_amount(basis_cells[1].get_text(" ", strip=True))
    afvoer_basis = _ex_vat_amount(basis_cells[2].get_text(" ", strip=True))
    zuivering_basis = _ex_vat_amount(basis_cells[3].get_text(" ", strip=True))
    drink_comfort = _ex_vat_amount(comfort_cells[1].get_text(" ", strip=True))
    if abs(drink_comfort - 2.0 * drink_basis) > 0.01:
        raise ExtractorError(
            f"Pidpa drinkwater comforttarief {drink_comfort} is not 2× basistarief"
            f" {drink_basis} for {commune_slug!r} {target} (VMM 2× rule)"
        )
    # The fifth cell of the same row is the page's own sum of the three
    # before it. Checking against it is the guard that cannot go stale:
    # the 2x rule holds just as well when a cell has been read from the
    # wrong column, and a Flanders-wide constant would need re-pinning
    # every January.
    if len(basis_cells) >= 5:
        integrale = _ex_vat_amount(basis_cells[4].get_text(" ", strip=True))
        if abs(drink_basis + afvoer_basis + zuivering_basis - integrale) > 0.0001:
            raise ExtractorError(
                f"Pidpa rows {drink_basis} + {afvoer_basis} + {zuivering_basis} do not add "
                f"up to the integrale waterprijs {integrale} the page prints for "
                f"{commune_slug!r} {target}"
            )

    tariff = build_flanders_tariff(
        utility_id=UTILITY_ID,
        year=target,
        publication_label=f"Pidpa per-commune tarieven {target} ({commune_label or commune_slug})",
        source_url=COMMUNE_URL_FMT.format(slug=commune_slug),
        basis=drink_basis,
        comfort=drink_comfort,
        sanering_gemeentelijk=afvoer_basis,
        sanering_bovengemeentelijk=zuivering_basis,
    )
    return carry_prior_year_card(tariff, asked)


async def fetch_for_commune(session: aiohttp.ClientSession, commune: str) -> WaterTariff:
    return await fetch_and_parse(
        session,
        COMMUNE_URL_FMT.format(slug=commune),
        parse_commune_tariff,
        commune_slug=commune,
    )


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    """No-commune fetch: the rate off the default commune's page.

    Nothing stands in for it. The Tariefplan PDF used to: it is a
    May-2024 projection whose 2026 column reads 2,0848 / 1,6533 / 1,1809
    where the commune pages carry 2,1888 / 1,9572 / 1,7019, so it bills
    606.21 EUR a year at 80 m3 against the page's 704.68. It shipped that
    way for months once already, and the only signal was a log line.

    A card 14 % short is worse than no card: without one the coordinator
    keeps serving the last good snapshot and raises the stale-snapshot
    Repair, and the daily live check fails and opens an issue. The PDF is
    still parsed, by the drift check, which compares it against itself so
    a change in the projection is still noticed.
    """
    return await fetch_and_parse(
        session,
        COMMUNE_URL_FMT.format(slug=_DEFAULT_COMMUNE_SLUG),
        parse_commune_tariff,
        commune_slug=_DEFAULT_COMMUNE_SLUG,
        commune_label=_DEFAULT_COMMUNE_LABEL,
    )


def _slug_to_label(slug: str) -> str:
    """Title-case each hyphenated token; the user picks from the dropdown so
    cosmetic Dutch capitalisation glitches (Op / Den / De / Sint) don't matter.
    """
    return "-".join(token.capitalize() for token in slug.split("-"))


# Phantom slugs in Pidpa's sitemap -- the /ons-aanbod/je-gemeente/<slug>
# page exists but has no huishoudelijk tariff table because the commune
# is not actually served by Pidpa (Antwerpen is Water-link territory;
# Pidpa lists it for marketing reach). Picking these crashes with
# "could not locate Pidpa huishoudelijk <year> table". Drop them from
# the dropdown so users can't pick them. The data lives in
# ``_phantom_blocklists`` (imported at the top of this module).


async def list_communes(session: aiohttp.ClientSession) -> tuple[CommuneOption, ...]:
    """Discover the Pidpa-served communes from the public sitemap.

    Drops slugs that resolve to a page without a tariff table (see
    ``_UNSERVABLE_COMMUNE_SLUGS``).
    """
    sitemap = await fetch_html(session, SITEMAP_URL)
    slugs = sorted(set(_COMMUNE_SLUG_RE.findall(sitemap)))
    if not slugs:
        raise ExtractorError("Pidpa sitemap returned no commune slugs")
    return tuple(
        CommuneOption(id=s, label=_slug_to_label(s))
        for s in slugs
        if s not in _UNSERVABLE_COMMUNE_SLUGS
    )


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_FLANDERS,
    fetch=fetch,
    fetch_for_commune=fetch_for_commune,
    list_communes=list_communes,
    commune_for_postcode=commune_for_postcode,
)
