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

"""Ecofix Gas & Power gas tariff card extractor.

Ecofix publishes one card per product at a stable URL, overwritten in place
every month:

    https://portal.ecofixgp.be/docs/prices/current/GAS_Ecofix_<Product>_NL.pdf

The Dutch card prints the Flemish and the Walloon tables both, so it is read
for either region; the French twin carries the same figures.

Since August 2026 the cards are page images: the text layer holds the month,
the monthly and yearly prices and the fee, and nothing else, so the reader
refuses the card as unreadable (``CardNotReadableError``). The card archive
reads it with the OCR engine every day and files the result as an ordinary
row, and an entry prices on that row. This module parses the text the engine
hands back, which is shaped like pdfplumber's: taken from its trusted text, a
line holding a mark the engine refused is left out, so a mandatory figure is
read whole or missing and the parse fails. The title is one such line (the
export clips the descender of the y in Flexy), so the product is the one the
URL names.

The formula indexes on TTF-RLP-M, the arithmetic mean of the delivery
month's day-ahead and weekend TTF assessments (EGSI) as EEX publishes them.
Ecofix publishes no values of its own, and EEX's terms forbid reuse, so there
is no index table: every month is priced at the "Maandprijs" its card prints,
and marked provisional.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import aiohttp

from ..const import REGION_FLANDERS, REGION_WALLONIA
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
from ._parse import require_contract, to_float
from ._pdf import NL_MONTHS, fetch_pdf_text_layout, head_freshness_key, printed_vat_rate
from ._rates import Contract, IndexedRates
from ._validity import end_of_month
from .base import DsoOverlay, ExtractorError, SupplierExtractor, SupplierSnapshot, TaxOverlay

_BASE_URL = "https://portal.ecofixgp.be/docs/prices/current"
_REGIONS = frozenset({REGION_FLANDERS, REGION_WALLONIA})
_INDEX = "TTF-RLP-M"


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    file: str  # <Product> in the file name


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("ecofix_flexy", "Ecofix Flexy", "Flexy"),
    _ContractDef("ecofix_flexy_online", "Ecofix Flexy Online", "Flexy_Online"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def card_url(contract: _ContractDef) -> str:
    return f"{_BASE_URL}/GAS_Ecofix_{contract.file}_NL.pdf"


def _contract(contract_id: str, region: str) -> _ContractDef:
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Ecofix")
    if region not in _REGIONS:
        raise ExtractorError(f"Ecofix {contract_id}: not sold in region {region!r}")
    return contract


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The current card, which since August 2026 no reader here can read."""
    url = card_url(_contract(contract_id, region))
    return parse_snapshot(contract_id, region, await fetch_pdf_text_layout(session, url), url)


async def probe(session: aiohttp.ClientSession, contract_id: str, region: str) -> str | None:
    """The Last-Modified of the card, which is overwritten in place."""
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region not in _REGIONS:
        return None
    return await head_freshness_key(session, card_url(contract))


def parse_snapshot(contract_id: str, region: str, text: str, source_url: str) -> SupplierSnapshot:
    """Parse the text of one Dutch card for ``region``, a text layer's or
    the OCR engine's trusted text."""
    _contract(contract_id, region)
    month = _card_month(text)
    vat = printed_vat_rate(text, _VAT_RE)
    if vat is None:
        raise ExtractorError("Ecofix: VAT statement not found")
    return SupplierSnapshot(
        supplier="ecofix",
        contract=contract_id,
        energy=_energy(text, 1.0 + vat),
        dsos=_dsos(text, region),
        taxes=TaxOverlay(
            excise_bands=_excise(text),
            energy_contribution=_cents(_CONTRIBUTION_RE, text, "energy contribution"),
            connection_fee=(
                _cents(_CONNECTION_FEE_RE, text, "Walloon connection fee")
                if region == REGION_WALLONIA
                else 0.0
            ),
            card_vat_rate=vat,
        ),
        source_url=source_url,
        publication_label=f"{month:%Y-%m}",
        valid_until=end_of_month(month.year, month.month),
    )


_CARD_MONTH_RE = re.compile(
    r"Variabele prijzen aardgas voor contracten afgesloten in ("
    + "|".join(NL_MONTHS)
    + r") (20\d{2})"
)
_VAT_RE = re.compile(r"Prijzen inclusief (\d+)% BTW")
# The fee in EUR a year, then the monthly price in c EUR/kWh, both VAT
# inclusive: "60,00 + 7,23 Maandprijs". Up to July 2026 the card printed only
# an expected yearly price, and a card without the monthly one is refused.
_PRICE_RE = re.compile(r"^(\d+,\d+) \+ (\d+,\d+) Maandprijs$", re.MULTILINE)
# "Onze tariefformule voor aardgas (excl. btw): (0,1010*TTF-RLP-M) + 0,5200
# c€/kWh", in c EUR/kWh against the index in EUR/MWh.
_FORMULA_RE = re.compile(
    r"tariefformule voor aardgas \(excl\. btw\): \((\d+,\d+)\*" + re.escape(_INDEX) + r"\) "
    r"\+ (\d+,\d+) c€/kWh"
)


def _card_month(text: str) -> date:
    match = _CARD_MONTH_RE.search(text)
    if match is None:
        raise ExtractorError("Ecofix: card month not found")
    return date(int(match.group(2)), NL_MONTHS.index(match.group(1)) + 1, 1)


def _energy(text: str, vat: float) -> IndexedRates:
    price = _PRICE_RE.search(text)
    if price is None:
        raise ExtractorError("Ecofix: fee and monthly price not found")
    formula = _FORMULA_RE.search(text)
    if formula is None:
        raise ExtractorError(f"Ecofix: {_INDEX} formula not found")
    # c EUR/kWh against EUR/MWh, excluding VAT: /100 for EUR, grossed up here.
    return IndexedRates(
        factor=to_float(formula.group(1)) / 100.0 * vat,
        base=to_float(formula.group(2)) / 100.0 * vat,
        index=_INDEX,
        price=to_float(price.group(2)) / 100.0,
        yearly_fixed_fee=to_float(price.group(1)),
        formula=formula.group(0),
        settled=False,
    )


# Per tier the fixed term then the proportional one; then in Flanders the
# data management fee, then transport.
_FLANDERS = (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, METERING, TRANSPORT)
_WALLONIA = (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, TRANSPORT)
_WALLOON_LABELS = {**ORES_LABELS, "TECTO - RESA": "resa"}


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    if region == REGION_FLANDERS:
        dsos = read_dsos(
            text,
            FLUVIUS_LABELS,
            _FLANDERS,
            supplier="Ecofix",
            after="Vlaanderen Distributie",
            before="Wallonië Distributie",
        )
    else:
        dsos = read_dsos(
            text, _WALLOON_LABELS, _WALLONIA, supplier="Ecofix", after="Wallonië Distributie"
        )
    require_region(dsos, region, "Ecofix")
    return dsos


_EXCISE_LOW_RE = re.compile(r"Verbruik tussen 0 & 12\.000 kWh (\d+,\d+)")
_EXCISE_HIGH_RE = re.compile(r"Verbruik groter dan 12\.000 kWh (\d+,\d+)")
_CONTRIBUTION_RE = re.compile(r"Bijdrage op energie (\d+,\d+)")
_CONNECTION_FEE_RE = re.compile(r"Aansluitingsvergoeding (\d+,\d+)")


def _cents(pattern: re.Pattern[str], text: str, what: str) -> float:
    """A figure the card prints in c EUR/kWh, in EUR/kWh."""
    match = pattern.search(text)
    if match is None:
        raise ExtractorError(f"Ecofix: {what} not found")
    return to_float(match.group(1)) / 100.0


def _excise(text: str) -> tuple[tuple[float | None, float], ...]:
    return excise_bands(
        _cents(_EXCISE_LOW_RE, text, "excise up to 12 000 kWh"),
        _cents(_EXCISE_HIGH_RE, text, "excise above 12 000 kWh"),
    )


EXTRACTOR = SupplierExtractor(
    id="ecofix",
    label="Ecofix",
    contracts=tuple(
        Contract(id=c.contract_id, label=c.label, kind="indexed", regions=_REGIONS)
        for c in _CONTRACTS
    ),
    fetch=fetch,
    probe=probe,
    images_only=True,
)
