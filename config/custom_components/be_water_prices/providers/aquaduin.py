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

"""Aquaduin (ex-IWVA) -- 6 communes Westkust (~80 k year-round residents).

Source: https://www.aquaduin.be/nl/zelf-regelen/tarieven/tarieven-<year>
(the tariff-card PDF link is scraped from that page; Aquaduin's CMS
serves the PDF under an opaque /volumes/... path that changes over time)

Aquaduin publishes a clean numeric tariff card PDF -- the gold-standard
example among Belgian water utilities. The PDF lays out the residential
block as::

    Basistarief 30 m³ + 30 m³ per gedomicilieerde persoon  5,9908 euro/m³  6,35
    Comforttarief > Basisverbruik (pro rata verrekend)     11,9816 euro/m³ 12

Plus the standard VMM vastrecht / korting (50/30/20 + 10/6/4 -- the
``20 %`` line in the PDF is the per-resident korting expressed as a
percentage of the matching vastrecht component).

The 5.9908 €/m³ is the **integrale waterprijs basistarief** (drinkwater
+ saneringsbijdragen combined into one per-m³ figure -- the highest
per-m³ rate among Flemish operators). The PDF does not split it into separate
drinkwater / sanering rows the way Pidpa or AGSO Knokke do. We store
it as ``basis_eur_per_m3`` with sanering = 0, which keeps the
volumetric math correct (per_m3_basis = basis + sanering still equals
the published 5.9908). The trade-off: the ``basis_rate`` sensor
shows the integrated rate rather than the drinkwater-only rate, which
is unavoidable without per-component publication.
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
    ExtractorError,
    TransientFetchError,
    WaterExtractor,
    WaterTariff,
    belgian_today,
    carry_prior_year_card,
)

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "aquaduin"
LABEL = "Aquaduin"
# Human-facing tariff page for a given year: our citation, and the page we
# scrape the PDF link from. Aquaduin rebuilt its site in 2026 and now serves
# the tariff card under an opaque, CMS-generated /volumes/... path (plus a
# ?v= cache-buster) that changes whenever the file is re-uploaded, so the
# directory cannot be hardcoded. The page URL and the "overzicht-tarieven-
# <year>.pdf" filename are the stable parts, so we discover the href here.
SOURCE_URL_FMT = "https://www.aquaduin.be/nl/zelf-regelen/tarieven/tarieven-{year}"
# The tariff PDF href is read off that page, so pin what it may resolve to.
_PDF_HOST = "aquaduin.be"

# Anchored on the PDF's exact wording -- "Basistarief 30 m³ + 30 m³ per
# gedomicilieerde persoon  N,NNNN euro/m³". The intervening "+ 30 m³ per
# gedomicilieerde persoon" string carries digits, so the gap regex uses
# ``.*?`` not ``[^0-9]*?``. Numeric format is 4-decimal Belgian (comma).
_BASIS_RE = re.compile(
    r"basistarief\s+30\s*m³.*?([\d]+,\d{3,5})\s*euro/m³",
    re.IGNORECASE | re.DOTALL,
)
# Anchor on the same "Basisverbruik" qualifier the PDF uses for the
# comforttarief row ("Comforttarief > Basisverbruik (pro rata
# verrekend) N,NNNN euro/m³") so a future explainer paragraph above
# the row cannot supply the first match. Tolerant of the ">" being
# dropped or spaced differently.
_COMFORT_RE = re.compile(
    r"comforttarief\s*>?\s*basisverbruik.*?([\d]+,\d{3,5})\s*euro/m³",
    re.IGNORECASE | re.DOTALL,
)


def _find_pdf_href(html: str, year: int) -> str:
    """Pull the ``overzicht-tarieven-<year>.pdf`` link out of a year page.

    Anchored on the stable filename; tolerant of the quote style and of a
    trailing ``?v=`` cache-buster. Raises when the page carries no PDF (the
    prior-year pages keep the numbers as inline HTML only), which lets the
    caller fall back a year or surface a real failure.
    """
    # A re-uploaded file gets a "_0", "_1", ... suffix from the CMS; a
    # corrected card would arrive that way, so the suffix is accepted.
    m = re.search(
        rf'href=["\']?([^"\'>\s]*overzicht-tarieven-{year}(?:_\d+)?\.pdf[^"\'>\s]*)',
        html,
        re.IGNORECASE,
    )
    if m is None:
        raise ExtractorError(f"no {year} tariff PDF link on Aquaduin year page")
    return m.group(1)


async def _discover_pdf_url(session: aiohttp.ClientSession, year: int) -> str:
    """Return the absolute URL of the ``year`` tariff-card PDF.

    The href comes off a remote page, so it decides what gets fetched next.
    Keep it on Aquaduin's own site over HTTPS rather than following it
    wherever it points.
    """
    page_url = SOURCE_URL_FMT.format(year=year)
    href = await fetch_and_parse(session, page_url, _find_pdf_href, year)
    pdf_url = urljoin(page_url, href)
    parsed = urlparse(pdf_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or (host != _PDF_HOST and not host.endswith(f".{_PDF_HOST}")):
        raise ExtractorError(f"Aquaduin tariff PDF link points off-site: {pdf_url}")
    return pdf_url


def parse_tariff(text: str, year: int | None = None) -> WaterTariff:
    """Parse a captured Aquaduin tariff PDF (extracted via pdfplumber)."""
    target = year or belgian_today().year
    # The card states the year it applies from. Dating it from the file
    # name or the page URL alone meant a link left pointing at an older
    # card was served as this year's, and carry_prior_year_card and the
    # staleness check could never retire it.
    stated = stated_card_year(text)
    if stated is not None and stated != target:
        raise ExtractorError(
            f"Aquaduin card states it applies from 1 January {stated}, "
            f"not {target} as its link says"
        )
    basis_m = _BASIS_RE.search(text)
    comfort_m = _COMFORT_RE.search(text)
    if basis_m is None:
        raise ExtractorError("could not locate Aquaduin basistarief in tariff PDF")
    basis = to_float(basis_m.group(1))
    comfort = to_float(comfort_m.group(1)) if comfort_m else 2.0 * basis
    if abs(comfort - 2.0 * basis) > 0.01:
        raise ExtractorError(
            f"Aquaduin comforttarief {comfort} is not 2× basistarief {basis} (VMM 2× rule)"
        )

    # basis is integrated drinkwater + sanering, see module docstring; the
    # sanering_* arguments stay at their default of 0.0.
    return build_flanders_tariff(
        utility_id=UTILITY_ID,
        year=target,
        publication_label=f"Aquaduin overzicht tarieven {target}",
        source_url=SOURCE_URL_FMT.format(year=target),
        basis=basis,
        comfort=comfort,
    )


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    """This year's card, or last year's until 31 March.

    The fallback reads the PDF link off last year's page, and Aquaduin
    strips that link once a year is over: on 2026-09-07 the 2025 page
    carried none. The fallback therefore only helps while the previous
    year's page still links its card, and when it does not, the fetch
    fails and the coordinator keeps serving the cached card with the
    stale-snapshot Repair up until the new card is published.
    """
    target = belgian_today().year
    try:
        pdf_url = await _discover_pdf_url(session, target)
        text = await fetch_pdf_text_layout(session, pdf_url)
        return await asyncio.to_thread(parse_tariff, text, year=target)
    except ExtractorError as err:
        if isinstance(err, TransientFetchError):
            # A transient blip (5xx / 429 / timeout) fetching this year's
            # page or PDF must propagate so live_check classifies it as
            # TRANSIENT instead of being masked by serving last year's prices.
            raise
        _LOGGER.info("Aquaduin %d tariff unavailable (%s); trying %d", target, err, target - 1)
        pdf_url = await _discover_pdf_url(session, target - 1)
        text = await fetch_pdf_text_layout(session, pdf_url)
        prior = await asyncio.to_thread(parse_tariff, text, year=target - 1)
        return carry_prior_year_card(prior, target)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_FLANDERS,
    fetch=fetch,
)
