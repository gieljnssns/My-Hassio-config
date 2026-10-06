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

"""AGSO Knokke-Heist -- water utility for the single Knokke-Heist commune (~33 k pop).

Source: https://www.agsoknokke-heist.be/waterbedrijf/tarieven/tarieven-kleinverbruikers

The page exposes two tables side-by-side, one for the previous year
and one for the current year; the next-year section is introduced by a
``Wijziging per 1 januari <YYYY>`` heading. Each table follows the
canonical "Integrale waterprijs" layout::

    Tariefschijf       | Basis (huishoudelijk) | comfort | tot 1.000m³ | >1.000m³ | Vast recht | Korting/dom
    Drinkwater         | € 2,3295              | € 4,6590| € 2,7073    | € 2,1658 | € 50,00    | -€ 10,00
    Afvoer afvalwater  | € 1,9572              | € 3,9144| € 2,2173    | € 2,2173 | € 30,00    | -€ 6,00
    Zuivering afvalwater| € 1,7019             | € 3,4038| € 1,9281    | € 1,9281 | € 20,00    | -€ 4,00
    Integrale prijs ex-BTW | €5,9886           | ...

Picks the table the page labels with the year asked for, or the
newest year that has already started, as long as every table carries
a heading with a year. When one does not, or none of the dated tables
has started yet, the table whose "Integrale waterprijs" total is the
highest is taken as the current one, since operators only ever index
up year-on-year.

Stores all three components separately (drinkwater + afvoer +
zuivering) the way Pidpa does, so the ``basis_rate`` /
``sewerage_rate`` sensors decompose cleanly. Uses the standard
VMM vastrecht (50/30/20 + 10/6/4) materialised from
:mod:`const`.
"""

from __future__ import annotations

import logging
import re

import aiohttp
from bs4 import BeautifulSoup, Tag

from ..const import REGION_FLANDERS
from ._flanders import build_flanders_tariff
from ._html import extract_amounts, fetch_and_parse
from .base import ExtractorError, WaterExtractor, WaterTariff, belgian_today, carry_prior_year_card

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "agso_knokke"
LABEL = "AGSO Knokke-Heist"
SOURCE_URL = "https://www.agsoknokke-heist.be/waterbedrijf/tarieven/tarieven-kleinverbruikers"


def _row_first_amount(table: Tag, row_label: str, column: int = 1) -> float | None:
    """Return the amount in ``column`` (the basis column by default) for the
    row whose first cell contains ``row_label`` (case-insensitive substring
    match).
    """
    needle = row_label.lower()
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) <= column:
            continue
        if needle in cells[0].lower():
            amounts = extract_amounts(cells[column])
            if amounts:
                return amounts[0]
    return None


def _table_integrale_basis(table: Tag) -> float | None:
    """Return the integrale basis ex-BTW total used to rank tables."""
    return _row_first_amount(table, "integrale")


def _parse_one(table: Tag, year: int) -> WaterTariff | None:
    drinkwater = _row_first_amount(table, "drinkwater")
    afvoer = _row_first_amount(table, "afvoer")
    zuivering = _row_first_amount(table, "zuivering")
    if drinkwater is None or afvoer is None or zuivering is None:
        return None
    # The page prints the comforttarief right next to the basis column.
    # Reading it and holding it to the VMM 2x rule is what tells a column
    # reorder, an inserted incl-BTW column or a swapped cell from a real
    # rate: read by position alone, a swap shipped twice the drinkwater
    # rate with no error. The sanering comfort rates are still derived.
    comfort = _row_first_amount(table, "drinkwater", column=2)
    if comfort is None:
        raise ExtractorError("AGSO Knokke drinkwater row carries no comforttarief cell")
    if abs(comfort - 2.0 * drinkwater) > 0.01:
        raise ExtractorError(
            f"AGSO Knokke comforttarief {comfort} is not 2× basistarief {drinkwater} (VMM 2× rule)"
        )
    # The page adds the three legs up itself, in the row this module
    # already reads to rank the tables. Checking against it costs nothing
    # and is the one guard that does not go stale: the 2x rule holds just
    # as well when a cell has been read from the wrong column, and a
    # Flanders-wide constant would have to be re-pinned every January.
    integrale = _table_integrale_basis(table)
    if integrale is not None and abs(drinkwater + afvoer + zuivering - integrale) > 0.0001:
        raise ExtractorError(
            f"AGSO Knokke rows {drinkwater} + {afvoer} + {zuivering} do not add up to the "
            f"integrale waterprijs {integrale} the page prints"
        )
    return build_flanders_tariff(
        utility_id=UTILITY_ID,
        year=year,
        publication_label=f"AGSO Knokke-Heist tarieven {year}",
        source_url=SOURCE_URL,
        basis=drinkwater,
        comfort=comfort,
        sanering_gemeentelijk=afvoer,
        sanering_bovengemeentelijk=zuivering,
    )


# Each table is introduced by its own heading, in one of the two shapes
# the page has used: "OVERZICHT TARIEVEN 2025" and "OVERZICHT
# TARIEVEN&nbsp; PER 1/1/2026".
_YEAR_HEADING_RE = re.compile(
    r"OVERZICHT\s+TARIEVEN[\s\xa0]*(?:PER\s*\d{1,2}/\d{1,2}/)?(\d{4})",
    re.IGNORECASE,
)


def _year_for_table(table: Tag) -> int | None:
    """The year of the nearest heading above ``table``, if one dates it.

    The walk stops at the previous table: a heading beyond it dated that
    table, not this one, and reading it here handed a reworded heading's
    table the older year and served last year's card as the newest.
    """
    for text in table.find_all_previous(string=True):
        if text.find_parent("table") is not None:
            return None
        match = _YEAR_HEADING_RE.search(str(text))
        if match:
            return int(match.group(1))
    return None


def parse_tariff(html: str, year: int | None = None) -> WaterTariff:
    """Parse a captured AGSO Knokke-Heist tarieven page."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        raise ExtractorError("could not locate AGSO Knokke tariff tables")

    ranked: list[tuple[float, Tag]] = []
    for table in tables:
        score = _table_integrale_basis(table)
        if score is not None:
            ranked.append((score, table))
    if not ranked:
        raise ExtractorError("none of the AGSO Knokke tables carry an Integrale waterprijs row")

    target = year or belgian_today().year
    # Prefer the table the page itself labels with the year we want, then
    # the newest one that has already started. Picking by price instead
    # meant a page publishing next year's card early was read as this
    # year's, which also stopped the stale-snapshot check ever firing:
    # the year was stamped from the clock, so it always looked current.
    # Only when every table is dated, though: one whose heading no longer
    # reads as a year is as likely the newest card as any, and dating the
    # rest around it served the older card as the newest.
    dated = [(_year_for_table(table), table) for _, table in ranked]
    chosen: Tag | None = None
    chosen_year = target
    if all(y is not None for y, _ in dated):
        chosen = next((table for y, table in dated if y == target), None)
        if chosen is None:
            past = sorted((y for y, _ in dated if y is not None and y <= target), reverse=True)
            if past:
                chosen_year = past[0]
                chosen = next(table for y, table in dated if y == chosen_year)
    if chosen is None:
        # Not every table is dated: fall back to the highest integrale
        # basis, since the operator only ever indexes up year on year.
        ranked.sort(key=lambda x: x[0], reverse=True)
        chosen = ranked[0][1]
        # Stamping the clock's year on it made a card published early read
        # as this year's, and stopped the staleness check ever firing,
        # because the stamp always looked current. If the table the price
        # picked does carry a heading, that is the year it is, whatever
        # its neighbours are missing.
        chosen_year = _year_for_table(chosen) or target
        if chosen_year > target and year is None:
            raise ExtractorError(
                f"AGSO Knokke's dearest table is dated {chosen_year}, ahead of {target}, "
                "and its neighbours carry no heading to place it against"
            )

    parsed = _parse_one(chosen, chosen_year)
    if parsed is None:
        raise ExtractorError(
            "AGSO Knokke chosen table missing drinkwater / afvoer / zuivering rows"
        )
    return carry_prior_year_card(parsed, target)


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    return await fetch_and_parse(session, SOURCE_URL, parse_tariff)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_FLANDERS,
    fetch=fetch,
)
