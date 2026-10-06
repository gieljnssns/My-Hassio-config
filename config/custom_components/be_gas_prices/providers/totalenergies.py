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

"""TotalEnergies Belgium gas tariff card extractor.

TotalEnergies publishes the current card per (product, region) at a URL it
overwrites every month, the one its cartes-tarifaires page links:

    https://totalenergies.be/static/marketing-documents/b2c/tariff-card/
        latest/<SLUG>_GAS_<VL|WAL|BXL>_FR.pdf

and keeps each month's card beside it, the current month's included, as

    .../tariff-card/<YYYY>_<M>_<SLUG>_GAS_<VL|WAL|BXL>_FR.pdf

with the month NOT zero-padded (2026_8). A card it does not publish (IMPACT
outside Wallonia, a zero-padded or unarchived month) answers 200 with an HTML
page rather than a 404, which the fetch helper refuses as not a PDF.

The region's card is read: the energy price differs between regions, and so
do the DSO table and the levies. Prices are 6% VAT inclusive; the formula is
printed excluding VAT and grossed up here by the card's own rate.

The variable products index on TTF_M_RLP, the RLP-weighted mean of the TTF
day-ahead quotes over the delivery month, known once the month is over. The
card prints a forward estimate made the Vlaamse Nutsregulator way ("Tarif
mensuel") and, "A titre indicatif", the formula at the last known TTF_M_RLP,
the previous month's ("Compteur Simple : 7,33"). The latter is kept as the
printed price. The index values are published month by month in a PDF linked
from the "valeur des indices historique" page, which ``fetch_index`` reads.

The cards are read with pdfplumber (``fetch_pdf_text_layout``): pypdf prints
the DSO labels first and their figures after. Three things about that text:

  - A rotated side stamp (a production date and the file name) comes out
    reversed ("erbmetpes", "RF_ZAG_elbairaV") and carries a date unrelated to
    the card. Nothing here matches it.
  - The "6" of "TVA 6 % incluse" is a text field of its own, which the
    reader emits after the heading instead of in place.
  - Every regulated figure is rounded to two decimals: excise 1,09 / 1,18,
    transport 0,17, the Walloon connection fee 0,01 where the regulated rate
    is 0,0075 c EUR/kWh. The energy contribution is still printed, at 0,11,
    as the last column of the DSO table. All are read as printed; the federal
    levies are replaced by the law's rates for the delivery month later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import aiohttp

from ..const import (
    DSO_ORES,
    DSO_RESA,
    DSO_SIBELGA,
    REGION_BRUSSELS,
    REGION_FLANDERS,
    REGION_WALLONIA,
)
from ._network import (
    FLUVIUS_LABELS,
    METERING,
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
    read_dsos,
    require_region,
)
from ._parse import (
    SIGN_CHARS,
    cell_value,
    fold_accents,
    parse_sign,
    require_contract,
    table_row,
    to_float,
)
from ._pdf import (
    MONTH_NAMES,
    fetch_pdf_text_layout,
    head_freshness_key,
    printed_vat_rate,
)
from ._rates import ALL_REGIONS, Contract, FixedRates, IndexedRates, TariffKind
from ._validity import end_of_month, future_month, month_card
from .base import (
    DsoOverlay,
    ExtractorError,
    IndexTable,
    SupplierExtractor,
    SupplierSnapshot,
    TaxOverlay,
)

_BASE_URL = "https://totalenergies.be/static/marketing-documents/b2c/tariff-card"
# The link on https://totalenergies.be/fr/particuliers/produits-et-services/
# my-home/electricite-et-gaz/offre-electricite-gaz/valeur-des-indices-historique.
# It redirects to a CDN copy under a dated folder (s3fs-public/2026-09/), so
# the link is the address kept.
_INDEX_URL = "https://totalenergies.be/fr/files/Historique-valeurs-param%C3%A8tres-gaz-produits-actuels-FR.pdf"

_REGION_TO_CODE: dict[str, str] = {
    REGION_FLANDERS: "VL",
    REGION_WALLONIA: "WAL",
    REGION_BRUSSELS: "BXL",
}


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    product: str  # the product name the card prints after "TotalEnergies"
    kind: TariffKind
    slug: str  # the file name prefix
    regions: frozenset[str] = ALL_REGIONS


# Every residential gas card the cartes-tarifaires page links. The social
# tariff is set by the CREG and assigned rather than chosen, so it is not
# listed; myDrive and myDynamic have no gas card.
_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("totalenergies_gaz_fixed", "Gaz Fixe", "fixed", "GAZ-FIXE"),
    _ContractDef("totalenergies_gaz_variable", "Gaz Variable", "indexed", "GAZ-VARIABLE"),
    _ContractDef(
        "totalenergies_impact_variable",
        "Impact Variable",
        "indexed",
        "IMPACT",
        frozenset({REGION_WALLONIA}),
    ),
    _ContractDef("totalenergies_mycomfort_variable", "myComfort Variable", "indexed", "MYCOMFORT"),
    _ContractDef("totalenergies_mycomfort_fixed", "myComfort Fixe", "fixed", "MYCOMFORT-FIXED"),
    _ContractDef(
        "totalenergies_myessential_variable", "myEssential Variable", "indexed", "MYESSENTIAL"
    ),
    _ContractDef(
        "totalenergies_myessential_fixed", "myEssential Fixe", "fixed", "MYESSENTIAL-FIXED"
    ),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _contract(contract_id: str, region: str) -> _ContractDef:
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "TotalEnergies")
    if region not in contract.regions:
        raise ExtractorError(f"TotalEnergies {contract_id}: not sold in region {region!r}")
    return contract


def _card_name(contract: _ContractDef, region: str) -> str:
    return f"{contract.slug}_GAS_{_REGION_TO_CODE[region]}_FR.pdf"


def _latest_url(contract: _ContractDef, region: str) -> str:
    return f"{_BASE_URL}/latest/{_card_name(contract, region)}"


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The configured region's current card for ``contract_id``."""
    contract = _contract(contract_id, region)
    return await _read(session, contract_id, region, _latest_url(contract, region))


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(contract_id, region, await fetch_pdf_text_layout(session, url), url)


async def probe(session: aiohttp.ClientSession, contract_id: str, region: str) -> str | None:
    """The Last-Modified of the current card, which is overwritten in place."""
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region not in contract.regions:
        return None
    return await head_freshness_key(session, _latest_url(contract, region))


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card TotalEnergies published for a past month, or None.

    A month ahead of today in Home Assistant's zone is refused rather than
    asked for. A transient failure raises so the month cache retries it; any
    other failure, the soft 404 of a month the archive does not hold among
    them, is a month with no card, and a card naming another month than the
    one asked for is refused too.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region not in contract.regions:
        return None
    if future_month(year_month):
        return None
    url = f"{_BASE_URL}/{year_month.year}_{year_month.month}_{_card_name(contract, region)}"
    return await month_card(_read(session, contract_id, region, url), year_month)


def parse_snapshot(
    contract_id: str, region: str, text: str, source_url: str | None = None
) -> SupplierSnapshot:
    """Parse one regional card's text as pdfplumber lays it out."""
    contract = _contract(contract_id, region)
    card_month = _card_month(text, contract)
    vat_rate = _vat_rate(text)
    dsos = _dsos(text, region)
    # A dash in the contribution column would be a card printing none.
    contribution = _table_levy(text, region, _CONTRIBUTION_COLUMN) or 0.0
    return SupplierSnapshot(
        supplier="totalenergies",
        contract=contract_id,
        energy=_energy(text, contract, 1.0 + vat_rate),
        dsos=dsos,
        taxes=TaxOverlay(
            excise_bands=_excise(text),
            energy_contribution=contribution,
            connection_fee=_connection_fee(text) if region == REGION_WALLONIA else 0.0,
            osp_by_caliber=_osp(text) if region == REGION_BRUSSELS else None,
            card_vat_rate=vat_rate,
        ),
        source_url=source_url or _latest_url(contract, region),
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


# Both pages open on the product over the card month: "TotalEnergies
# myComfort Variable" then "septembre 2026".
_HEADING_RE = re.compile(r"^TotalEnergies (.+)\n([^\W\d_]+) (20\d{2})$", re.MULTILINE)


def _card_month(text: str, contract: _ContractDef) -> date:
    """The month the card is for, from a heading naming this product."""
    headings = set(_HEADING_RE.findall(text))
    if len(headings) != 1:
        raise ExtractorError("TotalEnergies: card heading not found or inconsistent")
    product, month_name, year = headings.pop()
    if product != contract.product:
        raise ExtractorError(
            f"TotalEnergies: card is for {product!r}, expected {contract.product!r}"
        )
    month = MONTH_NAMES.get(fold_accents(month_name))
    if month is None:
        raise ExtractorError(f"TotalEnergies: card month {month_name!r} not understood")
    return date(int(year), month, 1)


# "TVA 6 % incluse" comes out as "TVA % incluse", and the rate as a line of
# its own after the heading's "Conditions particulières relatives à la
# formule ..." line.
_VAT_RE = re.compile(
    r"TVA % incluse\n[\s\S]*?^Conditions particulières relatives à la formule [^\n]+\n"
    r"(\d+(?:,\d+)?)$",
    re.MULTILINE,
)


def _vat_rate(text: str) -> float:
    rate = printed_vat_rate(text, _VAT_RE)
    if rate is None:
        raise ExtractorError("TotalEnergies: VAT statement not found")
    return rate


_INDEX = "TTF_M_RLP"
# The fixed card prints the yearly fee then the price on one row: "90,00 8,45
# Tarif annuel". The variable one prints the estimate with the fee on the
# line below ("7,41 Tarif mensuel", "90,00", and from October 2026 "100"),
# then the formula in c EUR/kWh excluding VAT with the index in EUR/MWh. The
# March 2026 cards wrote it "0.1007*TTFM_RLP+0,67".
_FIXED_RE = re.compile(r"^(\d+,\d+) (\d+,\d+) Tarif annuel$", re.MULTILINE)
_FEE_RE = re.compile(r"^(\d+,\d+) Tarif mensuel\n(\d+(?:,\d+)?)$", re.MULTILINE)
_FORMULA_RE = re.compile(
    rf"^((\d+[.,]\d+)\s*\*\s*TTF_?M_RLP\s*([{SIGN_CHARS}])\s*(\d+[.,]\d+)) Formule tarifaire$",
    re.MULTILINE,
)
_INDICATIVE_RE = re.compile(r"Compteur Simple\s*:\s*(\d+,\d+)")


def _energy(text: str, contract: _ContractDef, vat: float) -> FixedRates | IndexedRates:
    if contract.kind == "fixed":
        match = _FIXED_RE.search(text)
        if match is None:
            raise ExtractorError("TotalEnergies: fixed price row not found")
        return FixedRates(
            price=to_float(match.group(2)) / 100.0,
            yearly_fixed_fee=to_float(match.group(1)),
        )
    fee = _FEE_RE.search(text)
    formula = _FORMULA_RE.search(text)
    if fee is None or formula is None:
        raise ExtractorError("TotalEnergies: variable price block or formula not found")
    # The indicative price is the formula at the previous month's value.
    # From October 2026 the card leaves it blank ("Compteur Simple : € cent/
    # kWh"), and its estimate, the only price it then prints, stands in.
    indicative = _INDICATIVE_RE.search(text)
    price = fee.group(1) if indicative is None else indicative.group(1)
    # TTF_M_RLP is only known once the delivery month is over, so the
    # indicative price is not settled.
    return IndexedRates(
        factor=to_float(formula.group(2)) / 100.0 * vat,
        base=parse_sign(formula.group(3)) * to_float(formula.group(4)) / 100.0 * vat,
        index=_INDEX,
        price=to_float(price) / 100.0,
        yearly_fixed_fee=to_float(fee.group(2)),
        formula=formula.group(1),
    )


# The DSO table's columns as its header prints them: the three proportional
# terms, the three fixed ones, transport, "Coût activité de mesure et
# comptage" (0,00 in Wallonia), then the levies the table carries: the
# Walloon connection fee and, last on every card, the energy contribution.
_NETWORK_COLUMNS = (T1_PROP, T2_PROP, T3_PROP, T1_FIXED, T2_FIXED, T3_FIXED, TRANSPORT, METERING)
_COLUMNS: dict[str, tuple[str, ...]] = {
    REGION_FLANDERS: (*_NETWORK_COLUMNS, SKIP),
    REGION_WALLONIA: (*_NETWORK_COLUMNS, SKIP, SKIP),
    REGION_BRUSSELS: (*_NETWORK_COLUMNS, SKIP),
}
_CONNECTION_FEE_COLUMN = -2
_CONTRIBUTION_COLUMN = -1
_LABELS: dict[str, dict[str, str]] = {
    REGION_FLANDERS: FLUVIUS_LABELS,
    REGION_WALLONIA: {
        "RESA SA": DSO_RESA,
        "ORES (Namur - Namen)": DSO_ORES,
        "ORES (Hainaut - Henegouwen)": DSO_ORES,
        "ORES (Luxembourg - Luxemburg)": DSO_ORES,
        "ORES (Waals-Brabant Wallon)": DSO_ORES,
        "ORES (Mouscron - Moeskroen)": DSO_ORES,
    },
    REGION_BRUSSELS: {"SIBELGA": DSO_SIBELGA},
}
_TABLE_START = "Coûts de distribution - Terme variable"
_TABLE_END = "Accise fédérale"


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    dsos = read_dsos(
        text,
        _LABELS[region],
        _COLUMNS[region],
        supplier="TotalEnergies",
        after=_TABLE_START,
        before=_TABLE_END,
    )
    require_region(dsos, region, "TotalEnergies")
    return dsos


def _table_levy(text: str, region: str, column: int) -> float | None:
    """A levy the DSO table prints as a column, in EUR/kWh, None for a dash.

    Every row repeats it, since it does not depend on the DSO, so it is read
    off each row and the rows must agree: rows that differ are a misread.
    """
    columns = _COLUMNS[region]
    cells = {
        row[column]
        for label in _LABELS[region]
        if (row := table_row(text, label, len(columns), after=_TABLE_START, before=_TABLE_END))
        is not None
    }
    if len(cells) != 1:
        raise ExtractorError("TotalEnergies: DSO table levy column missing or inconsistent")
    value = cell_value(cells.pop())
    return None if value is None else value / 100.0


def _connection_fee(text: str) -> float:
    """The Walloon connection fee: mandatory on a Walloon card."""
    fee = _table_levy(text, REGION_WALLONIA, _CONNECTION_FEE_COLUMN)
    if fee is None:
        raise ExtractorError("TotalEnergies: Walloon connection fee not printed")
    return fee


_EXCISE_LOW_RE = re.compile(r"^Consommation entre 0 et 12\.000 kWh (\d+,\d+)$", re.MULTILINE)
_EXCISE_HIGH_RE = re.compile(r"^> 12\.000 kWh (\d+,\d+)$", re.MULTILINE)


def _excise(text: str) -> tuple[tuple[float | None, float], ...]:
    low = _EXCISE_LOW_RE.search(text)
    high = _EXCISE_HIGH_RE.search(text)
    if low is None or high is None:
        raise ExtractorError("TotalEnergies: federal excise rows not found")
    return excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0)


_OSP_START = "Droit pour le financement des Obligations de Service Public"
# "<= 10 m³/h 5 3,56": the digit after the caliber is a footnote mark the card
# never defines, so the amount is the last figure of the row.
_OSP_ROW_RE = re.compile(r"^(?:<=|Entre|>)[^\n]*m³/h[^\n]* (\d+,\d+)$", re.MULTILINE)


def _osp(text: str) -> dict[str, float]:
    start = text.find(_OSP_START)
    end = text.find(_TABLE_END, start) if start >= 0 else -1
    if end < 0:
        raise ExtractorError("TotalEnergies: Brussels levy table not found")
    amounts = [to_float(value) for value in _OSP_ROW_RE.findall(text[start:end])]
    return osp_table(amounts, supplier="TotalEnergies")


# ---- index values ------------------------------------------------------------

# The history's columns, left to right after the month.
_INDEX_COLUMNS = (_INDEX, "ZTP_M_RLP", "ZTP_Q_RLP")
_INDEX_HEADER_RE = re.compile(r"TTF_M_RLP\*\s+ZTP_M_RLP\*\s+ZTP_Q_RLP\*\*")
_INDEX_ROW_RE = re.compile(r"^(\d{2})/(20\d{2})((?: \d+,\d+){2,3})$", re.MULTILINE)


def parse_index_history(text: str) -> IndexTable:
    """TotalEnergies's gas index history by delivery month, in EUR/MWh.

    One row per month, newest first ("08/2026 61,662 61,824"). The quarterly
    ZTP_Q_RLP is printed on each month of its quarter and left empty until the
    quarter is over, so a row with two figures is missing the last column.
    The header is checked because the columns are read by position.
    """
    if _INDEX_HEADER_RE.search(text) is None:
        raise ExtractorError("TotalEnergies: index history header not found")
    table: IndexTable = {name: {} for name in _INDEX_COLUMNS}
    for month, year, values in _INDEX_ROW_RE.findall(text):
        for name, value in zip(_INDEX_COLUMNS, values.split(), strict=False):
            table[name][f"{year}-{month}"] = to_float(value)
    if not table[_INDEX]:
        raise ExtractorError("TotalEnergies: index history table not found")
    return table


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """TotalEnergies's published gas index values."""
    return parse_index_history(await fetch_pdf_text_layout(session, _INDEX_URL))


EXTRACTOR = SupplierExtractor(
    id="totalenergies",
    label="TotalEnergies",
    contracts=tuple(
        Contract(
            id=c.contract_id,
            label=f"TotalEnergies {c.product}",
            kind=c.kind,
            regions=c.regions,
        )
        for c in _CONTRACTS
    ),
    fetch=fetch,
    probe=probe,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    # pdfplumber takes about 10 s per card on a Raspberry Pi 4.
    sweep_cost_s=10.0,
)
