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

"""CILE -- Compagnie Intercommunale Liégeoise des Eaux.

Liège region, ~560 k inhabitants across 24 communes -- the largest
Walloon distributor after SWDE. Source:
https://www.cile.be/facturation/le-prix-de-leau

The page exposes a clean 4-row table::

    Poste            | Tarif au 1er janvier <YYYY>
    C.V.A            | 2,7480 €/m³
    C.V.D            | 3,5552 €/m³
    Fonds social     | 0,0339 €/m³
    TVA 6%           |

CVA / FSE come from the SPGE flat-Wallonia constants and are
cross-checked here: a divergence between page and constant fails the
fetch.

Stores tariff like SWDE / inBW: ``cvd_eur_per_m3`` for the
distributor's value, ``cva_eur_per_m3`` and ``fse_eur_per_m3`` for
the national ones, and ``yearly_fixed_fee = 20·CVD + 30·CVA``
materialised from the regulator's redevance formula. The Wallonia
branch of :func:`pricing.compute_annual_cost` handles the tier math.
"""

from __future__ import annotations

import logging

import aiohttp
from bs4 import BeautifulSoup, Tag

from ..const import (
    REGION_WALLONIA,
    WALLONIA_CVA_EUR_PER_M3,
    WALLONIA_FSE_EUR_PER_M3,
)
from ._html import extract_amounts, fetch_and_parse
from ._walloon_simple import (
    build_tariff,
    detect_published_year,
    hold_to_constant,
    warn_constant_drift,
)
from .base import ExtractorError, WaterExtractor, WaterTariff, belgian_today

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "cile"
LABEL = "CILE"
SOURCE_URL = "https://www.cile.be/facturation/le-prix-de-leau"


def _value_column(table: Tag, year: int | None) -> int:
    """The column whose heading names ``year``, else the only one there is.

    The table has one value column today. Should a comparison column
    appear, "new | old" or "old | new", the last cell is the right one
    only half the time; the heading that carries the year is not. Falling
    back to the last column across a two-column table was a coin toss on
    which year the household got billed, so a table this cannot place the
    year in is refused instead.
    """
    head = table.find("tr")
    cells: list[str] = []
    if isinstance(head, Tag):
        cells = [c.get_text(" ", strip=True) for c in head.find_all(["td", "th"])]
        if year is not None:
            for index, cell in enumerate(cells):
                if index > 0 and str(year) in cell:
                    return index
    if len(cells) > 2:
        raise ExtractorError(
            f"CILE's table has {len(cells) - 1} value columns and none of them names "
            f"{year}; refusing to guess which year the household is billed at"
        )
    return -1


def _row_amount(table: Tag, row_label: str, column: int = -1) -> float | None:
    needle = row_label.lower()
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 2 or column >= len(cells):
            continue
        if needle in cells[0].lower():
            amounts = extract_amounts(cells[column])
            if amounts:
                return amounts[0]
    return None


def parse_tariff(html: str, year: int | None = None) -> WaterTariff:
    """Parse a captured ``cile.be/facturation/le-prix-de-leau`` page."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not isinstance(table, Tag):
        raise ExtractorError("could not locate CILE tariff table")

    # The table is headed "Tarif au 1er janvier YYYY": date the card from
    # that rather than the clock, so a page still on last year's card in
    # January looks stale instead of being relabelled as this year's.
    target = year or detect_published_year(soup.get_text(" ", strip=True)) or belgian_today().year
    column = _value_column(table, target)

    cvd = _row_amount(table, "c.v.d", column)
    if cvd is None:
        raise ExtractorError("could not find CILE CVD row")

    hold_to_constant(
        published=_row_amount(table, "c.v.a", column),
        constant=WALLONIA_CVA_EUR_PER_M3,
        label="CILE CVA",
        logger=_LOGGER,
    )
    warn_constant_drift(
        published=_row_amount(table, "fonds social", column),
        constant=WALLONIA_FSE_EUR_PER_M3,
        label="CILE FSE",
        logger=_LOGGER,
        threshold=0.001,
    )

    return build_tariff(
        utility_id=UTILITY_ID,
        cvd=cvd,
        source_url=SOURCE_URL,
        publication_label=f"CILE prix de l'eau {target}",
        year=target,
    )


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    return await fetch_and_parse(session, SOURCE_URL, parse_tariff)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_WALLONIA,
    fetch=fetch,
)
