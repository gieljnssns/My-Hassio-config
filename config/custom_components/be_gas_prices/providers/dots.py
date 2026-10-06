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

"""Dots Energy gas card extractor.

Dots Energy sells one residential gas product, Connect - Digital, in
Flanders. Its product page https://www.dotsenergy.be/dots-connect-gas-digital
links the current card as an Odoo attachment,
``/web/content/<id>?unique=<checksum>&download=true``. No archive of past
cards was found. The "Dots Internal" card is reserved for Dots's own staff
and needs Dots's approval, so it is not a product a household can choose and
is not read.

The energy price is VariableRates, not IndexedRates, because the card does
not say which index it is on. The formula line reads "Gas 1,05 * M ZTP rek.
gem. EGSI EEX + 0,9" (c EUR/kWh), which reads as the monthly arithmetic
mean of EEX's ZTP spot index (EGSI), under a price column headed "M-1 *".
The footnote to that
star defines the M-1 price as the mean of the "EEX Gas Futures Month Base
ZTP" settlement prices in the month before delivery, a month-ahead price,
and the next paragraph defines "ZTP rekendig gemiddelde" as the mean of
day-ahead ZTP prices weighted by metered consumption, while the same
footnote says the prices are "exclusief volumeweging". Dots publishes no
index values either. The printed price is kept as the card gives it,
VAT inclusive by the card's own statement, and the formula only for
diagnostics.

Some cells of the September 2026 distribution table are wrong: Limburg's
mid tier prints its small tier's 2,240 c EUR/kWh where Engie and Sparki
print 0,983 (the regulator's 0,98293), and the T3 proportional terms of
Halle-Vilvoorde, Kempen and Midden-Vlaanderen repeat their T2 value
(0,980, 0,882, 0,910 against 0,621, 0,552, 0,577 elsewhere). Each repeats
the tier before it, which is not degressive, so ``dso_overlay`` drops the
tier with those above it.
"""

from __future__ import annotations

import html
import re
from datetime import date

import aiohttp

from ..const import REGION_FLANDERS
from ._network import (
    FLUVIUS_LABELS,
    METERING,
    T1_FIXED,
    T1_PROP,
    T2_FIXED,
    T2_PROP,
    T3_FIXED,
    T3_PROP,
    TRANSPORT,
    excise_bands,
    read_dsos,
    require_region,
)
from ._parse import require_contract, to_float
from ._pdf import NL_MONTHS, fetch_pdf_text, fetch_text, printed_vat_rate
from ._rates import Contract, VariableRates
from ._validity import end_of_month
from .base import ExtractorError, SupplierExtractor, SupplierSnapshot, TaxOverlay

_HOST = "https://www.dotsenergy.be"
_PRODUCT_PAGE = f"{_HOST}/dots-connect-gas-digital"

_CONTRACT_ID = "dots_connect_digital"
_CONTRACTS = {_CONTRACT_ID: "Dots Connect - Digital"}

_CARD_LINK_RE = re.compile(r'href="(/web/content/\d+\?[^"]*)"')


def card_path(page: str) -> str:
    """The one attachment the product page links."""
    paths = {html.unescape(path) for path in _CARD_LINK_RE.findall(page)}
    if len(paths) != 1:
        raise ExtractorError(f"Dots Energy: product page links {len(paths)} cards")
    return paths.pop()


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The card the product page links today."""
    _check(contract_id, region)
    url = _HOST + card_path(await fetch_text(session, _PRODUCT_PAGE))
    return parse_snapshot(contract_id, region, await fetch_pdf_text(session, url), url)


def _check(contract_id: str, region: str) -> None:
    require_contract(_CONTRACTS, contract_id, "Dots Energy")
    if region != REGION_FLANDERS:
        raise ExtractorError(f"Dots Energy {contract_id}: not sold in region {region!r}")


_MONTHS = "|".join(NL_MONTHS)
_CARD_MONTH_RE = re.compile(rf"Tariefkaart\s+({_MONTHS})\s+(20\d{{2}})\b", re.IGNORECASE)
_PRODUCT_TEXT = "Dots: Gas Connect - Digital"
_REGION_TEXT = "residentiële klanten in het Vlaamse Gewest"
_VAT_RE = r"inclusief\s+(\d+)\s*%\s*BTW"
# "Gas 1,05 * M ZTP rek. gem. EGSI EEX + 0,9 7,873": the formula up to its
# adder, then the price. Anchored on the adder, so a price wrapped onto the
# next line refuses the card rather than reading the 0,9 as the price.
_PRICE_RE = re.compile(
    r"^Gas[ \t]+(\S.*ZTP.*\+[ \t]*\d+(?:,\d+)?)[ \t]+(\d+,\d+)[ \t]*$", re.MULTILINE
)
_FEE_RE = re.compile(r"€\s*(\d+(?:,\d+)?)\s*/maand/EAN")
# pypdf breaks some tax figures around their comma ("0, 10577", "1 ,093").
_FIGURE = r"\s+(\d+ ?, ?\d+)"
_CONTRIBUTION_RE = re.compile(r"Energiebijdrage" + _FIGURE)
_EXCISE_LOW_RE = re.compile(r"Verbruik tussen 0 & 12\.000 kWh" + _FIGURE)
_EXCISE_HIGH_RE = re.compile(r"Verbruik > 12\.000 kWh" + _FIGURE)

# Per tier the fixed term then the proportional one, then data management and
# transport.
_COLUMNS = (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, METERING, TRANSPORT)


def _card_month(text: str) -> date:
    match = _CARD_MONTH_RE.search(text)
    if match is None:
        raise ExtractorError("Dots Energy: card month not found")
    return date(int(match.group(2)), NL_MONTHS.index(match.group(1).lower()) + 1, 1)


def _energy(text: str) -> VariableRates:
    """The M-1 price and the monthly fee: "Gas 1,05 * M ZTP rek. gem. EGSI EEX
    + 0,9 7,873" and "€5,3/maand/EAN"."""
    price = _PRICE_RE.search(text)
    fee = _FEE_RE.search(text)
    if price is None or fee is None:
        raise ExtractorError("Dots Energy: price or fee not found")
    return VariableRates(
        price=to_float(price.group(2)) / 100.0,
        yearly_fixed_fee=to_float(fee.group(1)) * 12.0,
        formula=price.group(1),
    )


def _taxes(text: str, vat_rate: float) -> TaxOverlay:
    contribution = _CONTRIBUTION_RE.search(text)
    low = _EXCISE_LOW_RE.search(text)
    high = _EXCISE_HIGH_RE.search(text)
    if contribution is None or low is None or high is None:
        raise ExtractorError("Dots Energy: excise or energy contribution not found")
    return TaxOverlay(
        excise_bands=excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0),
        energy_contribution=to_float(contribution.group(1)) / 100.0,
        card_vat_rate=vat_rate,
    )


def parse_snapshot(contract_id: str, region: str, text: str, source_url: str) -> SupplierSnapshot:
    """Parse the card's text as pypdf extracts it."""
    _check(contract_id, region)
    if _PRODUCT_TEXT not in text or _REGION_TEXT not in text:
        raise ExtractorError("Dots Energy: card is not the Flemish Connect - Digital card")
    vat_rate = printed_vat_rate(text, _VAT_RE)
    if vat_rate is None:
        raise ExtractorError("Dots Energy: VAT statement not found")
    dsos = read_dsos(text, FLUVIUS_LABELS, _COLUMNS, supplier="Dots Energy")
    require_region(dsos, region, "Dots Energy")
    card_month = _card_month(text)
    return SupplierSnapshot(
        supplier="dots",
        contract=contract_id,
        energy=_energy(text),
        dsos=dsos,
        taxes=_taxes(text, vat_rate),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


EXTRACTOR = SupplierExtractor(
    id="dots",
    label="Dots Energy",
    contracts=(
        Contract(
            id=_CONTRACT_ID,
            label=_CONTRACTS[_CONTRACT_ID],
            kind="variable",
            regions=frozenset({REGION_FLANDERS}),
        ),
    ),
    fetch=fetch,
    sweep_cost_s=0.5,
)
