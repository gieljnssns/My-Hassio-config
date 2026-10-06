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

"""INASEP -- Intercommunale Namuroise de Services Publics.

Wallonia (Namur sud), 10 communes, ~38 600 abonnés (~80-100 k people).
Source: https://www.inasep.be/prix-de-leau-et-evolution

The page lists the three components under a ``Tarifs YYYY`` heading,
e.g.::

    Tarifs 2026
    Coût-Vérité Distribution (CVD) = 3,6734 €/m³ depuis le 27 avril 2026
    Coût-Vérité Assainissement (CVA) = 2,748 €/m³ depuis le 1er janvier 2026
    Fonds social de l'Eau = 0,0339 €/m³ depuis le 1er janvier 2026

CVA and FSE are the SPGE flat-Wallonia constants; the values the page
prints are held to them and a move fails the fetch, as on every other
Walloon page. The parser anchors the CVD on the literal phrase
``Coût-Vérité Distribution (CVD)`` so the unrelated euros amounts
elsewhere on the page (annual-impact figures, per-glass examples)
can't win.

INASEP revises its CVD mid-year: the 2026 card dates it from 27 April.
The tariff is stamped from that day rather than from 1 January, so the
sensor attribute and the price backfill do not claim the rate for
months it did not apply to. The previous rate is not published, so the
year-to-date cost still bills the whole year's volume at the current
one.
"""

from __future__ import annotations

import logging
import re
from datetime import date

import aiohttp
from bs4 import BeautifulSoup

from ..const import REGION_WALLONIA
from ._html import fetch_and_parse
from ._pdf import to_float
from ._walloon_simple import build_tariff, check_spge_constants, detect_published_year
from .base import ExtractorError, WaterExtractor, WaterTariff, belgian_today

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "inasep"
LABEL = "INASEP"
SOURCE_URL = "https://www.inasep.be/prix-de-leau-et-evolution"

# The page renders ``Coût-Vérité Distribution (CVD) = 3,6734 €/m³``,
# but bs4's text extraction drops the accents on some passes and the
# superscript ``³`` becomes a plain ``3``. Tolerate accent-stripped
# spellings of "Coût" and "Vérité".
#
# The day the rate took effect follows the unit: "3,6734 €/m³ depuis le
# 27 avril 2026" (bs4 renders the unit as "€ €/m 3"). It is captured as
# part of the same match so only a date glued to the CVD counts; the
# CVA's own "depuis le 1er janvier" a few words later cannot answer for
# it.
#
# Every optional piece of whitespace is tied to its literal. A shape
# like `\s*X?\s+` lets the engine split one run of spaces two ways and
# try every split when the match fails, which is quadratic in the run:
# a page with a few thousand spaces after the date held the parser for
# seconds, and the body cap allows millions.
_CVD_RE = re.compile(
    r"Co[ûu]t.{0,3}V[ée]rit[ée]\s+Distribution\s*\(CVD\)\s*(?:=\s*)?([\d]+,\d{1,5})\s*€"
    r"(?:\s*€)?(?:\s*/\s*m\s*[³3]?)?"
    r"(?:\s*depuis\s+le\s+(\d{1,2})(?:\s*er)?\s+([a-zéû]+)\s+(20\d\d))?",
    re.IGNORECASE | re.DOTALL,
)
_FR_MONTHS = {
    "janvier": 1,
    "fevrier": 2,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
    "décembre": 12,
}


def _cvd_effective_date(match: re.Match[str], year: int) -> date | None:
    """The day the CVD applies from, when the page dates it inside ``year``.

    A date in an earlier year means the rate has been in force since
    before the card, and the card itself then runs from 1 January.
    """
    day, month_name, since_year = match.group(2), match.group(3), match.group(4)
    if day is None:
        return None
    month = _FR_MONTHS.get(month_name.lower())
    if month is None or int(since_year) != year:
        return None
    try:
        return date(year, month, int(day))
    except ValueError:
        return None


def parse_tariff(html: str, year: int | None = None) -> WaterTariff:
    """Parse a captured INASEP page."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    match = _CVD_RE.search(text)
    if match is None:
        raise ExtractorError("could not find INASEP CVD on the tariff page")
    cvd = to_float(match.group(1))
    check_spge_constants(text, utility_id=UTILITY_ID, logger=_LOGGER)

    # The block is headed "Tarifs YYYY": date the card from that rather
    # than the clock, so a page still on last year's card in January
    # looks stale instead of being relabelled as this year's.
    target = year or detect_published_year(text) or belgian_today().year
    return build_tariff(
        utility_id=UTILITY_ID,
        cvd=cvd,
        source_url=SOURCE_URL,
        publication_label=f"INASEP votre eau au coût-vérité {target}",
        year=target,
        valid_from=_cvd_effective_date(match, target),
    )


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    return await fetch_and_parse(session, SOURCE_URL, parse_tariff)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_WALLONIA,
    fetch=fetch,
)
