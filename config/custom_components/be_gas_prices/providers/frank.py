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

"""Frank Energie gas tariff card extractor.

Frank Energie sells one variable gas contract in Flanders in five tiers,
each with its own monthly card: the standard one, HV (a higher subscription
for a lower margin), JN, Slim (only beside a Slim electricity contract) and
Korting (a cashback). The cards are file assets of the Sanity CMS behind the
site, found with the query the electricity cards use:

    https://8navd656.api.sanity.io/v2023-01-01/data/query/production-be
        *[_type=="sanity.fileAsset" && originalFilename match "*Gas*"]

The file names carry the tier and the month: "... Tariefkaart Gas ZTP
September 2026.pdf" for the standard tier, "... Gas HV September 2026.pdf"
from September 2026 and "... Gas ZTP HV Augustus 2026.pdf" before. Korting
files are "VT", Slim ones "SL" or "Slim" from month to month. Frank
re-uploads a card now and then ("... Maart 2026 (1).pdf", "... 2026 v2.pdf"),
sometimes after the next month's card, so a card is chosen by the month its
name gives and only then by upload time. Uploads go back to July 2023, which
makes the same query the archive, but the late 2024 names carry no year and
the January 2025 cards are the first to print the Fluvius areas of today.

Every tier prices the delivery month at

    (factor x M ZTP RLP0N EOD EEX + base) x 1,06 in EURct/kWh

with the index, the RLP-weighted ZTP day price published by EEX, in EUR/MWh.
The formula carries its VAT, so it is not grossed again. The card only
prints the formula at a VNR estimate ("Verwacht volgens methode VNR voor
september 2026"). Frank publishes the realised index month by month in the
"Index waarden" table of its terms page, which is what fetch_index reads.

The subscription is printed per month. The cashback three tiers grant (HV,
JN, Korting) is not read: a snapshot has no field for it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

import aiohttp
from homeassistant.util import dt as dt_util

from ..const import REGION_FLANDERS
from ._network import (
    FLUVIUS_LABELS,
    METERING,
    T1_FIXED,
    T1_PROP,
    T2_FIXED,
    T2_PROP,
    TRANSPORT,
    excise_bands,
    printed_contribution,
    read_dsos,
    require_region,
)
from ._parse import (
    SIGN_CHARS,
    fold_accents,
    html_rows,
    month_date,
    parse_sign,
    require_contract,
    to_float,
)
from ._pdf import (
    MONTH_NAMES,
    NL_MONTHS,
    fetch_pdf_text_layout,
    fetch_text,
    parse_json,
    printed_vat_rate,
)
from ._rates import Contract, IndexedRates
from ._validity import end_of_month, future_month, month_card
from .base import (
    DsoOverlay,
    ExtractorError,
    IndexTable,
    SupplierExtractor,
    SupplierSnapshot,
    TaxOverlay,
)

_SANITY_URL = "https://8navd656.api.sanity.io/v2023-01-01/data/query/production-be"
_TERMS_URL = "https://www.frankenergie.be/nl/voorwaarden"
_GAS_ASSETS = '*[_type=="sanity.fileAsset" && originalFilename match "*Gas*"'

# The index as the card and the terms page both name it.
_INDEX = "M ZTP RLP0N EOD EEX"

_REGIONS = frozenset({REGION_FLANDERS})


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    # The tier words the card's title and the file names use; "" for the
    # standard tier, which names none.
    titles: tuple[str, ...]
    files: tuple[str, ...]


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("frank_variable", "Frank Energie Gas Variabel", ("",), ("",)),
    _ContractDef("frank_variable_hv", "Frank Energie Gas Variabel HV", ("HV",), ("HV",)),
    # "June" until May 2025: the same wording ("voor klanten met een digitale
    # meter"), formula and 35 EUR cashback as the JN cards after it.
    _ContractDef(
        "frank_variable_jn", "Frank Energie Gas Variabel JN", ("JN", "June"), ("JN", "June")
    ),
    _ContractDef(
        "frank_variable_slim", "Frank Energie Gas Variabel Slim", ("Slim", "SL"), ("SL", "Slim")
    ),
    # Titled "Korting ZTP" until September 2026, "VT ZTP" from October, as
    # its file was named all along.
    _ContractDef(
        "frank_variable_korting", "Frank Energie Gas Variabel Korting", ("Korting", "VT"), ("VT",)
    ),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


# ---- finding a card ----------------------------------------------------------

# "Gas[ ZTP][ <tier words>] <Maand> <jaar>", in a file name whose runs of
# spaces are collapsed first (the August 2026 names put two before the
# month). A name without a month ("Gas ZTP Wintervast 2025") is another
# product.
_FILE_RE = re.compile(
    r"\bGas(?: ZTP)?((?: \S+)*?) (" + "|".join(NL_MONTHS) + r") (20\d{2})\b", re.IGNORECASE
)


@dataclass(frozen=True, order=True)
class _Asset:
    month: date
    created: str
    url: str


def _assets(rows: list[dict[str, Any]], contract: _ContractDef) -> list[_Asset]:
    """The rows that are ``contract``'s cards, whatever month."""
    out: list[_Asset] = []
    for row in rows:
        name = " ".join(str(row.get("originalFilename", "")).split())
        match = _FILE_RE.search(name)
        url = row.get("url")
        if match is None or not isinstance(url, str) or not url.startswith("https://"):
            continue
        if match.group(1).strip() not in contract.files:
            continue
        month = MONTH_NAMES[match.group(2).lower()]
        out.append(_Asset(date(int(match.group(3)), month, 1), str(row.get("_createdAt", "")), url))
    return out


async def _query(session: aiohttp.ClientSession, query: str) -> list[dict[str, Any]]:
    body = await fetch_text(session, _SANITY_URL, params={"query": query})
    payload = parse_json(body, "Frank Energie: Sanity answer")
    result = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(result, list):
        raise ExtractorError("Frank Energie: Sanity answer has no result list")
    return [row for row in result if isinstance(row, dict)]


def _region(region: str) -> None:
    if region != REGION_FLANDERS:
        raise ExtractorError(f"Frank Energie: gas is not sold in region {region!r}")


class _OtherTierError(ExtractorError):
    """The card is another tier's than the one asked for."""


async def _read_month(
    session: aiohttp.ClientSession, contract: _ContractDef, region: str, assets: list[_Asset]
) -> SupplierSnapshot:
    """The tier's card among one month's uploads, newest upload first.

    A file named for one tier can carry another's card: "Gas ZTP Januari
    2026 v2.pdf" is the Korting card, uploaded after the standard tier's own.
    Only that is a reason to try the next upload; any other failure is the
    card's own.
    """
    for asset in sorted(assets, reverse=True):
        text = await fetch_pdf_text_layout(session, asset.url)
        try:
            return parse_snapshot(contract.contract_id, region, text, source_url=asset.url)
        except _OtherTierError:
            continue
    raise ExtractorError(f"Frank Energie: no {contract.label} card among the uploads")


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The card of the newest month ``contract_id``'s tier has one for."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Frank Energie")
    _region(region)
    # Five tiers a month: the last 40 uploads reach back further than any
    # re-upload has lagged.
    rows = await _query(
        session, _GAS_ASSETS + "]{originalFilename,url,_createdAt} | order(_createdAt desc)[0..39]"
    )
    assets = _assets(rows, contract)
    if not assets:
        raise ExtractorError(f"Frank Energie: no card found for {contract.label}")
    # Frank uploads a month's cards in the last days of the month before,
    # and until that month begins the running one's card is in force.
    months = {asset.month for asset in assets}
    newest = max((m for m in months if not future_month(m)), default=max(months))
    return await _read_month(session, contract, region, [a for a in assets if a.month == newest])


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card Frank published for ``year_month``, or None.

    The month is the one the file name gives, so no clock is involved; of
    several uploads the latest of the tier wins. A month with no card is
    None, only a transient failure raises, and a card naming another month
    is refused.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region != REGION_FLANDERS:
        return None
    wanted = date(year_month.year, year_month.month, 1)
    query = (
        _GAS_ASSETS
        + f' && originalFilename match "*{NL_MONTHS[wanted.month - 1].capitalize()}*"'
        + f' && originalFilename match "*{wanted.year}*"'
        + "]{originalFilename,url,_createdAt}"
    )
    return await month_card(_read_listed(session, contract, region, query, wanted), wanted)


async def _read_listed(
    session: aiohttp.ClientSession, contract: _ContractDef, region: str, query: str, wanted: date
) -> SupplierSnapshot | None:
    assets = [a for a in _assets(await _query(session, query), contract) if a.month == wanted]
    if not assets:
        return None
    return await _read_month(session, contract, region, assets)


async def probe(session: aiohttp.ClientSession, contract_id: str, region: str) -> str | None:
    """The upload time of the newest gas file, a new card changing it, and
    the running month, so a card uploaded before its month began is fetched
    once it begins.

    One short query, where reading a card takes half a minute of rendering
    on a Raspberry Pi.
    """
    if contract_id not in _CONTRACTS_BY_ID or region != REGION_FLANDERS:
        return None
    try:
        rows = await _query(session, _GAS_ASSETS + "]{_createdAt} | order(_createdAt desc)[0..0]")
    except ExtractorError:
        return None
    if not rows:
        return None
    return f"{rows[0].get('_createdAt')} {dt_util.now().date():%Y-%m}"


# ---- the card ----------------------------------------------------------------


def parse_snapshot(
    contract_id: str, region: str, text: str, *, source_url: str = _SANITY_URL
) -> SupplierSnapshot:
    """Parse one card's text as pdfplumber lays it out."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Frank Energie")
    _region(region)
    card_month = _card_month(text, contract)
    vat_rate = printed_vat_rate(text, _VAT_RE)
    if vat_rate is None:
        raise ExtractorError("Frank Energie: VAT rate not found")
    return SupplierSnapshot(
        supplier="frank",
        contract=contract_id,
        energy=_energy(text),
        dsos=_dsos(text),
        taxes=TaxOverlay(
            excise_bands=_excise(text),
            energy_contribution=_energy_contribution(text, card_month),
            card_vat_rate=vat_rate,
        ),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


# The title is the card's first line, its parts set apart by dashes:
# "Tariefkaart gas variabel contract" ("Tariefkaart gas variabel" from 1
# October 2026) and the month for the standard tier, "Frank Energie
# Variabel", the tier and the month for the others. The tier reads "HV ZTP",
# "JN", "Slim" or "Korting ZTP" ("VT ZTP" from October 2026), and "SL" or
# "Slim ZTP" on older Slim cards. It is the one place the card names its tier, so it is
# checked against the contract: HV, JN and the standard tier print different
# formulas. Nothing may follow the tier but "ZTP", which keeps out the
# January 2025 product whose title names both Korting and Slim. The year has
# to be whole: the March 2026 cards lost the last character of every line
# ("maart 202", "(EUR/maand 2,9" for 2,92) and are refused rather than read
# short.
_DASH = "[" + SIGN_CHARS + "]"
_TITLE_RE = re.compile(
    r"(?:Tariefkaart gas variabel(?: contract)?|Frank Energie Variabel\s*"
    + _DASH
    + r"\s*(\S+)(?:\s+ZTP)?)"
    r"\s*" + _DASH + r"\s*([a-z]+)\s+(\d{4})\s*",
    re.IGNORECASE,
)


def _card_month(text: str, contract: _ContractDef) -> date:
    title = text.lstrip().partition("\n")[0]
    match = _TITLE_RE.fullmatch(title.strip())
    month = MONTH_NAMES.get(fold_accents(match.group(2))) if match else None
    if match is None or month is None:
        raise ExtractorError(f"Frank Energie: card title {title!r} not understood")
    if (match.group(1) or "") not in contract.titles:
        raise _OtherTierError(f"Frank Energie: card {title!r} is not {contract.label}")
    return month_date(match.group(3), month, "Frank Energie")


_VAT_RE = re.compile(r"incl\.\s*(\d+)\s*%\s*btw")
_FEE_RE = re.compile(r"Abonnementskost \(EUR/maand\)\s+(\d+,\d+)")
_FORMULA_RE = re.compile(
    r"Formule Gasprijs:\s*\(\s*(\d+,\d+)\s*x\s*" + r"\s+".join(_INDEX.split()) + r"\s*"
    r"(" + _DASH + r")\s*(\d+(?:,\d+)?)\s*\)\s*x\s*(\d+,\d+)\s*in EURct/kWh"
)
# The regulator is "VNR" on the recent cards and "VREG", its old name, on
# the older ones.
_ESTIMATE_RE = re.compile(
    r"Verwacht volgens methode (?:VNR|VREG) voor [a-z]+ \d{4} \(EURct/kWh\)\s+(\d+,\d+)"
)


def _energy(text: str) -> IndexedRates:
    formula = _FORMULA_RE.search(text)
    estimate = _ESTIMATE_RE.search(text)
    fee = _FEE_RE.search(text)
    if formula is None or estimate is None or fee is None:
        raise ExtractorError("Frank Energie: formula, expected price or subscription not found")
    # EURct/kWh with the index in EUR/MWh, times the multiplier the formula
    # itself prints.
    vat = to_float(formula.group(4))
    base = parse_sign(formula.group(2)) * to_float(formula.group(3))
    return IndexedRates(
        factor=to_float(formula.group(1)) / 100.0 * vat,
        base=base / 100.0 * vat,
        index=_INDEX,
        price=to_float(estimate.group(1)) / 100.0,
        yearly_fixed_fee=to_float(fee.group(1)) * 12.0,
        formula=" ".join(formula.group(0).split()),
    )


# "Fluvius | Databeheer EUR/jaar | Transport EURct/kWh | Kleinverbruik
# Variabel, Vast | Gemiddeld verbruik Variabel, Vast", the areas without the
# "Fluvius" prefix.
_COLUMNS = (METERING, TRANSPORT, T1_PROP, T1_FIXED, T2_PROP, T2_FIXED)
_LABELS = {label.removeprefix("Fluvius "): key for label, key in FLUVIUS_LABELS.items()}
# The table comes out one figure per line under its area; joining every line
# that opens on a figure to the one above rebuilds the rows.
_FIGURE_LINE_RE = re.compile(r"\n[ \t]*(?=\d)")


def _dsos(text: str) -> dict[str, DsoOverlay]:
    # "N ettarieven": the heading's first letter is set apart.
    start = re.search(r"N\s?ettarieven", text)
    end = text.find("Informatie over uw tariefformule")
    if start is None or end < start.end():
        raise ExtractorError("Frank Energie: network table not found")
    dsos = read_dsos(
        _FIGURE_LINE_RE.sub(" ", text[start.end() : end]),
        _LABELS,
        _COLUMNS,
        supplier="Frank Energie",
    )
    require_region(dsos, REGION_FLANDERS, "Frank Energie")
    return dsos


# The lower band's figure falls on the next line.
_EXCISE_RE = re.compile(
    r"Bijzondere accijns op Energie \(EURct/kWh\) (kleiner|groter) dan 12\.000 kWh\s+(\d+,\d+)"
)
_CONTRIBUTION_RE = re.compile(r"Bijdrage op Energie \(EURct/kWh\)\s+(\d+,\d+)")


def _excise(text: str) -> tuple[tuple[float | None, float], ...]:
    rates = {m.group(1): to_float(m.group(2)) / 100.0 for m in _EXCISE_RE.finditer(text)}
    if set(rates) != {"kleiner", "groter"}:
        raise ExtractorError("Frank Energie: federal excise rows not found")
    return excise_bands(rates["kleiner"], rates["groter"])


def _energy_contribution(text: str, card_month: date) -> float:
    """The energy contribution as printed; Frank dropped the row from its
    August 2026 cards."""
    match = _CONTRIBUTION_RE.search(text)
    return printed_contribution(
        None if match is None else match.group(1), card_month, supplier="Frank Energie"
    )


# ---- index values ------------------------------------------------------------

_PERIOD_RE = re.compile(r"([A-Za-z]+) (20\d{2})")
_VALUE_RE = re.compile(r"\d+(?:[.,]\d+)?")


def parse_index_page(page: str) -> IndexTable:
    """The M ZTP RLP0N EOD EEX column of the terms page's "Index waarden"
    table, in EUR/MWh, month by month ("Augustus 2026" | ... | "61.9").

    The column is found by its heading, since the table carries four indices
    and has dropped one of them before (M TTF RLP0N EOD EEX, empty since June
    2024). Its figures are dot decimals, with the odd comma elsewhere in the
    table.
    """
    start = page.find("Index waarden")
    end = page.find("</table>", start)
    if start < 0 or end < 0:
        raise ExtractorError("Frank Energie: index table not found")
    column: int | None = None
    values: dict[str, float] = {}
    for cells in html_rows(page[start:end]):
        if column is None:
            if _INDEX in cells:
                column = cells.index(_INDEX)
            continue
        period = _PERIOD_RE.fullmatch(cells[0]) if cells else None
        month = MONTH_NAMES.get(period.group(1).lower()) if period else None
        if period is None or month is None or len(cells) <= column:
            raise ExtractorError(f"Frank Energie: unexpected index row {cells!r}")
        if _VALUE_RE.fullmatch(cells[column]):
            values[f"{period.group(2)}-{month:02d}"] = to_float(cells[column])
    if not values:
        raise ExtractorError(f"Frank Energie: no {_INDEX} values in the index table")
    return {_INDEX: values}


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """Frank's published M ZTP RLP0N EOD EEX values."""
    return parse_index_page(await fetch_text(session, _TERMS_URL))


EXTRACTOR = SupplierExtractor(
    id="frank",
    label="Frank Energie",
    contracts=tuple(
        Contract(id=c.contract_id, label=c.label, kind="indexed", regions=_REGIONS)
        for c in _CONTRACTS
    ),
    fetch=fetch,
    probe=probe,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=29.0,
)
