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

"""energie.be gas tariff card extractor.

energie.be sells two residential gas products, in Flanders only, each on a
one-year term: Gas particulier online (variable) and Gas vast particulier
online (fixed). Neither card has a document key of its own. The contracts
endpoint the site itself reads names the current card of each product:

    https://www.energie.be/api/v1/data/contracts
        contracts[tariffType == "Variable" | "Fixed"].contractTypeNgRes.tariffDocument

(contractTypeElRes is the electricity card). The Dynamic contract has no gas
card: the site says a gas contract beside it is variable.

The archive is a second endpoint, one row per month with its gas card:

    https://www.energie.be/api/v1/data/tariff-cards
        ?isProfessional=false&tariffType=<Variable|Fixed>
        tariffCards[date == "YYYY/MM"].gasDocument

It is published in arrears, so the running month is never on it. Rows go
back to November 2023, but the cards of January to November 2025 are page
images without a text layer and the older ones print the Fluvius areas that
no longer exist, so the readable archive starts at December 2025.

The variable card bills the delivery month at (factor x TTF_RLP + base)
c EUR/kWh excluding VAT, TTF_RLP being that month's RLP-weighted TTF
day-ahead mean in c EUR/kWh, so it is only known once the month is over. The
factor moves from card to card (1,025 in August 2026, 1,014 in September),
which is why a cohort's own card matters. The printed price is the formula at
a VNR estimate of the index ("Weergegeven prijs op basis van de ingeschatte
index (VNR methodologie): 6,24 c EUR/kWh"), not at a known value.

energie.be publishes the realised TTF_RLP month by month in its indexation
parameters document, which the document key ``?key=Indexation`` redirects to.

Every figure on the card is VAT inclusive ("Alle prijzen zijn inclusief btw
tenzij anders vermeld") except the formula, and the card never states the
rate. The formula is grossed by the residential rate the law sets, which is
what reproduces the price the card prints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

import aiohttp

from ..const import REGION_FLANDERS, VAT_RATE_REDUCED
from ._network import (
    FLUVIUS_LABELS,
    METERING,
    T1_FIXED,
    T1_PROP,
    T2_FIXED,
    T2_PROP,
    TRANSPORT,
    excise_bands,
    read_dsos,
    require_region,
)
from ._parse import SIGN_CHARS, fold_accents, month_date, parse_sign, require_contract, to_float
from ._pdf import (
    MONTH_NAMES,
    fetch_pdf_text,
    fetch_pdf_text_layout,
    fetch_text,
    parse_json,
)
from ._rates import Contract, FixedRates, IndexedRates, TariffKind
from ._validity import end_of_month, month_card
from .base import (
    DsoOverlay,
    ExtractorError,
    IndexTable,
    SupplierExtractor,
    SupplierSnapshot,
    TaxOverlay,
)

_CONTRACTS_URL = "https://www.energie.be/api/v1/data/contracts"
_ARCHIVE_URL = "https://www.energie.be/api/v1/data/tariff-cards"
_INDEX_URL = "https://www.energie.be/api/v1/data/document?key=Indexation"

# The index the variable card names, and the name fetch_index files it under.
_INDEX = "TTF_RLP"

_REGIONS = frozenset({REGION_FLANDERS})


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    kind: TariffKind
    tariff_type: str  # the endpoints' tariffType


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("energiebe_variable", "energie.be Gas particulier online", "indexed", "Variable"),
    _ContractDef("energiebe_fixed", "energie.be Gas vast particulier online", "fixed", "Fixed"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _json(body: str, what: str) -> dict[str, Any]:
    """The endpoint's answer as a JSON object, or raise."""
    payload = parse_json(body, f"energie.be: {what}")
    if not isinstance(payload, dict):
        raise ExtractorError(f"energie.be: {what} is not a JSON object")
    return payload


def _https(value: object) -> str | None:
    return value if isinstance(value, str) and value.startswith("https://") else None


async def _current_card_url(session: aiohttp.ClientSession, contract: _ContractDef) -> str:
    payload = _json(await fetch_text(session, _CONTRACTS_URL), "contracts endpoint")
    rows = payload.get("contracts")
    for row in rows if isinstance(rows, list) else ():
        if not isinstance(row, dict) or row.get("tariffType") != contract.tariff_type:
            continue
        gas = row.get("contractTypeNgRes")
        url = _https(gas.get("tariffDocument")) if isinstance(gas, dict) else None
        if url is not None:
            return url
    raise ExtractorError(f"energie.be: no {contract.tariff_type} gas card in the contracts list")


async def _archive_card_url(
    session: aiohttp.ClientSession, contract: _ContractDef, year_month: date
) -> str | None:
    """The archived gas card of ``year_month``, or None when the archive
    lists no such month."""
    body = await fetch_text(
        session,
        _ARCHIVE_URL,
        params={"isProfessional": "false", "tariffType": contract.tariff_type},
    )
    rows = _json(body, "tariff card archive").get("tariffCards")
    if not isinstance(rows, list):
        raise ExtractorError("energie.be: tariff card archive has no tariffCards list")
    wanted = f"{year_month.year:04d}/{year_month.month:02d}"
    for row in rows:
        if isinstance(row, dict) and row.get("date") == wanted:
            return _https(row.get("gasDocument"))
    return None


def _region(region: str) -> None:
    if region != REGION_FLANDERS:
        raise ExtractorError(f"energie.be: gas is not sold in region {region!r}")


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The current card for ``contract_id``."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "energie.be")
    _region(region)
    return await _read(session, contract_id, region, await _current_card_url(session, contract))


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(
        contract_id, region, await fetch_pdf_text_layout(session, url), source_url=url
    )


async def _read_month(
    session: aiohttp.ClientSession, contract: _ContractDef, region: str, year_month: date
) -> SupplierSnapshot | None:
    url = await _archive_card_url(session, contract, year_month)
    if url is None:
        return None
    return await _read(session, contract.contract_id, region, url)


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card energie.be published for a past month, or None.

    The archive is keyed by month, so no clock is involved. A month it does
    not list, a card without a text layer and a card of another layout are
    all a month with no card; only a transient failure raises, so the month
    cache retries it. A card naming another month than its row is refused.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region != REGION_FLANDERS:
        return None
    return await month_card(_read_month(session, contract, region, year_month), year_month)


def parse_snapshot(
    contract_id: str, region: str, text: str, *, source_url: str = _CONTRACTS_URL
) -> SupplierSnapshot:
    """Parse one card's text as pdfplumber lays it out."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "energie.be")
    _region(region)
    card_month = _card_month(text, contract)
    energy = _fixed(text) if contract.kind == "fixed" else _indexed(text)
    return SupplierSnapshot(
        supplier="energiebe",
        contract=contract_id,
        energy=energy,
        dsos=_dsos(text),
        taxes=TaxOverlay(
            excise_bands=_excise(text),
            energy_contribution=_energy_contribution(text),
            card_vat_rate=None,
        ),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


# "Gas particulier online – september 2026", "Gas vast particulier online –
# september 2026"; the December 2025 cards leave out "online". The word
# "vast" is the only thing on the page naming the product, so it is checked
# against the contract asked for.
_TITLE_RE = re.compile(
    r"^Gas\s+(vast\s+)?particulier(?:\s+online)?\s*[" + SIGN_CHARS + r"]\s*([a-z]+)\s+(\d{4})\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _card_month(text: str, contract: _ContractDef) -> date:
    match = _TITLE_RE.search(text)
    month = MONTH_NAMES.get(fold_accents(match.group(2))) if match else None
    if match is None or month is None:
        raise ExtractorError("energie.be: card title not found")
    if bool(match.group(1)) != (contract.kind == "fixed"):
        raise ExtractorError(f"energie.be: card {match.group(0).strip()!r} is not {contract.label}")
    return month_date(match.group(3), month, "energie.be")


# The price sits alone at the start of the line under the "Energieprijs"
# heading, before the formula (variable) or the fixed-price sentence.
_PRICE_RE = re.compile(r"^Energieprijs[ \t]*\n[ \t]*(\d+,\d+)\s", re.MULTILINE)
_FEE_RE = re.compile(
    r"^Vaste vergoeding[ \t]*\n[ \t]*(\d+(?:,\d+)?)[ \t]*\n[ \t]*\(€/jaar\)", re.MULTILINE
)
_FORMULA_RE = re.compile(
    r"formule\s*\(excl\.\s*btw\)\s*:\s*\(\s*(\d+,\d+)\s*x\s*TTF_RLP\s*"
    r"([" + SIGN_CHARS + r"])\s*(\d+,\d+)\s*\)\s*c€/kWh"
)
_FIXED_RE = re.compile(r"De energieprijs is een vaste prijs")


def _price_and_fee(text: str) -> tuple[float, float]:
    price = _PRICE_RE.search(text)
    fee = _FEE_RE.search(text)
    if price is None or fee is None:
        raise ExtractorError("energie.be: energy price or fixed fee not found")
    return to_float(price.group(1)) / 100.0, to_float(fee.group(1))


def _fixed(text: str) -> FixedRates:
    # The variable card is the one that prints a formula; a fixed contract
    # served it would bill an estimate as a fixed price.
    if _FORMULA_RE.search(text) or not _FIXED_RE.search(text):
        raise ExtractorError("energie.be: fixed card does not state a fixed price")
    price, fee = _price_and_fee(text)
    return FixedRates(price=price, yearly_fixed_fee=fee)


def _indexed(text: str) -> IndexedRates:
    formula = _FORMULA_RE.search(text)
    if formula is None:
        raise ExtractorError("energie.be: variable card formula not found")
    price, fee = _price_and_fee(text)
    # The card states no VAT rate; the residential one the law sets is what
    # reproduces its printed price.
    vat = 1.0 + VAT_RATE_REDUCED
    # TTF_RLP in c EUR/kWh is the index in EUR/MWh over 10, and the formula
    # yields c EUR/kWh: factor / 1000 per EUR/MWh, base / 100, both grossed.
    base = parse_sign(formula.group(2)) * to_float(formula.group(3))
    return IndexedRates(
        factor=to_float(formula.group(1)) / 1000.0 * vat,
        base=base / 100.0 * vat,
        index=_INDEX,
        price=price,
        yearly_fixed_fee=fee,
        formula=formula.group(0),
    )


# "Netbeheerder | Klein verbruik Variabel, Vast | Gemiddeld verbruik
# Variabel, Vast | Transportkosten | Databeheer": proportional before fixed
# within each tier, transport in c EUR/kWh on every row.
_COLUMNS = (T1_PROP, T1_FIXED, T2_PROP, T2_FIXED, TRANSPORT, METERING)


def _dsos(text: str) -> dict[str, DsoOverlay]:
    dsos = read_dsos(
        text,
        FLUVIUS_LABELS,
        _COLUMNS,
        supplier="energie.be",
        after="Nettarieven",
        before="Taksen en heffingen",
    )
    require_region(dsos, REGION_FLANDERS, "energie.be")
    return dsos


_EXCISE_RE = re.compile(
    r"Bijzondere accijns op Energie \(c€/kWh\) (kleiner|groter) dan 12\.000\s*kWh\s+(\d+,\d+)"
)
# "0" on the current cards, "0, 1058" (a stray space in the figure) on the
# ones from before August 2026.
_CONTRIBUTION_RE = re.compile(
    r"Bijdrage op de Energie \(c€/kWh\)\s+(\d+(?:,\s?\d+)?)\s*$", re.MULTILINE
)


def _excise(text: str) -> tuple[tuple[float | None, float], ...]:
    rates = {m.group(1): to_float(m.group(2)) / 100.0 for m in _EXCISE_RE.finditer(text)}
    if set(rates) != {"kleiner", "groter"}:
        raise ExtractorError("energie.be: federal excise rows not found")
    return excise_bands(rates["kleiner"], rates["groter"])


def _energy_contribution(text: str) -> float:
    match = _CONTRIBUTION_RE.search(text)
    if match is None:
        raise ExtractorError("energie.be: energy contribution row not found")
    return to_float(match.group(1)) / 100.0


# ---- index values ------------------------------------------------------------

_YEAR_RE = re.compile(r"20\d{2}")
_VALUE_RE = re.compile(r"\d+,\d+")


def parse_index_document(text: str) -> IndexTable:
    """The TTF_RLP table of the indexation document, in EUR/MWh.

    Read as pypdf extracts it, which keeps every figure whole where
    pdfplumber splits some ("11,2 1"). The table comes out one cell per line:
    the year headings, then each month name followed by its values, one per
    year from the oldest. A month the latest year has not reached yet is
    simply shorter, so the values fill the years from the left.
    """
    start = text.find("TTF_RLP (c€/kWh)")
    if start < 0:
        raise ExtractorError("energie.be: TTF_RLP table not found")
    end = text.find("Belpex_SPP", start)
    tokens = text[start + len("TTF_RLP (c€/kWh)") : end if end >= 0 else None].split()
    years: list[str] = []
    while tokens and _YEAR_RE.fullmatch(tokens[0]):
        years.append(tokens.pop(0))
    values: dict[str, float] = {}
    month: int | None = None
    column = 0
    for token in tokens:
        name = MONTH_NAMES.get(token.lower())
        if name is not None:
            month, column = name, 0
            continue
        if month is None or not _VALUE_RE.fullmatch(token) or column >= len(years):
            raise ExtractorError(f"energie.be: unexpected {token!r} in the TTF_RLP table")
        # c EUR/kWh to EUR/MWh.
        values[f"{years[column]}-{month:02d}"] = to_float(token) * 10.0
        column += 1
    if not values:
        raise ExtractorError("energie.be: TTF_RLP table is empty")
    return {_INDEX: values}


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """energie.be's published TTF_RLP values."""
    return parse_index_document(await fetch_pdf_text(session, _INDEX_URL))


EXTRACTOR = SupplierExtractor(
    id="energiebe",
    label="energie.be",
    contracts=tuple(
        Contract(id=c.contract_id, label=c.label, kind=c.kind, regions=_REGIONS) for c in _CONTRACTS
    ),
    fetch=fetch,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=7.0,
)
