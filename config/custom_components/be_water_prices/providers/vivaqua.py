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

"""VIVAQUA -- monopoly water utility for the Brussels-Capital Region.

Linear tariff since 2022 (no consumption blocks). Brugel approves the
multi-year period; the current card runs through 2026, with a new one
expected for 2027.

Source: https://www.vivaqua.be/en/the-domestic-linear-rate/
The page exposes one ``<table>`` per year; the parser picks the table
whose header includes the current year (matching ``"<year>"`` plus the
``"VAT"`` keyword to avoid the side "rates 2025" comparison block).

The table uses the layout::

    Price from January 1st <YYYY> (VAT included 6 %)
    Fixed charge (per year)            € 40,23
      supply                            € 19,69
      sanitation                        € 20,54
    Variable charge (per m³)            € 5,35
      supply                            € 2,62
      sanitation                        € 2,73

VIVAQUA publishes VAT-incl numbers; this parser divides by ``1 + VAT``
so :class:`WaterTariff` keeps its ex-VAT convention. The two breakdown
rows ("supply" / "sanitation") are surfaced as ``linear_eur_per_m3``
(supply) and ``sanering_gemeentelijk_eur_per_m3`` (sanitation, billed
on behalf of Hydria). Their sum equals the variable-charge total.
"""

from __future__ import annotations

import logging
import re
from datetime import date

import aiohttp
from bs4 import BeautifulSoup, Tag

from ..const import DEFAULT_VAT_RATE, REGION_BRUSSELS
from ._html import extract_amounts, fetch_and_parse
from ._pdf import fold_accents
from .base import ExtractorError, WaterExtractor, WaterTariff, belgian_today, carry_prior_year_card

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "vivaqua"
LABEL = "VIVAQUA"
SOURCE_URL = "https://www.vivaqua.be/en/the-domestic-linear-rate/"


def _label_for_year(year: int) -> str:
    return f"Price from January 1st {year} (VAT included 6 %)"


# The 6 % that marks the residential card, wherever the header puts it.
# Matching the literal "VAT included 6" meant any rewording of the header
# ("6 % VAT included", "incl. 6% VAT") read as "card not published yet",
# and the parser then served last year's rates until 31 March with only a
# warning, which is exactly the outcome the fallback exists to avoid on a
# card that IS there.
_RESIDENTIAL_VAT_RE = re.compile(r"\b6\s*%")


def _residential_table(soup: BeautifulSoup, year: int) -> Tag | None:
    """The ``<table>`` for ``year`` that carries the 6 % VAT marker."""
    for table in soup.find_all("table"):
        text = fold_accents(table.get_text(" ", strip=True))
        if str(year) in text and "vat" in text and _RESIDENTIAL_VAT_RE.search(text):
            return table
    return None


def _parse_year_table(soup: BeautifulSoup, year: int) -> WaterTariff | None:
    """Try to parse the ``<table>`` for ``year``; return None if absent.

    Absent means the year's card is not on the page yet, which the caller
    answers by falling back to the previous year. A card that *is* present
    but whose rows no longer parse raises instead: that is a broken parser,
    and silently serving last year's rates for it would hide the breakage.
    """
    # Pin to the residential 6 % card. A non-residential 21 % card on
    # the same page would also contain "vat" + the year and silently
    # bind to the wrong rate.
    table = _residential_table(soup, year)
    if table is None:
        return None

    # Walk rows to anchor each amount to its label rather than relying on
    # positional order; the page has occasionally swapped supply/sanitation
    # rows on prior re-renders.
    fixed_total = fixed_supply = fixed_sanitation = None
    var_total = var_supply = var_sanitation = None

    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True).lower() for td in tr.find_all(["td", "th"])]
        if len(cells) < 2:
            continue
        label_only = cells[0]
        reads_this_row = (
            "fixed charge" in label_only
            or "variable charge" in label_only
            or (label_only in ("supply", "sanitation"))
        )
        if len(cells) > 2 and reads_this_row:
            # One label, one value: that is the shape this card has always
            # had. Reading cells[-1] out of a wider row would silently take
            # whichever column happens to sit last, and VIVAQUA putting the
            # current year first in a merged multi-year table would price
            # the previous one -- 416.54 EUR a year against 468.23 on the
            # 2025/2026 pair, with the supply-plus-sanitation cross-check
            # passing, because all three figures would come from the same
            # wrong column.
            raise ExtractorError(
                f"VIVAQUA {year} row {cells[0]!r} has {len(cells)} cells; this card is "
                "read as one label and one value, so a wider row needs the column "
                "picking rather than guessing"
            )
        if len(cells) > 2:
            # A wide row the parser does not read is a footnote or a note
            # appended to the same table. It used to be skipped, and
            # refusing the whole card for it killed VIVAQUA on a purely
            # cosmetic edit.
            continue
        label, value = cells[0], cells[1]
        amounts = extract_amounts(value)
        if not amounts:
            continue
        amt = amounts[0]
        if "fixed charge" in label:
            fixed_total = amt
        elif "variable charge" in label:
            var_total = amt
        elif label == "supply":
            if fixed_supply is None:
                fixed_supply = amt
            else:
                var_supply = amt
        elif label == "sanitation":
            if fixed_sanitation is None:
                fixed_sanitation = amt
            else:
                var_sanitation = amt

    if None in (fixed_total, var_total, var_supply, var_sanitation):
        raise ExtractorError(f"VIVAQUA {year} table found but its rows could not be parsed")
    assert fixed_total is not None
    assert var_total is not None
    assert var_supply is not None
    assert var_sanitation is not None

    # Cross-check: supply + sanitation must reconstruct the totals to the
    # cent, one cent of rounding allowed since the rows are rounded on
    # their own. Catches a published page where one of the rows was
    # edited but the headline value was not. Compared in whole cents: on
    # binary floats the real 2025 card's one-cent gap came out as
    # 0.00999, and the same gap with other cent values came out over.
    if _cents_apart(var_supply, var_sanitation, var_total) > 1:
        raise ExtractorError(
            f"VIVAQUA variable supply ({var_supply}) + sanitation ({var_sanitation})"
            f" != total ({var_total})"
        )
    if (
        fixed_supply is not None
        and fixed_sanitation is not None
        and _cents_apart(fixed_supply, fixed_sanitation, fixed_total) > 1
    ):
        raise ExtractorError(
            f"VIVAQUA fixed supply ({fixed_supply}) + sanitation"
            f" ({fixed_sanitation}) != total ({fixed_total})"
        )

    vat = 1.0 + DEFAULT_VAT_RATE
    return WaterTariff(
        utility=UTILITY_ID,
        region=REGION_BRUSSELS,
        valid_from=date(year, 1, 1),
        valid_until=date(year, 12, 31),
        publication_label=_label_for_year(year),
        source_url=SOURCE_URL,
        yearly_fixed_fee=fixed_total / vat,
        linear_eur_per_m3=var_supply / vat,
        sanering_gemeentelijk_eur_per_m3=var_sanitation / vat,
        vat_rate=DEFAULT_VAT_RATE,
    )


def _cents_apart(part: float, other: float, total: float) -> int:
    """How many cents the two parts miss the total by."""
    return abs(round(part * 100) + round(other * 100) - round(total * 100))


def parse_tariff(html: str, year: int | None = None) -> WaterTariff:
    """Parse a captured ``vivaqua/the-domestic-linear-rate`` page.

    ``year`` defaults to the current calendar year and falls back to
    the previous year if the page has not yet been refreshed (Brugel
    typically publishes the new card in late December).
    """
    soup = BeautifulSoup(html, "html.parser")
    target = year or belgian_today().year
    snapshot = _parse_year_table(soup, target)
    if snapshot is not None:
        return snapshot
    fallback = _parse_year_table(soup, target - 1)
    if fallback is not None:
        _LOGGER.warning(
            "VIVAQUA page does not yet show %d rates, falling back to %d",
            target,
            target - 1,
        )
        return carry_prior_year_card(fallback, target)
    raise ExtractorError(f"could not locate a VIVAQUA tariff table for {target} or {target - 1}")


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    return await fetch_and_parse(session, SOURCE_URL, parse_tariff)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_BRUSSELS,
    fetch=fetch,
)
