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

"""Engie Belgium gas tariff card extractor.

Engie publishes the current month's card per (product, region) through the
public document endpoint it uses for electricity:

    https://www.engie.be/api/engie/be/ms/pricing/v1/public/pricesAndConditionsPDF
        ?document=<CODE>&monthOffset=0&segment=R&language=F

A gas code reads ``G_<FAMILY>_R_GREY_C_<F|I>_<MM>_<V|W|B>_F``: every gas
family is GREY, F is fixed and I indexed, MM the contract term in months as
Engie writes it (00 for an open-ended one) and the region letter the regional
card. ``monthOffset`` counts months back, which makes the same endpoint the
archive.

The energy price is identical on the three regional cards; the DSO table and
the levies are not, so the configured region's card is read. Every figure is
6% VAT inclusive; the formula is printed excluding VAT and grossed up here.

Two kinds of variable product:

  - EASY Variable indexes on ZTP101, the average of month-ahead quotes taken
    in the month BEFORE delivery. Its value is known when the card is
    printed, and the card prices the month on it ("ZTP101 (Heren) du mois =
    61,7680 EUR/MWh, d'application pour Septembre 2026"), so its price is
    settled when the month it names is the card's own.
  - FLOW, EMPOWER, DIRECT ONLINE, BASIC ONLINE and the empty-house tariff
    index on ZTPDAM, the mean of the delivery month's day-ahead and weekend
    assessments, known only at month end. Their printed price is the formula
    at the last known value ("Aout 2026: 61,5370 EUR/MWh").

Both indices are published on Engie's indexation page, month by month.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import aiohttp
from homeassistant.util import dt as dt_util

from ..const import REGION_BRUSSELS, REGION_FLANDERS, REGION_WALLONIA
from ._network import (
    FLUVIUS_LABELS,
    METERING,
    ORES_LABELS,
    SKIP,
    T1_FIXED,
    T1_PROP,
    T2_FIXED,
    T2_PROP,
    T3_FIXED,
    T3_PROP,
    TRANSPORT,
    excise_bands,
    osp_table,
    printed_contribution,
    read_dsos,
    require_region,
)
from ._parse import fold_accents, html_rows, month_date, require_contract, to_float
from ._pdf import MONTH_NAMES, fetch_pdf_text, fetch_text
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

_API_URL = "https://www.engie.be/api/engie/be/ms/pricing/v1/public/pricesAndConditionsPDF"
_INDEX_URL = (
    "https://www.engie.be/fr/energie/electricite-gaz/prix-conditions/"
    "parametres-indexation/parametres-indexation-gaz"
)

_REGION_TO_CODE: dict[str, str] = {
    REGION_FLANDERS: "V",
    REGION_WALLONIA: "W",
    REGION_BRUSSELS: "B",
}


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    kind: TariffKind
    family: str
    rate: str  # F (fixed) or I (indexed) in the code
    months_per_region: dict[str, str]


# Every residential gas product on Engie's conditions page. Dynamic has no gas
# card, Basic Online no Brussels one, and the social tariff is set by the CREG
# and assigned rather than chosen, so it is not listed.
_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef(
        "engie_easy_fixed",
        "Engie Easy Fixe",
        "fixed",
        "EASY",
        "F",
        {"V": "12", "W": "12", "B": "36"},
    ),
    _ContractDef(
        "engie_easy_variable",
        "Engie Easy Variable",
        "indexed",
        "EASY",
        "I",
        {"V": "12", "W": "12", "B": "36"},
    ),
    _ContractDef(
        "engie_flow", "Engie Flow", "indexed", "FLOW", "I", {"V": "24", "W": "24", "B": "48"}
    ),
    _ContractDef(
        "engie_direct_online",
        "Engie Direct Online",
        "indexed",
        "DIRECT_ONLINE",
        "I",
        {"V": "12", "W": "12", "B": "36"},
    ),
    _ContractDef(
        "engie_basic_online",
        "Engie Basic Online",
        "indexed",
        "BASIC_ONLINE",
        "I",
        {"V": "24", "W": "24"},
    ),
    _ContractDef(
        "engie_empower_fixed",
        "Engie Empower Fixe",
        "fixed",
        "EMPOWER",
        "F",
        {"V": "00", "W": "00", "B": "00"},
    ),
    _ContractDef(
        "engie_empower_variable",
        "Engie Empower Variable",
        "indexed",
        "EMPOWER",
        "I",
        {"V": "00", "W": "00", "B": "00"},
    ),
    _ContractDef(
        "engie_empty_house",
        "Engie Empty House",
        "indexed",
        "EMPTYHOUSE",
        "I",
        {"V": "00", "W": "00", "B": "00"},
    ),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}
_CODE_TO_REGION = {code: region for region, code in _REGION_TO_CODE.items()}


def _document_url(contract: _ContractDef, region_code: str, month_offset: int = 0) -> str:
    months = contract.months_per_region[region_code]
    code = f"G_{contract.family}_R_GREY_C_{contract.rate}_{months}_{region_code}_F"
    return f"{_API_URL}?document={code}&monthOffset={month_offset}&segment=R&language=F"


def _region_code(contract: _ContractDef, region: str) -> str:
    code = _REGION_TO_CODE.get(region)
    if code is None or code not in contract.months_per_region:
        raise ExtractorError(f"Engie {contract.contract_id}: not sold in region {region!r}")
    return code


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The configured region's current card for ``contract_id``."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Engie")
    return await _read(
        session, contract_id, region, _document_url(contract, _region_code(contract, region))
    )


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(contract_id, region, await fetch_pdf_text(session, url))


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card Engie published for a past month, or None.

    ``monthOffset`` is the calendar distance from the month the endpoint is
    in, taken in Home Assistant's zone: on a UTC host the OS clock is still
    on the previous month for the first hours of the 1st in Brussels. A
    month ahead of today is refused rather than sent. A transient failure
    raises so the month cache retries it; any other failure is a month with
    no card, and a card naming another month than the one asked for is
    refused too.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    code = _REGION_TO_CODE.get(region)
    if contract is None or code is None or code not in contract.months_per_region:
        return None
    today = dt_util.now().date()
    offset = (today.year - year_month.year) * 12 + (today.month - year_month.month)
    if offset < 0:
        return None
    url = _document_url(contract, code, offset)
    return await month_card(_read(session, contract_id, region, url), year_month)


def parse_snapshot(contract_id: str, region: str, text: str) -> SupplierSnapshot:
    """Parse one regional card's text as pypdf extracts it."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Engie")
    _region_code(contract, region)
    card_month = _card_month(text)
    vat_rate = _vat_rate(text)
    energy = _energy(text, contract, 1.0 + vat_rate, card_month)
    dsos = _dsos(text, region)
    return SupplierSnapshot(
        supplier="engie",
        contract=contract_id,
        energy=energy,
        dsos=dsos,
        taxes=TaxOverlay(
            excise_bands=_excise(text),
            energy_contribution=_energy_contribution(text, card_month),
            connection_fee=_connection_fee(text) if region == REGION_WALLONIA else 0.0,
            osp_by_caliber=_osp(text) if region == REGION_BRUSSELS else None,
            card_vat_rate=vat_rate,
        ),
        source_url=_API_URL,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


_CARD_MONTH_RE = re.compile(r"contrats conclus en\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})")


def _card_month(text: str) -> date:
    """The month the card is for: "contrats conclus en Septembre 2026"."""
    match = _CARD_MONTH_RE.search(text)
    month = MONTH_NAMES.get(fold_accents(match.group(1))) if match else None
    if match is None or month is None:
        raise ExtractorError("Engie: card month not found")
    return month_date(match.group(2), month, "Engie")


_VAT_RE = re.compile(r"Prix,\s*(\d+(?:,\d+)?)\s*%\s*de tva comprise")


def _vat_rate(text: str) -> float:
    match = _VAT_RE.search(text)
    if match is None:
        raise ExtractorError("Engie: VAT statement not found")
    return to_float(match.group(1)) / 100.0


# "Redevance fixe (EUR/an)(11) Prix par kWh(1) (c EUR/kWh)" is a heading; the
# fixed card prints the two figures on the next line ("60,00 7,939"), the
# variable one prints the monthly price after "Prix mensuels" and the fee
# before a repeated "Prix par kWh".
_FIXED_RE = re.compile(r"Redevance fixe[^\n]*\n\s*(\d+,\d+)\s+(\d+,\d+)\s*\n")
_MONTHLY_RE = re.compile(r"Prix mensuels\s*\n\s*(\d+,\d+)\s*\n\s*(\d+,\d+)\s+Prix par kWh")
_FORMULA_RE = re.compile(
    r"Prélèvement\s*:\s*(\d+,\d+)\s*\+\s*\(\s*(\d+,\d+)\s*x\s*(ZTP101|ZTPDAM)\s*\(Heren\)"
)


# "Le prix ci-dessus a été calculé sur la base du paramètre ZTP101 (Heren) du
# mois = 61,7680 €/MWh, d’application pour Septembre 2026."
_APPLIES_RE = re.compile(r"d.application pour\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})")


def _priced_on_its_month(text: str, card_month: date) -> bool:
    """Whether the card states its ZTP101 value applies to its own month.
    The October 2026 card first went out priced on September's."""
    match = _APPLIES_RE.search(text)
    if match is None:
        return False
    month = MONTH_NAMES.get(fold_accents(match.group(1)))
    if month is None:
        return False
    try:
        return month_date(match.group(2), month, "Engie") == card_month
    except ExtractorError:
        return False


def _energy(
    text: str, contract: _ContractDef, vat: float, card_month: date
) -> FixedRates | IndexedRates:
    if contract.kind == "fixed":
        match = _FIXED_RE.search(text)
        if match is None:
            raise ExtractorError("Engie: fixed price block not found")
        return FixedRates(
            price=to_float(match.group(2)) / 100.0,
            yearly_fixed_fee=to_float(match.group(1)),
        )
    monthly = _MONTHLY_RE.search(text)
    formula = _FORMULA_RE.search(text)
    if monthly is None or formula is None:
        raise ExtractorError("Engie: variable price block or formula not found")
    index = formula.group(3)
    return IndexedRates(
        factor=to_float(formula.group(2)) / 100.0 * vat,
        base=to_float(formula.group(1)) / 100.0 * vat,
        index=index,
        price=to_float(monthly.group(1)) / 100.0,
        yearly_fixed_fee=to_float(monthly.group(2)),
        formula=formula.group(0),
        # ZTP101 is set in the month before delivery and the card prices its
        # month on it, when it says so; ZTPDAM is only known once the month
        # is over.
        settled=index == "ZTP101" and _priced_on_its_month(text, card_month),
    )


# The table columns as each regional card's header lays them out: per tier the
# fixed term then the proportional one, then Flanders's data management and
# Brussels's two metering fees (yearly and monthly reading), then transport.
_COLUMNS: dict[str, tuple[str, ...]] = {
    REGION_FLANDERS: (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, METERING, TRANSPORT),
    REGION_WALLONIA: (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, TRANSPORT),
    REGION_BRUSSELS: (
        T1_FIXED,
        T1_PROP,
        T2_FIXED,
        T2_PROP,
        T3_FIXED,
        T3_PROP,
        METERING,
        SKIP,
        TRANSPORT,
    ),
}
_LABELS: dict[str, dict[str, str]] = {
    REGION_FLANDERS: FLUVIUS_LABELS,
    REGION_WALLONIA: {**ORES_LABELS, "TECTEO - RESA": "resa"},
    REGION_BRUSSELS: {"SIBELGA": "sibelga"},
}


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    dsos = read_dsos(
        text,
        _LABELS[region],
        _COLUMNS[region],
        supplier="Engie",
        after="Coûts de réseaux",
    )
    require_region(dsos, region, "Engie")
    return dsos


_EXCISE_LOW_RE = re.compile(r"Consommation entre 0 & 12\.000 kWh\s+(\d+,\d+)")
_EXCISE_HIGH_RE = re.compile(r"Consommation > 12\.000 kWh\s+(\d+,\d+)")


def _excise(text: str) -> tuple[tuple[float | None, float], ...]:
    low = _EXCISE_LOW_RE.search(text)
    high = _EXCISE_HIGH_RE.search(text)
    if low is None or high is None:
        raise ExtractorError("Engie: federal excise rows not found")
    return excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0)


_CONTRIBUTION_RE = re.compile(r"Cotisation sur l['’]énergie\s+(\d+,\d+)")


def _energy_contribution(text: str, card_month: date) -> float:
    """The energy contribution as printed, up to the July 2026 cards."""
    match = _CONTRIBUTION_RE.search(text)
    return printed_contribution(
        None if match is None else match.group(1), card_month, supplier="Engie"
    )


_CONNECTION_FEE_RE = re.compile(r"Redevance raccordement\(\d+\)\s+(\d+,\d+)")


def _connection_fee(text: str) -> float:
    """The Walloon connection fee: a Walloon card without the row is a
    layout change, not a fee of zero."""
    match = _CONNECTION_FEE_RE.search(text)
    if match is None:
        raise ExtractorError("Engie: Walloon connection fee row not found")
    return to_float(match.group(1)) / 100.0


_OSP_ROW_RE = re.compile(r"^[>\d][^\n]*?m3/heure(?:\(\d+\))?\s+(\d+,\d+)\s*$", re.MULTILINE)


def _osp(text: str) -> dict[str, float]:
    start = text.find("Obligations de Service Public")
    if start < 0:
        raise ExtractorError("Engie: Brussels levy table not found")
    amounts = [to_float(value) for value in _OSP_ROW_RE.findall(text[start:])]
    return osp_table(amounts, supplier="Engie")


# ---- index values ------------------------------------------------------------

_MONTH_LABEL_RE = re.compile(r"^([A-Za-zÀ-ÿ]+)\s+(\d{4})$")
# The page's columns, left to right after the month, and the index each one is.
_INDEX_COLUMNS = ("TTF103", "TTF101", "ZTP101", "ZIGDAM", "ZTPDAM")


def parse_index_page(page: str) -> IndexTable:
    """Engie's gas indexation table, month by month, in EUR/MWh.

    One row per month or quarter, newest first; quarter rows ("2eme trimestre
    de 2016") are older than any product this reads and are skipped, as are
    empty cells and dashes.
    """
    table: IndexTable = {name: {} for name in _INDEX_COLUMNS}
    for cells in html_rows(page):
        if len(cells) != len(_INDEX_COLUMNS) + 1:
            continue
        match = _MONTH_LABEL_RE.match(cells[0])
        month = MONTH_NAMES.get(fold_accents(match.group(1))) if match else None
        if match is None or month is None:
            continue
        key = f"{match.group(2)}-{month:02d}"
        for name, value in zip(_INDEX_COLUMNS, cells[1:], strict=True):
            if re.fullmatch(r"\d+(?:,\d+)?", value):
                table[name][key] = to_float(value)
    if not table["ZTP101"] or not table["ZTPDAM"]:
        raise ExtractorError("Engie: indexation table not found")
    return table


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """Engie's published gas index values."""
    return parse_index_page(await fetch_text(session, _INDEX_URL))


EXTRACTOR = SupplierExtractor(
    id="engie",
    label="Engie",
    contracts=tuple(
        Contract(
            id=c.contract_id,
            label=c.label,
            kind=c.kind,
            regions=frozenset(_CODE_TO_REGION[code] for code in c.months_per_region),
        )
        for c in _CONTRACTS
    ),
    fetch=fetch,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=0.3,
)
