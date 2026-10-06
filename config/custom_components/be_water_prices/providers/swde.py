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

"""SWDE -- Société wallonne des eaux.

Largest Walloon distributor: ~2.4 M inhabitants across ~200 communes,
roughly two-thirds of Wallonia's population. Publishes its own CVD
(true-cost-of-supply) on https://www.swde.be/en/water-prices-swde
(the FR slug ``prix-de-l-eau-swde`` returns 404).

The page exposes the four bill components under their own ``<h3>``
headings, each followed by a ``<p>`` containing one ``<strong>`` with
the EUR value::

    <h3>1. True-cost of supply (CVD)</h3>
    <p>The current CVD amounts to <strong>€ 3.24/m³</strong>.</p>

    <h3>2. True cost of sanitation (CVA)</h3>
    <p>The current CVA is <strong>€ 2.748/m³</strong>.</p>

    <h3>3. VAT</h3>
    <p>For water supply, it amounts to <strong>6 %</strong>.</p>

    <h3>4. Social Water Fund</h3>
    <p>The current Social Water Fund amounts to <strong>€ 0.0339/m³</strong>.</p>

CVA and FSE are flat-Wallonia constants (set by SPGE / CWaPE) and live
in :mod:`const`; the parsed values are held to them and a move fails
the fetch, so the stale-snapshot Repair and the live check carry the
news rather than a log line.

The redevance (annual fixed fee) is the regulator-defined
``20·CVD + 30·CVA`` formula; we materialise it into
:attr:`WaterTariff.yearly_fixed_fee` here so the cost engine doesn't
re-derive it.

The page states no year. The card is dated by the clock, so a page
left on last year's rates in January is served as this year's and is
never stale by date. Nothing detects a CVD left on last year's value:
the CVA / FSE hold fails the fetch only when those two move, and the
daily live check only validates ranges.
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
from ._pdf import fold_accents
from ._walloon_simple import build_tariff, hold_to_constant, warn_constant_drift
from .base import ExtractorError, WaterExtractor, WaterTariff, belgian_today

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "swde"
LABEL = "SWDE"
SOURCE_URL = "https://www.swde.be/en/water-prices-swde"

# Headings that introduce each component on the page. We accent-fold
# everything before matching so a "à"/"é" re-render doesn't break us.
_CVD_HEADINGS = ("cvd", "true-cost of supply", "true cost of supply")
_CVA_HEADINGS = ("cva", "true cost of sanitation")
_FSE_HEADINGS = ("social water fund", "fonds social de l'eau", "fonds social")


def _amounts_after(heading: Tag) -> list[float]:
    """Every € amount inside the siblings after ``heading``.

    Callers take the first. Taking the largest instead was tried, to serve
    the current rate off a section that prints a historic one before it,
    and reverted: a VAT-inclusive twin of the same rate is only 6 % above
    it and a year of indexation is a few percent, so no threshold
    separates them, and reading the TVAC figure makes the cost engine
    apply the 6 % a second time. An 11 EUR slip on a page shape nobody has
    seen is the better trade against billing a household 6 % over on one
    that is ordinary.

    Walks forward through siblings until the next heading of the same
    or higher level, so the search is bounded to one section.

    Only true siblings are walked. Walking the whole remaining document
    instead descends into the *next* section's wrapper element, whose text
    already holds that section's figures, before ever reaching its
    heading: a section with no € amount of its own would then answer with
    the following section's number.
    """
    found: list[float] = []
    for sibling in heading.find_next_siblings():
        if sibling.name in ("h1", "h2", "h3", "h4"):
            break
        found.extend(extract_amounts(sibling.get_text(" ", strip=True)))
    return found


def _find_component(soup: BeautifulSoup, keywords: tuple[str, ...]) -> float | None:
    """Find the first ``<h3>`` whose text contains any of ``keywords``;
    return the first € amount in the section that follows.
    """
    for heading in soup.find_all(["h2", "h3", "h4"]):
        text = fold_accents(heading.get_text(" ", strip=True))
        if any(k in text for k in keywords):
            amounts = _amounts_after(heading)
            if amounts:
                return amounts[0]
    return None


def parse_tariff(html: str, year: int | None = None) -> WaterTariff:
    """Parse a captured ``swde.be/en/water-prices-swde`` page."""
    soup = BeautifulSoup(html, "html.parser")
    cvd = _find_component(soup, _CVD_HEADINGS)
    if cvd is None:
        raise ExtractorError("could not find SWDE CVD on the tariff page")

    hold_to_constant(
        published=_find_component(soup, _CVA_HEADINGS),
        constant=WALLONIA_CVA_EUR_PER_M3,
        label="SWDE CVA",
        logger=_LOGGER,
    )
    warn_constant_drift(
        published=_find_component(soup, _FSE_HEADINGS),
        constant=WALLONIA_FSE_EUR_PER_M3,
        label="SWDE FSE",
        logger=_LOGGER,
        # The Fonds Social is ~0.03 EUR/m3, so the 0.005 default would let a
        # 15% move pass unreported. CILE and inBW already check it at 0.001.
        threshold=0.001,
    )

    # SWDE's page states no tariff year anywhere, so the card can only be
    # dated from the clock. That means a page left on last year's rate is
    # served as this year's and the staleness check can never notice, so
    # the label says which it is rather than implying the page said so.
    stated = year is not None
    target = year or belgian_today().year
    return build_tariff(
        utility_id=UTILITY_ID,
        cvd=cvd,
        source_url=SOURCE_URL,
        publication_label=(
            f"SWDE water prices {target}"
            if stated
            else f"SWDE water prices {target} (page states no year)"
        ),
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
