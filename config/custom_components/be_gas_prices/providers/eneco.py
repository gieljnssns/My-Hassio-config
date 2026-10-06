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

"""Eneco Belgium gas tariff card extractor.

Eneco publishes one card per gas product, the same card for Flanders and
Wallonia, at

    https://cdn.eneco.be/downloads/nl/general/tk/BC_032_<ISSUE>_NL_ENECO_GAS_<TOKEN>.pdf

TOKEN is FIX (Aardgas Vast), FLEX (Aardgas Flex) or FLEX_ONE (Aardgas Flex
One). ISSUE is "01" and the card's year and month, which the card repeats
("Tariefkaart versie 012609" for September 2026). The current card is the
one the public listing links, the same scrape as for electricity. Every past
issue stays on the CDN, so the built URL is the archive: Flex back to at least
January 2020, Vast with a gap from January 2022 to April 2023, Flex One only
from September 2026. No second issue of a month ("02YYMM") was found for Flex
or Vast, gas or electricity, from 2019 to 2026, so only the first is asked for.
Cards before 2025 name the Fluvius DSOs that merged away and price no Flemish
household. Their Walloon rows read from February 2024, the first card on which
the five ORES sub-areas print one tariff.

There is no Brussels card: Brugel's supplier list notes that Eneco no longer
takes new Brussels residential customers, and the cards are "voor Vlaanderen
en Wallonië".

Every figure is 6% VAT inclusive, the formula included: it carries its own
multiplier ("(0,1 X TTFDAW-RLP-M + 1,074) X 1,06"). Both variable products
index on TTFDAW-RLP-M, the RLP-weighted mean of the ICIS Heren TTF day-ahead
and weekend prices over the delivery month, known once the month is over. The
card's Maandprijs is the formula at the last month known, which a footnote
names ("08/2026: €61,6374/MWh"). Eneco publishes every month's value to two
decimals in its indexation PDF, which is what fetch_index reads.

The card is read with pypdf. pdfplumber sets the tax block on the same lines
as the DSO rows and scrambles the one DSO label that wraps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from itertools import pairwise
from typing import Any

import aiohttp

from ..const import (
    DSO_FLUVIUS_ANTWERPEN,
    DSO_FLUVIUS_HALLE_VILVOORDE,
    DSO_FLUVIUS_IMEWO,
    DSO_FLUVIUS_KEMPEN,
    DSO_FLUVIUS_LIMBURG,
    DSO_FLUVIUS_MIDDEN_VLAANDEREN,
    DSO_FLUVIUS_WEST,
    DSO_FLUVIUS_ZENNE_DIJLE,
    DSO_RESA,
    REGION_FLANDERS,
    REGION_WALLONIA,
)
from ._network import (
    METERING,
    ORES_LABELS,
    T1_FIXED,
    T1_PROP,
    T2_FIXED,
    T2_PROP,
    excise_bands,
    read_dsos,
    require_region,
)
from ._parse import SIGN_CHARS, cell_value, month_date, parse_sign, require_contract, to_float
from ._pdf import (
    NL_MONTHS,
    fetch_pdf_rendered,
    fetch_pdf_text,
    fetch_text,
    pdfplumber_text,
    printed_vat_rate,
    word_centre,
    word_rows,
)
from ._rates import Contract, FixedRates, IndexedRates, TariffKind
from ._validity import end_of_month, future_month, month_card
from .base import (
    DsoOverlay,
    ExtractorError,
    IndexTable,
    SupplierExtractor,
    SupplierSnapshot,
    TaxOverlay,
)

_BASE_URL = "https://cdn.eneco.be/downloads/nl/general/tk"
# With the trailing slash: the bare path answers a 308 to this one.
_LISTING_URL = "https://eneco.be/nl/elektriciteit-gas/tariefkaarten/"
_INDEX_URL = "https://cdn.eneco.be/downloads/nl/b2c/acq/indexatieparameters-aardgas.pdf"

# The index both variable products settle on, as the card and the indexation
# PDF name it.
_INDEX = "TTFDAW-RLP-M"

_REGIONS = frozenset({REGION_FLANDERS, REGION_WALLONIA})
_NL_MONTH = {name: number for number, name in enumerate(NL_MONTHS, 1)}


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    kind: TariffKind
    token: str  # GAS_<TOKEN> in the file name


# The label is also the title the card opens with.
_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("eneco_aardgas_vast", "Eneco Aardgas Vast", "fixed", "FIX"),
    _ContractDef("eneco_aardgas_flex", "Eneco Aardgas Flex", "indexed", "FLEX"),
    _ContractDef("eneco_aardgas_flex_one", "Eneco Aardgas Flex One", "indexed", "FLEX_ONE"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _contract(contract_id: str, region: str) -> _ContractDef:
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Eneco")
    if region not in _REGIONS:
        raise ExtractorError(f"Eneco {contract_id}: not sold in region {region!r}")
    return contract


def card_url(listing: str, contract_id: str) -> str:
    """The current card of ``contract_id`` as the listing links it.

    The token is closed by ".pdf", so FLEX never picks up the FLEX_ONE card.
    """
    token = require_contract(_CONTRACTS_BY_ID, contract_id, "Eneco").token
    match = re.search(rf"{re.escape(_BASE_URL)}/BC_032_\d{{6}}_NL_ENECO_GAS_{token}\.pdf", listing)
    if match is None:
        raise ExtractorError(f"Eneco: the listing links no GAS_{token} card")
    return match.group(0)


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The current card for ``contract_id``, read for ``region``."""
    _contract(contract_id, region)
    return await _read(
        session, contract_id, region, card_url(await fetch_text(session, _LISTING_URL), contract_id)
    )


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(contract_id, region, await fetch_pdf_text(session, url), url)


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card Eneco issued for ``year_month``, or None.

    A month ahead of today in Home Assistant's zone is not asked for. A
    transient failure raises so the month cache retries it; any other
    failure, a 404 for a month the product was not sold included, is a month
    with no card. A card that parses but names another month is refused.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region not in _REGIONS:
        return None
    if future_month(year_month):
        return None
    issue = f"01{year_month.year % 100:02d}{year_month.month:02d}"
    url = f"{_BASE_URL}/BC_032_{issue}_NL_ENECO_GAS_{contract.token}.pdf"
    return await month_card(_read(session, contract_id, region, url), year_month)


def parse_snapshot(contract_id: str, region: str, text: str, source_url: str) -> SupplierSnapshot:
    """Parse one card's text as pypdf extracts it, for ``region``.

    One card serves both regions, so the region picks the DSO rows and
    whether the Walloon connection fee applies.
    """
    contract = _contract(contract_id, region)
    _require_product(text, contract)
    card_month = _card_month(text)
    return SupplierSnapshot(
        supplier="eneco",
        contract=contract_id,
        energy=_energy(text, contract),
        dsos=_dsos(text, region),
        taxes=_taxes(text, region),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


_TITLE_RE = re.compile(r"\s*(Eneco Aardgas[^\n]*)")


def _require_product(text: str, contract: _ContractDef) -> None:
    """Refuse a card whose title names another product. Flex and Flex One
    print the same layout and differ only in their base."""
    match = _TITLE_RE.match(text)
    title = match.group(1).strip() if match else None
    if title != contract.label:
        raise ExtractorError(f"Eneco: card is titled {title!r}, expected {contract.label!r}")


# "Tariefkaart september 2026 van Eneco Belgium nv", the first sentence.
_CARD_MONTH_RE = re.compile(r"Tariefkaart\s+([a-z]+)\s+(\d{4})\s+van\s+Eneco")


def _card_month(text: str) -> date:
    match = _CARD_MONTH_RE.search(text)
    month = _NL_MONTH.get(match.group(1)) if match else None
    if match is None or month is None:
        raise ExtractorError("Eneco: card month not found")
    return month_date(match.group(2), month, "Eneco")


# Under the "VERBRUIK (€cent/kWh)" heading the yearly fee comes first. The
# fixed card prints the price beside it; the variable one prints the yearly
# estimate and then the Maandprijs on lines of their own, each followed by its
# label, which the cards before 2025 prefixed with a ">" bullet.
_ENERGY_HEAD = r"VERBRUIK\s*\n\s*\(€cent/kWh\)\s*\n\s*(\d+,\d+)"
_FIXED_RE = re.compile(_ENERGY_HEAD + r"[ \t]+(\d+,\d+)[ \t]*\n")
_VARIABLE_RE = re.compile(
    _ENERGY_HEAD + r"\s*\n\s*\d+,\d+\s*>?\s*Geschatte jaarprijs\s*\n\s*(\d+,\d+)\s*>?\s*Maandprijs"
)
_FORMULA_RE = re.compile(
    rf"\(\s*(\d+(?:,\d+)?)\s*X\s*{_INDEX}\s*([{SIGN_CHARS}])\s*(\d+,\d+)\s*\)\s*X\s*(\d+,\d+)"
)


def _energy(text: str, contract: _ContractDef) -> FixedRates | IndexedRates:
    if contract.kind == "fixed":
        match = _FIXED_RE.search(text)
        if match is None:
            raise ExtractorError("Eneco: fixed price block not found")
        return FixedRates(
            price=to_float(match.group(2)) / 100.0,
            yearly_fixed_fee=to_float(match.group(1)),
        )
    monthly = _VARIABLE_RE.search(text)
    formula = _FORMULA_RE.search(text)
    if monthly is None or formula is None:
        raise ExtractorError("Eneco: variable price block or formula not found")
    # The formula gives c EUR/kWh for an index in EUR/MWh and carries its own
    # VAT multiplier ("X 1,06"), applied here once and not grossed again.
    scale = to_float(formula.group(4)) / 100.0
    return IndexedRates(
        factor=to_float(formula.group(1)) * scale,
        base=parse_sign(formula.group(2)) * to_float(formula.group(3)) * scale,
        index=_INDEX,
        price=to_float(monthly.group(2)) / 100.0,
        yearly_fixed_fee=to_float(monthly.group(1)),
        formula=formula.group(0),
    )


# "Vaste term (€/jaar), Proportionele term (€cent/kWh)" for T1 then T2, then
# "Meteropname (€/jaar)", which is the Flemish data management fee and a dash
# on the Walloon rows. No T3: the card only covers up to 100 MWh a year.
_COLUMNS = (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, METERING)

# The labels as Eneco prints them. Kempen and Midden-Vlaanderen keep the name
# of the DSO they replaced in brackets; their figures are the new areas'.
_LABELS: dict[str, dict[str, str]] = {
    REGION_FLANDERS: {
        "FLUVIUS ANTWERPEN": DSO_FLUVIUS_ANTWERPEN,
        "FLUVIUS HALLE VILVOORDE": DSO_FLUVIUS_HALLE_VILVOORDE,
        "FLUVIUS IMEWO": DSO_FLUVIUS_IMEWO,
        "FLUVIUS KEMPEN (IVEKA)": DSO_FLUVIUS_KEMPEN,
        "FLUVIUS LIMBURG": DSO_FLUVIUS_LIMBURG,
        "FLUVIUS MIDDEN VLAANDEREN (INTERGEM)": DSO_FLUVIUS_MIDDEN_VLAANDEREN,
        "FLUVIUS WEST": DSO_FLUVIUS_WEST,
        "FLUVIUS ZENNE DIJLE": DSO_FLUVIUS_ZENNE_DIJLE,
    },
    REGION_WALLONIA: {**ORES_LABELS, "TECTEO RESA": DSO_RESA},
}

# pypdf breaks "FLUVIUS MIDDEN VLAANDEREN (INTERGEM)" before the bracket and
# leaves the cells on the second line, where table_row would read "(INTERGEM)"
# as the whole label. Joined back, the row is one line like the others.
_WRAPPED_LABEL_RE = re.compile(r"^([A-Z][^\d\n]*?)[ \t]*\n(\([A-Z]+\)[ \t]+\d)", re.MULTILINE)

# Transport is a note beside the table, not a column: "Voor het jaar 2026
# raamt Fluxys deze kosten op 0,165 €cent/kWh (incl. btw)".
_TRANSPORT_RE = re.compile(r"raamt Fluxys deze kosten\s+op\s+(\d+,\d+)\s*€cent/kWh")


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    transport = _TRANSPORT_RE.search(text)
    if transport is None:
        raise ExtractorError("Eneco: Fluxys transport note not found")
    dsos = read_dsos(
        _WRAPPED_LABEL_RE.sub(r"\1 \2", text),
        _LABELS[region],
        _COLUMNS,
        supplier="Eneco",
        after="Netbeheerder",
        transport=to_float(transport.group(1)) / 100.0,
    )
    require_region(dsos, region, "Eneco")
    return dsos


# "Verbruik tussen 0 en 12.000 kWh 1,0929 0,0000": the special excise, then
# the energy contribution, on the same line. The label is set with no-break
# spaces.
_EXCISE_LOW_RE = re.compile(
    r"Verbruik\s+tussen\s+0\s+en\s+12\.000\s+kWh\s+(\d+,\d+)[ \t]+(\d+,\d+)"
)
_EXCISE_HIGH_RE = re.compile(r"Verbruik\s+>\s+12\.000\s+kWh\s+(\d+,\d+)[ \t]+(\d+,\d+)")
# The per-kWh row, not the flat "0 - 100 kWh/jaar 0,0075 €" one above it,
# which is the same rate on the first 100 kWh.
_CONNECTION_FEE_RE = re.compile(r"Aansluitingsvergoeding\s+<\s*1\s*GWh\s+(\d+,\d+)\s*€cent/kWh")
_VAT_RE = re.compile(r"Alle prijzen en tarieven zijn inclusief\s*(\d+(?:,\d+)?)\s*%\s*btw")


def _taxes(text: str, region: str) -> TaxOverlay:
    low = _EXCISE_LOW_RE.search(text)
    high = _EXCISE_HIGH_RE.search(text)
    if low is None or high is None:
        raise ExtractorError("Eneco: federal excise rows not found")
    contribution = to_float(low.group(2))
    if to_float(high.group(2)) != contribution:
        raise ExtractorError("Eneco: the two excise rows print different energy contributions")
    return TaxOverlay(
        excise_bands=excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0),
        energy_contribution=contribution / 100.0,
        connection_fee=_connection_fee(text) if region == REGION_WALLONIA else 0.0,
        card_vat_rate=printed_vat_rate(text, _VAT_RE),
    )


def _connection_fee(text: str) -> float:
    """The Walloon connection fee: a card without the row is a layout
    change, not a fee of zero."""
    match = _CONNECTION_FEE_RE.search(text)
    if match is None:
        raise ExtractorError("Eneco: Walloon connection fee row not found")
    return to_float(match.group(1)) / 100.0


# Index values, from the indexation PDF.

_YEAR_RE = re.compile(r"\d{4}")


def _word_rows(page: Any) -> list[list[dict[str, Any]]]:
    """The page's upright words by line. The print code set sideways in the
    margin is left out, or it could land at the start of a month's row."""
    return word_rows([w for w in page.extract_words() if w["upright"]])


def _place(words: list[dict[str, Any]], columns: list[float], month: str) -> list[str]:
    """One month's figures in their columns, a dash where there is none."""
    if not columns:
        raise ExtractorError(f"Eneco: index row {month} before the column headings")
    tolerance = min(b - a for a, b in pairwise(columns)) / 2.0
    cells = ["-"] * len(columns)
    for word in words:
        centre = word_centre(word)
        column = min(range(len(columns)), key=lambda i: abs(columns[i] - centre))
        if abs(columns[column] - centre) > tolerance or cells[column] != "-":
            raise ExtractorError(f"Eneco: index figure {word['text']} in {month} fits no column")
        cells[column] = word["text"]
    return cells


def _render_index(pdf: Any) -> str:
    lines: list[str] = []
    columns: list[float] = []
    for page in pdf.pages:
        for row in _word_rows(page):
            texts = [word["text"] for word in row]
            if _INDEX in texts:
                columns = [word_centre(word) for word in row]
                lines.append(" ".join(texts))
            elif len(texts) > 2 and texts[0].lower() in _NL_MONTH and _YEAR_RE.fullmatch(texts[1]):
                month = f"{texts[0]} {texts[1]}"
                lines.append(" ".join([month, *_place(row[2:], columns, month)]))
    return "\n".join(lines)


def index_table_text(payload: bytes) -> str:
    """Eneco's gas indexation PDF as text: the column headings, then one
    month a line with a dash in every empty cell.

    The PDF leaves a cell empty where a value is not published (TTFDAW-RLP-M
    before March 2023, a quarterly column until its quarter is over), and its
    text layer does not say which: "Juli 2026 52,99 45,11 45,75" reads the
    same whichever three columns they are. So each figure goes in the column
    whose heading it sits under.
    """
    return pdfplumber_text(payload, "index", _render_index)


def parse_index_text(text: str) -> IndexTable:
    """The index values by column heading and month, in EUR/MWh.

    The quarterly columns are printed on each month of their quarter, so
    they come out month by month like the monthly one.
    """
    table: IndexTable = {}
    names: list[str] = []
    for line in text.splitlines():
        words = line.split()
        if _INDEX in words:
            names = words
            for name in names:
                table.setdefault(name, {})
            continue
        month = _NL_MONTH.get(words[0].lower()) if words else None
        if month is None or len(words) != len(names) + 2:
            raise ExtractorError(f"Eneco: unreadable index row {line!r}")
        for name, cell in zip(names, words[2:], strict=True):
            value = cell_value(cell)
            if value is not None:
                table[name][f"{words[1]}-{month:02d}"] = value
    if not table.get(_INDEX):
        raise ExtractorError(f"Eneco: no {_INDEX} values in the indexation PDF")
    return table


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """Eneco's published gas index values."""
    text = await fetch_pdf_rendered(
        session, _INDEX_URL, variant="eneco-index", timeout=30, render=index_table_text
    )
    return parse_index_text(text)


EXTRACTOR = SupplierExtractor(
    id="eneco",
    label="Eneco",
    contracts=tuple(
        Contract(id=c.contract_id, label=c.label, kind=c.kind, regions=_REGIONS) for c in _CONTRACTS
    ),
    fetch=fetch,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=0.8,
)
