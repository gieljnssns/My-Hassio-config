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

"""inBW (ex-IECBW) -- water utility for Brabant Wallon (27 communes).

Source: https://eau.inbw.be/prix-de-leau

The page exposes one ``<table class="table">`` with the full per-tier
breakdown of an example 100 m³ residential bill. Each row carries the
unit price ("Prix unitaire" column), so we read CVD straight off the
"Consommation entre 30 et 5000 m³" row (= full CVD) and cross-check
against the "Redevance annuelle (20 x CVD)" row. CVA / FSE come from
the SPGE flat-Wallonia constants (:mod:`const`) and are cross-checked
against their published values; a move fails the fetch.

inBW's TLS chain is misconfigured -- the server does not send the
GoDaddy intermediate certificate, so the default Python trust path
fails. The fetch verifies normally and only retries with
``verify_ssl=False`` after a certificate or SSL error specifically,
logging a warning when it does, so the day inBW fixes its chain the
downgrade stops happening on its own. See the rationale in
:func:`_pdf.fetch_text`.

Tariff structure is the standard Wallonia residential model; see
:func:`pricing.compute_annual_cost` for the math.
"""

from __future__ import annotations

import asyncio
import logging
import re
import ssl

import aiohttp
from bs4 import BeautifulSoup, Tag

from ..const import (
    REGION_WALLONIA,
    WALLONIA_CVA_EUR_PER_M3,
    WALLONIA_FSE_EUR_PER_M3,
)
from ._html import extract_amounts, fetch_html
from ._walloon_simple import (
    build_tariff,
    detect_published_year,
    hold_to_constant,
    warn_constant_drift,
)
from .base import ExtractorError, WaterExtractor, WaterTariff, belgian_today

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "inbw"
LABEL = "inBW"
SOURCE_URL = "https://eau.inbw.be/prix-de-leau"


def _row_amount_after_label(table: Tag, label_keywords: tuple[str, ...]) -> float | None:
    """Return the *Prix unitaire* (3rd cell) for the row whose first cell
    contains every keyword in ``label_keywords`` (case-insensitive).

    The inBW table layout::

        | Rubrique | Quantité | Prix unitaire | Hors TVA | TVAC |

    Section headings (Coût Vérité Distribution, Fonds Social) sit on a
    row with the label in column 0 and the rest empty; the matching
    data row immediately below has an empty column 0. When the matched
    row carries no amount in *Prix unitaire*, fall through to the next
    row's *Prix unitaire* so the "Fonds Social" heading still resolves
    to the 0,0339 €/m³ rate published just below it.
    """
    needles = tuple(k.lower() for k in label_keywords)
    rows = list(table.find_all("tr"))
    for idx, tr in enumerate(rows):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 3:
            continue
        rubrique = cells[0].lower()
        if all(n in rubrique for n in needles):
            amounts = extract_amounts(cells[2])
            if amounts:
                return amounts[0]
            for next_tr in rows[idx + 1 :]:
                next_cells = [c.get_text(" ", strip=True) for c in next_tr.find_all(["td", "th"])]
                if len(next_cells) < 3:
                    continue
                if next_cells[0].strip():
                    # Different labelled row; bail out rather than reaching
                    # across into an unrelated section.
                    break
                amounts = extract_amounts(next_cells[2])
                if amounts:
                    return amounts[0]
            return None
    return None


def parse_tariff(html: str, year: int | None = None) -> WaterTariff:
    """Parse a captured ``eau.inbw.be/prix-de-leau`` page."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not isinstance(table, Tag):
        raise ExtractorError("could not locate inBW tariff table")

    cvd = _row_amount_after_label(table, ("consommation", "30", "5000"))
    if cvd is None:
        raise ExtractorError("could not find inBW full-CVD row (Consommation entre 30 et 5000 m³)")

    # Cross-check: row "0 et 30 m³" should be exactly half the full CVD.
    half_cvd = _row_amount_after_label(table, ("consommation", "entre 0", "30"))
    if half_cvd is not None and abs(half_cvd - 0.5 * cvd) > 0.005:
        raise ExtractorError(
            f"inBW first-block rate {half_cvd} is not 0.5×{cvd} (CWaPE residential rule)"
        )

    # Cross-check the redevance: should equal 20·CVD.
    redevance_cvd_text = None
    for tr in table.find_all("tr"):
        text = tr.get_text(" ", strip=True).lower()
        if re.search(r"redevance.*20\s*[x×*]\s*cvd", text):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) >= 4:
                amts = extract_amounts(cells[3])  # Hors TVA total
                if amts:
                    redevance_cvd_text = amts[0]
            break
    if redevance_cvd_text is not None and abs(redevance_cvd_text - 20.0 * cvd) > 0.05:
        raise ExtractorError(
            f"inBW redevance {redevance_cvd_text} does not equal 20·CVD ({20 * cvd:.2f})"
        )

    # Drift checks against the SPGE flat-Wallonia constants. Both values
    # appear in the table (CVA in the "30 x CVA" row's Prix unitaire,
    # FSE in the "Fonds Social" row's Prix unitaire). The redevance cell
    # shows 30 x CVA, not the CVA itself. A moved CVA fails the fetch like
    # a moved FSE does; it used to log and price on the old figure.
    cva_row = _row_amount_after_label(table, ("redevance", "30", "cva"))
    hold_to_constant(
        published=cva_row / 30.0 if cva_row is not None else None,
        constant=WALLONIA_CVA_EUR_PER_M3,
        label="inBW CVA",
        logger=_LOGGER,
    )
    warn_constant_drift(
        published=_row_amount_after_label(table, ("fonds social",)),
        constant=WALLONIA_FSE_EUR_PER_M3,
        label="inBW FSE",
        logger=_LOGGER,
        threshold=0.001,
    )

    # The page says "Tarifs YYYY": date the card from that rather than the
    # clock, so a page still on last year's card in January looks stale
    # instead of being relabelled as this year's.
    target = year or detect_published_year(soup.get_text(" ", strip=True)) or belgian_today().year
    return build_tariff(
        utility_id=UTILITY_ID,
        cvd=cvd,
        source_url=SOURCE_URL,
        publication_label=f"inBW prix de l'eau {target}",
        year=target,
    )


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    # Try with TLS verification first so a future server-side fix
    # (inBW shipping the GoDaddy intermediate, or migrating to a CA
    # whose chain is complete) is detectable. Fall back to
    # verify_ssl=False ONLY on a TLS-specific failure -- a transient
    # 5xx, DNS blip or timeout must not silently downgrade the
    # connection (otherwise the whole 'verify first' point evaporates
    # and an on-path attacker just needs to nudge the first request
    # toward any non-cert failure to trigger the no-verify retry).
    #
    # TLS issues can surface at two layers under aiohttp:
    #   - handshake-time:  ClientConnectorCertificateError, ClientSSLError
    #   - underlying:      ssl.SSLError raised from the asyncio layer
    #                      and surfaced via __cause__ chains
    #
    # ClientPayloadError is deliberately NOT in this set: it covers
    # any mid-body interruption (decompression failures, malformed
    # Transfer-Encoding, server reset for whatever reason) and only
    # rarely is a TLS signal. Treating it as TLS would let any
    # payload-layer failure trigger the verify_ssl=False retry, which
    # is exactly the on-path-attacker hint the 'verify first'
    # invariant exists to prevent.
    try:
        html = await fetch_html(session, SOURCE_URL)
    except ExtractorError as err:
        cause = err.__cause__
        is_tls = isinstance(
            cause,
            aiohttp.ClientConnectorCertificateError | aiohttp.ClientSSLError | ssl.SSLError,
        )
        if not is_tls:
            raise
        _LOGGER.warning(
            "inBW TLS verification failed (%s); falling back to verify_ssl=False",
            err,
        )
        html = await fetch_html(session, SOURCE_URL, verify_ssl=False)
    return await asyncio.to_thread(parse_tariff, html)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_WALLONIA,
    fetch=fetch,
)
