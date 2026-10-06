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

"""Sparki gas card extractor.

Sparki lists its cards on https://sparki.be/elektriciteit-gas/tariefkaarten/,
newest month first, as WordPress uploads:

    https://sparki.be/wp-content/uploads/<YYYY>/<MM>/
        Sparki_Tariefkaart_<month>_Particulier_<SelfService|AtYourService>_Gas_<NL|FR>.pdf

with the Dutch month name on both languages and no year. The upload folder
is not the price month (the April to June cards were uploaded in July), so
the card is found on the listing and dated by its own text. The listing keeps
every month since April 2026, which makes it the archive. The NL card is for
Flanders, the FR card for Wallonia; there is no Brussels card.

The energy price is VariableRates, not IndexedRates. The formula
"((0,105*TTF)+0,8)*1,06" (c EUR/kWh, VAT inclusive) never says which TTF it
means: neither the card, the general conditions (which defer to the card)
nor the site name the assessment, the averaging or the month (from October
2026 the card names "TTF EGSI EEX DA", an EEX index), and Sparki publishes no
index values. The printed "Geschatte maandprijs" is not a
month's settled value either. The NL card says it is based on the VNR
methodology and prints the value used, "6,24 c€/kWh": 62,4 EUR/MWh gives the
printed 7,79, and is the figure the Energy Together cards' twelve-month VNR
estimate implies for the same month. So the card's price is kept as printed
and the formula only for diagnostics.

The NL card also says "Onbalanskosten en transportkosten voor gas zijn in de
prijs inbegrepen" while its network table prints the Fluxys transport rate;
the table is read as printed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import aiohttp

from ..const import DSO_RESA, REGION_FLANDERS, REGION_WALLONIA
from ._network import (
    FLUVIUS_LABELS,
    METERING,
    ORES_LABELS,
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
from ._parse import fold_accents, require_contract, to_float
from ._pdf import (
    MONTH_NAMES,
    NL_MONTHS,
    fetch_pdf_text_layout,
    fetch_text,
    is_transient_fetch_error,
    printed_vat_rate,
)
from ._rates import Contract, VariableRates
from ._validity import end_of_month, future_month, month_card
from .base import DsoOverlay, ExtractorError, SupplierExtractor, SupplierSnapshot, TaxOverlay

_LISTING_URL = "https://sparki.be/elektriciteit-gas/tariefkaarten/"

_LANGUAGE = {REGION_FLANDERS: "NL", REGION_WALLONIA: "FR"}
# How each card says which region it is for.
_REGION_TEXT = {
    REGION_FLANDERS: "particulieren in Vlaanderen",
    REGION_WALLONIA: "particuliers en Wallonie",
}


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    product: str  # as the card names it
    file: str  # as the file name spells it


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("sparki_self_service", "Sparki Self Service", "Self Service", "SelfService"),
    _ContractDef(
        "sparki_at_your_service", "Sparki At Your Service", "At Your Service", "AtYourService"
    ),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def listed_cards(page: str, contract: _ContractDef, region: str) -> list[tuple[str, str]]:
    """(month name, URL) of every card of the listing for this product and
    region, in the listing's order."""
    pattern = (
        r'href="(https://sparki\.be/wp-content/uploads/\d{4}/\d{2}/Sparki_Tariefkaart_([a-z]+)'
        rf'_Particulier_{contract.file}_Gas_{_LANGUAGE[region]}\.pdf)"'
    )
    seen: set[str] = set()
    cards: list[tuple[str, str]] = []
    for url, month in re.findall(pattern, page):
        if url not in seen:
            seen.add(url)
            cards.append((month, url))
    return cards


def _contract(contract_id: str, region: str) -> _ContractDef:
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Sparki")
    if region not in _LANGUAGE:
        raise ExtractorError(f"Sparki {contract_id}: not sold in region {region!r}")
    return contract


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The newest card the listing links for the product and region."""
    contract = _contract(contract_id, region)
    cards = listed_cards(await fetch_text(session, _LISTING_URL), contract, region)
    if not cards:
        raise ExtractorError(f"Sparki: no {contract.file} {_LANGUAGE[region]} gas card listed")
    return await _read(session, contract_id, region, cards[0][1])


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(contract_id, region, await fetch_pdf_text_layout(session, url), url)


async def _read_month(
    session: aiohttp.ClientSession, contract: _ContractDef, region: str, year_month: date
) -> SupplierSnapshot | None:
    name = NL_MONTHS[year_month.month - 1]
    wanted = end_of_month(year_month.year, year_month.month)
    for month, url in listed_cards(await fetch_text(session, _LISTING_URL), contract, region):
        if month != name:
            continue
        try:
            snapshot = await _read(session, contract.contract_id, region, url)
        except ExtractorError as err:
            if is_transient_fetch_error(str(err)):
                raise
            # Another year's card of the same name that cannot be read: the
            # one asked for may still be further down the listing.
            continue
        if snapshot.valid_until == wanted:
            return snapshot
    return None


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card the listing links for a past month, or None.

    The file name gives the month but not the year, so every card named
    after the month is read until one is dated ``year_month``. A month ahead
    of today in Home Assistant's zone is not asked for. A transient failure
    raises so the month cache retries it; any other failure is a month with
    no card.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region not in _LANGUAGE:
        return None
    if future_month(year_month):
        return None
    return await month_card(_read_month(session, contract, region, year_month), year_month)


_CARD_MONTH_RE = re.compile(
    r"(?:tariefkaart|carte tarifaire)\s+(?:gas\s+|gaz\s+)?([a-z]+)\s+(20\d{2})\b"
)


def _card_month(text: str) -> date:
    """ "Tariefkaart september 2026" or "Carte tarifaire septembre 2026", and
    from October 2026 "Tariefkaart gas oktober 2026" or "Carte tarifaire gaz
    octobre 2026"."""
    match = _CARD_MONTH_RE.search(fold_accents(text))
    month = MONTH_NAMES.get(match.group(1)) if match else None
    if match is None or month is None:
        raise ExtractorError("Sparki: card month not found")
    return date(int(match.group(2)), month, 1)


_PRODUCT_RE = re.compile(r"produ(?:ct|it)\s*“([^”]+)”")
_VAT_PATTERNS = (r"inclusief\s+(\d+)\s*%\s*BTW", r"TVA\s+(\d+)\s*%\s*comprise")
_PRICE_RE = re.compile(
    r"^(\d+,\d+)\s+(\d+,\d+)\s+(?:Geschatte maandprijs|Prix mensuel estimé)", re.MULTILINE
)
# "((0,105*TTF)+0,8)*1,06.", from October 2026 "((0,105* TTF EGSI EEX DA)+0,8)
# *1,06.": up to the full stop.
_FORMULA_RE = re.compile(r"formule\s+(\S.*?TTF.*?)\.(?:\s|$)")


def _energy(text: str) -> VariableRates:
    """The fee and the estimated monthly price: "21,20 7,79 Geschatte maandprijs"."""
    price = _PRICE_RE.search(text)
    formula = _FORMULA_RE.search(text)
    if price is None or formula is None:
        raise ExtractorError("Sparki: price or formula not found")
    return VariableRates(
        price=to_float(price.group(2)) / 100.0,
        yearly_fixed_fee=to_float(price.group(1)),
        formula=formula.group(1),
    )


_FIGURE = r"\s+(\d+[.,]\d+)"
_CONTRIBUTION_RE = re.compile(
    r"(?:Bijdrage op de Energie|Cotisation sur l.énergie) \(c€/kWh\)" + _FIGURE
)
_EXCISE_LOW_RE = re.compile(r"(?:Verbruik tussen|Consommation entre) 0 & 12\.000 kWh" + _FIGURE)
_EXCISE_HIGH_RE = re.compile(r"(?:Verbruik|Consommation) > 12\.000 kWh" + _FIGURE)
_CONNECTION_FEE_RE = re.compile(r"Redevance raccordement" + _FIGURE)


def _taxes(text: str, region: str, vat_rate: float) -> TaxOverlay:
    """The levies, in c EUR/kWh on the card. The high excise band is printed
    with a decimal point ("0.9864")."""
    contribution = _CONTRIBUTION_RE.search(text)
    low = _EXCISE_LOW_RE.search(text)
    high = _EXCISE_HIGH_RE.search(text)
    if contribution is None or low is None or high is None:
        raise ExtractorError("Sparki: excise or energy contribution not found")
    connection_fee = 0.0
    if region == REGION_WALLONIA:
        fee = _CONNECTION_FEE_RE.search(text)
        if fee is None:
            raise ExtractorError("Sparki: Walloon connection fee row not found")
        connection_fee = to_float(fee.group(1)) / 100.0
    return TaxOverlay(
        excise_bands=excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0),
        energy_contribution=to_float(contribution.group(1)) / 100.0,
        connection_fee=connection_fee,
        card_vat_rate=vat_rate,
    )


# Per tier the fixed term then the proportional one, then Flanders's data
# management and transport.
_COLUMNS: dict[str, tuple[str, ...]] = {
    REGION_FLANDERS: (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, METERING, TRANSPORT),
    REGION_WALLONIA: (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, TRANSPORT),
}
_LABELS: dict[str, dict[str, str]] = {
    REGION_FLANDERS: FLUVIUS_LABELS,
    REGION_WALLONIA: {**ORES_LABELS, "TECTEO - RESA": DSO_RESA},
}


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    dsos = read_dsos(text, _LABELS[region], _COLUMNS[region], supplier="Sparki")
    require_region(dsos, region, "Sparki")
    return dsos


def parse_snapshot(contract_id: str, region: str, text: str, source_url: str) -> SupplierSnapshot:
    """Parse one card's text as pdfplumber lays it out.

    The card names its product and region in its validity sentence ("geldig
    voor het product “Self Service” ... aan particulieren in Vlaanderen"); a
    card for another one is refused.
    """
    contract = _contract(contract_id, region)
    product = _PRODUCT_RE.search(text)
    # "Self Service" until September 2026, "Self service" from October.
    if product is None or product.group(1).casefold() != contract.product.casefold():
        raise ExtractorError(f"Sparki: card is not for {contract.product!r}")
    if _REGION_TEXT[region] not in text:
        raise ExtractorError(f"Sparki: card is not for {region}")
    vat_rate = printed_vat_rate(text, *_VAT_PATTERNS)
    if vat_rate is None:
        raise ExtractorError("Sparki: VAT statement not found")
    card_month = _card_month(text)
    return SupplierSnapshot(
        supplier="sparki",
        contract=contract_id,
        energy=_energy(text),
        dsos=_dsos(text, region),
        taxes=_taxes(text, region, vat_rate),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


EXTRACTOR = SupplierExtractor(
    id="sparki",
    label="Sparki",
    contracts=tuple(
        Contract(
            id=c.contract_id,
            label=c.label,
            kind="variable",
            regions=frozenset(_LANGUAGE),
        )
        for c in _CONTRACTS
    ),
    fetch=fetch,
    fetch_for_month=fetch_for_month,
    sweep_cost_s=2.0,
)
