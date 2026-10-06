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

"""Bolt gas tariff card extractor.

Bolt prints one gas card per product for all three regions. The fixed
products roll monthly under a YYYYMM suffix:

    https://files.boltenergie.be/pricelists/fix/<fix|plenty_fix>_res_ng_fr_<YYYYMM>.pdf

The listing page https://www.boltenergie.be/fr/listes-des-prix links the
current card of each product, which is how :func:`fetch` finds it; the same
URL for an earlier month is the archive. The card says its price may change
within the month ("Le prix proposé peut évoluer dans le courant du mois"), and
the September 2026 card was last modified on the 14th, so the probe reads the
card's own Last-Modified rather than the listing's ETag.

Only Bolt Fixe and Plenty Fixe are supported. Bolt's variable gas cards
(Variable, Variable Online, Plenty Variable, Plenty Variable Online) bill each
day's consumption at that day's TTF day-ahead value, and the only daily
publication of it forbids reuse, so the maintainer decided not to support
them: they are not registered, and nothing here contacts EEX.

The two fixed cards print the same price and tables. Plenty Fixe charges a
lower platform fee (3,99 against 8,99 EUR a month in September 2026) and asks
for a share in the Plenty cooperative. The fee is billed per month and kept
here per year. Every figure is VAT inclusive ("TTC"); no rate is stated.

pdfplumber sets each table value on its own line after its label, so
:func:`_join_value_lines` puts every row back on one line before the shared
readers run. What the card prints, read as printed:

  - rows for Fluvius (Gaselwest), (Iveka), (Iverlek) and (Sibelgas), which
    no longer exist and carry transport only; they are ignored.
  - ORES proportional terms of 4,198 and 2,115 c EUR/kWh where the 2026 grid
    says 4,289 and 2,206. That grid with the regulatory balance term of CWaPE
    decision 1008, before decision 1146 of 16 October 2025 raised it, gives
    4,198 and 2,114.
  - RESA's mid-tier term 2,259, where the grid and every other card say
    2,529: most likely two digits swapped.
  - a single excise rate with no second band.
  - a Brussels levy table without the row above 160 m3/h.

The current three-page card starts with April 2026. The January and March
2026 cards checked are an older two-page template this module does not read,
so :func:`fetch_for_month` returns None for such months.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import aiohttp

from ..const import (
    DSO_RESA,
    DSO_SIBELGA,
    REGION_BRUSSELS,
    REGION_FLANDERS,
    REGION_WALLONIA,
    REGIONS,
)
from ._network import (
    FLUVIUS_LABELS,
    METERING,
    ORES_LABELS,
    T1_FIXED,
    T1_PROP,
    T2_FIXED,
    T2_PROP,
    TRANSPORT,
    excise_bands,
    osp_table,
    read_dsos,
    require_region,
)
from ._parse import cell_value, fold_accents, month_date, require_contract, to_float
from ._pdf import (
    MONTH_NAMES,
    fetch_pdf_text_layout,
    fetch_text,
    head_freshness_key,
)
from ._rates import Contract, FixedRates
from ._validity import end_of_month, month_card
from .base import (
    DsoOverlay,
    ExtractorError,
    SupplierExtractor,
    SupplierSnapshot,
    TaxOverlay,
)

_BASE_URL = "https://files.boltenergie.be/pricelists/fix"
_LISTING_URL = "https://www.boltenergie.be/fr/listes-des-prix"
_CARD_RE = re.compile(r"pricelists/fix/([a-z_]+)_res_ng_fr_(\d{6})\.pdf")

# A card is about 1.7 MB and Bolt's CDN is slow now and then.
_PDF_TIMEOUT = 60


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    slug: str  # file name prefix
    heading: str  # the product as the card's title prints it


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("bolt_fix", "Bolt Fixe", "fix", "Bolt Fixe"),
    _ContractDef("bolt_plenty_fix", "Bolt Plenty Fixe", "plenty_fix", "Plenty Fixe"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _card_url(contract: _ContractDef, month: str) -> str:
    return f"{_BASE_URL}/{contract.slug}_res_ng_fr_{month}.pdf"


async def _current_url(session: aiohttp.ClientSession, contract: _ContractDef) -> str:
    """The card the listing links for ``contract``, the latest month if it
    links several."""
    listing = await fetch_text(session, _LISTING_URL)
    months = [month for slug, month in _CARD_RE.findall(listing) if slug == contract.slug]
    if not months:
        raise ExtractorError(f"Bolt: the listing links no {contract.slug} gas card")
    return _card_url(contract, max(months))


def _check_region(region: str) -> None:
    if region not in REGIONS:
        raise ExtractorError(f"Bolt: unknown region {region!r}")


async def probe(session: aiohttp.ClientSession, contract_id: str, region: str) -> str | None:
    """The current card's Last-Modified, which moves when Bolt reissues the
    card within its month as well as when the month rolls over."""
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None:
        return None
    try:
        url = await _current_url(session, contract)
    except ExtractorError:
        return None
    return await head_freshness_key(session, url)


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The current card for ``contract_id``, read for ``region``."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Bolt")
    _check_region(region)
    return await _read(session, contract_id, region, await _current_url(session, contract))


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    text = await fetch_pdf_text_layout(session, url, timeout=_PDF_TIMEOUT)
    return parse_snapshot(contract_id, region, text, source_url=url)


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card Bolt published for a past month, or None.

    A month Bolt has no card for answers 404. A transient failure raises so
    the month cache retries it; any other failure, a card from the older
    template included, is a month with no card, and a card naming another
    month than the one asked for is refused.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region not in REGIONS:
        return None
    url = _card_url(contract, f"{year_month:%Y%m}")
    return await month_card(_read(session, contract_id, region, url), year_month)


# A line holding nothing but figures and dashes: the values pdfplumber sets
# on their own lines after the label they belong to.
_VALUES_ONLY_RE = re.compile(r"^\s*(?:\d+(?:[.,]\d+)*|-)(?:\s+(?:\d+(?:[.,]\d+)*|-))*\s*$")


def _join_value_lines(text: str) -> str:
    """``text`` with every line of bare values appended to the line above.

    The card's glyph stream breaks the line after each value, so a row comes
    out as its label and then one value per line, blank lines between rows.
    Rejoined, "Fluvius Imewo\\n 2,628\\n 18,61\\n ..." reads "Fluvius Imewo
    2,628 18,61 ...", which is the shape the shared readers expect.
    """
    lines: list[str] = []
    for line in text.replace("\u2028", "\n").splitlines():
        if not line.strip():
            continue
        if lines and _VALUES_ONLY_RE.match(line):
            lines[-1] = f"{lines[-1]} {line.strip()}"
        else:
            lines.append(line)
    return "\n".join(lines)


def parse_snapshot(
    contract_id: str, region: str, text: str, *, source_url: str = _LISTING_URL
) -> SupplierSnapshot:
    """Parse the card's text as pdfplumber lays it out, for one region."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Bolt")
    _check_region(region)
    text = _join_value_lines(text)
    card_month = _card_month(text, contract)
    return SupplierSnapshot(
        supplier="bolt",
        contract=contract_id,
        energy=_energy(text),
        dsos=_dsos(text, region),
        taxes=_taxes(text, region),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


# "Carte Tarifaire / Bolt Fixe / Septembre 2026 /Résidentiel /Gaz". The August
# 2026 card spells its month "Aôut", which folds to "aout" all the same.
_HEADING_RE = re.compile(r"Carte Tarifaire\s+(.+?)\s+(\S+)\s+(\d{4})\s*/Résidentiel\s*/Gaz")


def _card_month(text: str, contract: _ContractDef) -> date:
    """The month of the card's title, once the title names this product."""
    match = _HEADING_RE.search(text)
    if match is None:
        raise ExtractorError("Bolt: card title not found")
    if match.group(1) != contract.heading:
        raise ExtractorError(f"Bolt {contract.contract_id}: the card is for {match.group(1)}")
    month = MONTH_NAMES.get(fold_accents(match.group(2)))
    if month is None:
        raise ExtractorError(f"Bolt: card month {match.group(2)!r} not understood")
    return month_date(match.group(3), month, "Bolt")


_PRICE_RE = re.compile(r"Prix mensuel\s+(\d+,\d+)")
_FEE_RE = re.compile(r"€\s*(\d+(?:,\d+)?)\s*/\s*mois")


def _energy(text: str) -> FixedRates:
    price = _PRICE_RE.search(text)
    fee = _FEE_RE.search(text)
    if price is None or fee is None:
        raise ExtractorError("Bolt: price or platform fee not found")
    return FixedRates(
        price=to_float(price.group(1)) / 100.0,
        yearly_fixed_fee=to_float(fee.group(1)) * 12.0,
    )


# Per tier the proportional term then the fixed one, then transport and the
# metering fee ("-" in Wallonia).
_COLUMNS = (T1_PROP, T1_FIXED, T2_PROP, T2_FIXED, TRANSPORT, METERING)
_LABELS: dict[str, dict[str, str]] = {
    REGION_FLANDERS: FLUVIUS_LABELS,
    REGION_WALLONIA: {**ORES_LABELS, "TECTEO RESA": DSO_RESA},
    REGION_BRUSSELS: {"SIBELGA": DSO_SIBELGA},
}


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    dsos = read_dsos(
        text,
        _LABELS[region],
        _COLUMNS,
        supplier="Bolt",
        after="Distribution et transport",
        before="Taxes et redevances",
    )
    require_region(dsos, region, "Bolt")
    return dsos


# A levy row: its label, a footnote digit on some, then one value per region
# (Flandres, Wallonie, Bruxelles), each a figure with decimals or a dash. A
# row that lost a value does not match, rather than shifting the footnote
# digit into the Flanders column.
_TAX_VALUE = r"[ \t]+(\d+,\d+|-)"
_TAX_COLUMN = {REGION_FLANDERS: 0, REGION_WALLONIA: 1, REGION_BRUSSELS: 2}


def _tax_cell(text: str, label: str, region: str) -> float | None:
    """The region's value on the levy row ``label``, None for a dash."""
    match = re.search(rf"^{label}(?:[ \t]+\d)?{_TAX_VALUE * 3}[ \t]*$", text, re.MULTILINE)
    if match is None:
        raise ExtractorError(f"Bolt: levy row {label!r} not found")
    return cell_value(match.group(1 + _TAX_COLUMN[region]))


def _taxes(text: str, region: str) -> TaxOverlay:
    excise = _tax_cell(text, r"Accise fédérale \(c€/kWh\)", region)
    if excise is None:
        raise ExtractorError("Bolt: no excise for the region")
    # A dash is the card saying no contribution, which the law made so from
    # August 2026; the row itself is still required.
    contribution = _tax_cell(text, r"Contribution sur l.énergie \(c€/kWh\)", region)
    connection_fee = 0.0
    if region == REGION_WALLONIA:
        fee = _tax_cell(text, r"Redevance de raccordement \(c€/kWh\)", region)
        if fee is None:
            raise ExtractorError("Bolt: Walloon connection fee not found")
        connection_fee = fee / 100.0
    return TaxOverlay(
        excise_bands=excise_bands(excise / 100.0, None),
        energy_contribution=(contribution or 0.0) / 100.0,
        connection_fee=connection_fee,
        osp_by_caliber=_osp(text) if region == REGION_BRUSSELS else None,
    )


# "6 of 10 m3/h 4 3,56", "25m3/h 75,18": the caliber, a footnote digit on the
# two smallest-caliber rows, the amount.
_OSP_ROW_RE = re.compile(r"^(?:6 of 10|\d+) ?m3/h(?:[ \t]+\d)?[ \t]+(\d+,\d+)[ \t]*$", re.MULTILINE)


def _osp(text: str) -> dict[str, float]:
    start = text.find("Obligations de service publique")
    if start < 0:
        raise ExtractorError("Bolt: Brussels levy table not found")
    end = text.find("Informations sur les éléments", start)
    block = text[start:] if end < 0 else text[start:end]
    amounts = [to_float(value) for value in _OSP_ROW_RE.findall(block)]
    return osp_table(amounts, supplier="Bolt")


EXTRACTOR = SupplierExtractor(
    id="bolt",
    label="Bolt",
    contracts=tuple(Contract(id=c.contract_id, label=c.label, kind="fixed") for c in _CONTRACTS),
    fetch=fetch,
    probe=probe,
    fetch_for_month=fetch_for_month,
    sweep_cost_s=45.0,
)
