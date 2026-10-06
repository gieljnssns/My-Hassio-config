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

"""Mega gas tariff card extractor.

Mega publishes one card per (product, region) on its own CDN:

    https://my.mega.be/resources/tarif/Mega-FR-NG-B2C-<BX|VL|WL>-<MMYYYY>-<Suffix>.pdf

The suffix carries the product and, on most products, the day and month the
card took effect ("Smart0109", "Cosy0809", "Zen0109-Fixed"), while a few
carry no date at all ("Prepaid", "Offpeak-Bi-Var"). It cannot be predicted,
and gas suffixes are not the electricity ones (Online Flex is "Online0109"
here, "Online0109-Green" there), so the current card is found on the public
listing, https://www.mega.be/fr/energie/cartes-tarifaires, where every card
link carries a ``data-product-element="<Product>"`` attribute.

The CDN keeps past months under the same grammar, which is the archive
(Smart Flex reaches back to January 2024 at least). The listing points at
the latest issue of a month, and Mega reissues some cards mid-month: in
September 2026 Cosy Flex and Smart Fixed went from "...0109" (published on
31 and 27 August) to "...0809" (7 September), with the same tariff and a
larger first-year ristourne. A reissue's day does not carry over to other
months ("Cosy0808" for August is the CDN's HTML stub, "Cosy0108" the card),
while every month checked has an issue dated the 1st, so a past month is
asked for as issued on the 1st.

Every figure is 6% VAT inclusive. The Flex products index monthly on the
arithmetic mean of the EGSI day-ahead and weekend assessments of ZTP or TTF
over the delivery month, known only once the month is over. The formula is
printed excluding VAT, in c EUR/kWh with the index in c EUR/kWh ("ZTP x 1,08
+ 1,15 c EUR/kWh"). The headline price is a forecast over the next twelve
months; the card also prints its formula at the last month the index is
known for ("pour le mois de aout 2026 ... Compteur mono-horaire : 8.28"),
which is the price read here. Mega publishes both indices month by month on
its indexation page as "ZTP mensuel" and "TTF1", in EUR/kWh excluding VAT,
and that price is the formula at the page's value to the card's rounding.

The first-year ristourne most cards offer (a c EUR/kWh and a fixed fee
reduction capped at 848 EUR, or a flat amount on the Off-peak cards) is a
one-off credit granted after twelve or fourteen months and is not part of
the tariff, so it is not read.

Mega's CDN sends the cards with a bogus "Content-Encoding: UTF-8" header,
which aiohttp ignores as an encoding it does not know.
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
)
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
    excise_bands,
    osp_table,
    read_dsos,
    require_region,
)
from ._parse import SIGN_CHARS, html_cells, month_date, parse_sign, require_contract, to_float
from ._pdf import fetch_pdf_text, fetch_text, printed_vat_rate
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

_LISTING_URL = "https://www.mega.be/fr/energie/cartes-tarifaires"
_INDEX_URL = "https://www.mega.be/fr/energie/indexation-de-nos-produits-variables"

_REGION_TO_CODE: dict[str, str] = {
    REGION_FLANDERS: "VL",
    REGION_WALLONIA: "WL",
    REGION_BRUSSELS: "BX",
}


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    kind: TariffKind
    listing_name: str  # the data-product-element value on the listing
    card_name: str  # the name the card prints, less its term ("2Y")
    regions: frozenset[str] = ALL_REGIONS


# Every residential gas product on the listing. There is no Dynamic gas card,
# and Off-peak Impact has a Walloon card only, priced like Off-peak Flex. The
# listing also links two SME cards, which are professional and not listed
# here.
_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("mega_smart_flex", "Mega Smart Flex", "indexed", "Smart Flex", "Smart Flex"),
    _ContractDef("mega_cosy_flex", "Mega Cosy Flex", "indexed", "Cosy Flex", "Cosy Flex"),
    _ContractDef("mega_online_flex", "Mega Online Flex", "indexed", "Online Flex", "Online Flex"),
    _ContractDef(
        "mega_prepaid_flex", "Mega Prepaid Flex", "indexed", "Prepaid Flex", "Prepaid Flex"
    ),
    _ContractDef(
        "mega_offpeak_flex", "Mega Off-peak Flex", "indexed", "Off-peak Flex", "Offpeak Flex"
    ),
    _ContractDef(
        "mega_offpeak_impact",
        "Mega Off-peak Impact",
        "indexed",
        "Off-peak Impact",
        "Offpeak Impact Flex",
        regions=frozenset({REGION_WALLONIA}),
    ),
    _ContractDef("mega_smart_fixed", "Mega Smart Fixed", "fixed", "Smart Fixed", "Smart Fixed"),
    _ContractDef("mega_cosy_fixed", "Mega Cosy Fixed", "fixed", "Cosy Fixed", "Cosy Fixed"),
    _ContractDef("mega_online_fixed", "Mega Online Fixed", "fixed", "Online Fixed", "Online Fixed"),
    _ContractDef(
        "mega_prepaid_fixed", "Mega Prepaid Fixed", "fixed", "Prepaid Fixed", "Prepaid Fixed"
    ),
    _ContractDef(
        "mega_offpeak_fixed", "Mega Off-peak Fixed", "fixed", "Off-peak Fixed", "Offpeak Fixed"
    ),
    _ContractDef("mega_zen_fixed", "Mega Zen Fixed", "fixed", "Zen Fixed", "Zen Fixed"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _region_code(contract: _ContractDef, region: str) -> str:
    if region not in contract.regions:
        raise ExtractorError(f"Mega {contract.contract_id}: not sold in region {region!r}")
    return _REGION_TO_CODE[region]


def _listed_url(listing: str, contract: _ContractDef, code: str) -> str | None:
    """The link the listing carries for ``contract``'s gas card in the
    region ``code``, pinned to that segment, so the electricity card and
    the other regions' links of the same product never match."""
    match = re.search(
        r'data-product-element="' + re.escape(contract.listing_name) + r'"[^>]*?'
        r'href="(https://my\.mega\.be/resources/tarif/Mega-FR-NG-B2C-'
        + code
        + r'-\d{6}-[^"]+\.pdf)"',
        listing,
    )
    return None if match is None else match.group(1)


def card_url(listing: str, contract_id: str, region: str) -> str:
    """The URL of the card the listing links for ``contract_id`` in ``region``.

    Mega drops one region's block of a product from the listing now and then
    while still publishing its card: the electricity listing lost Dynamic
    Wallonia overnight in July 2026. The regional cards differ only by their
    -B2C-<code>- segment, so another region's link is rewritten for it. That
    is a guess at the URL: a card not published there fails its download,
    and a card of another region fails ``require_region``.
    """
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Mega")
    code = _region_code(contract, region)
    url = _listed_url(listing, contract, code)
    if url is not None:
        return url
    for other in _REGION_TO_CODE.values():
        sibling = None if other == code else _listed_url(listing, contract, other)
        if sibling is not None:
            return sibling.replace(f"-NG-B2C-{other}-", f"-NG-B2C-{code}-", 1)
    raise ExtractorError(f"Mega {contract_id}: no {code} card on the listing")


_URL_MONTH_RE = re.compile(r"-(\d{2})(\d{4})-(?=[^/]*\.pdf$)")


def archive_url(current: str, year_month: date) -> str:
    """The URL of the same card as first issued for ``year_month``.

    Both months in the filename move: the ``-MMYYYY-`` segment and the month
    of the suffix's issue date, whose day becomes the 1st. A suffix with no
    date is left alone. The current month keeps the listing's own URL, which
    is its latest issue.
    """
    match = _URL_MONTH_RE.search(current)
    if match is None:
        raise ExtractorError(f"Mega: no month in card URL {current}")
    if (int(match.group(2)), int(match.group(1))) == (year_month.year, year_month.month):
        return current
    target = f"{year_month.month:02d}"
    head = current[: match.start()] + f"-{target}{year_month.year}-"
    tail = re.sub(
        rf"(?<=[A-Za-z])\d{{2}}{match.group(1)}(?=[-.])",
        f"01{target}",
        current[match.end() :],
        count=1,
    )
    return head + tail


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The card the listing links today for ``contract_id`` in ``region``."""
    url = card_url(await fetch_text(session, _LISTING_URL), contract_id, region)
    return await _read(session, contract_id, region, url)


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(contract_id, region, await fetch_pdf_text(session, url), source_url=url)


async def _read_month(
    session: aiohttp.ClientSession, contract_id: str, region: str, year_month: date
) -> SupplierSnapshot:
    listing = await fetch_text(session, _LISTING_URL)
    url = archive_url(card_url(listing, contract_id, region), year_month)
    return await _read(session, contract_id, region, url)


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card Mega published for a past month, or None.

    The URL is built off the listing's current one, so a product Mega no
    longer lists has no archive here. A month ahead of Home Assistant's
    clock is refused rather than asked for. A transient failure raises so
    the month cache retries it; any other failure, the HTML stub the CDN
    serves for a card it never published included, is a month with no card,
    and a card naming another month than the one asked for is refused too.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region not in contract.regions:
        return None
    if future_month(year_month):
        return None
    return await month_card(_read_month(session, contract_id, region, year_month), year_month)


_FIG = r"\d+(?:[.,]\d+)?"


def parse_snapshot(
    contract_id: str, region: str, text: str, *, source_url: str = _LISTING_URL
) -> SupplierSnapshot:
    """Parse one regional card's text as pypdf extracts it."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Mega")
    _region_code(contract, region)
    flat = " ".join(text.split())
    _check_product(text, contract)
    card_month = _card_month(flat)
    vat_rate = printed_vat_rate(flat, r"TVA\s+(\d+(?:[.,]\d+)?)\s*%\s+incluse")
    if vat_rate is None:
        raise ExtractorError("Mega: VAT statement not found")
    bands, contribution = _excise(text, flat)
    return SupplierSnapshot(
        supplier="mega",
        contract=contract_id,
        energy=_energy(text, flat, contract, 1.0 + vat_rate),
        dsos=_dsos(text, region),
        taxes=TaxOverlay(
            excise_bands=bands,
            energy_contribution=contribution,
            connection_fee=_connection_fee(text) if region == REGION_WALLONIA else 0.0,
            osp_by_caliber=_osp(text) if region == REGION_BRUSSELS else None,
            card_vat_rate=vat_rate,
        ),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


# "Gaz naturel / Smart Flex 2Y / (Variable)". The term is not part of the
# name: the January 2025 card printed "Smart Flex" alone.
_PRODUCT_RE = re.compile(r"Gaz naturel\s*\n(.+)\n\s*\((?:Variable|Fixe)\)")


def _check_product(text: str, contract: _ContractDef) -> None:
    """Refuse a card printed for another product than ``contract``.

    An archive URL is built rather than linked, so the card it lands on is
    checked for the product it prices before any figure is trusted.
    """
    match = _PRODUCT_RE.search(text)
    if match is None:
        raise ExtractorError("Mega: product name not found")
    printed = re.sub(r"\s+\d+Y$", "", match.group(1).strip())
    if printed != contract.card_name:
        raise ExtractorError(f"Mega {contract.contract_id}: card is for {printed!r}")


_CARD_MONTH_RE = re.compile(r"Prix du mois (\d{2})/(\d{4})")


def _card_month(flat: str) -> date:
    """The month the card is for: "Prix du mois 09/2026"."""
    match = _CARD_MONTH_RE.search(flat)
    if match is None or not 1 <= int(match.group(1)) <= 12:
        raise ExtractorError("Mega: card month not found")
    return month_date(match.group(2), match.group(1), "Mega")


_PRICE_RE = re.compile(rf"Coût énergie \(c€/kWh\)\s*\n\s*({_FIG})\s*\n")
_FEE_RE = re.compile(rf"Redevance fixe \(€/an\)\s*\n\s*({_FIG})\s*\n")
_FORMULA_RE = re.compile(
    rf"formule tarifaire pour le gaz est la suivante \(HTVA\) ?: "
    rf"((ZTP|TTF) x ({_FIG}) ([{SIGN_CHARS}]) ({_FIG}) c€/kWh)"
)
# The index the formula names, as the card defines it. It has to be the
# definition of the series Mega's indexation page publishes under the name
# mapped below, or the price would be resolved against another index.
_INDEX_DEFINITION_RE = re.compile(
    r"moyenne arithmétique des cotations journalières Day Ahead et Weekend "
    r"(ZTP|TTF) \(EGSI\) durant le mois de fourniture"
)
_INDEX_NAMES: dict[str, str] = {"ZTP": "ZTP mensuel", "TTF": "TTF1"}
# "Les derniers prix constates ... pour le mois de aout 2026 (...) sont les
# suivants (c EUR/kWh) : Compteur mono-horaire : 8.28." The label wraps at
# its hyphen.
_LAST_KNOWN_RE = re.compile(
    rf"derniers prix constatés .{{0,600}}?sont les suivants \(c€/kWh\) : "
    rf"Compteur mono- ?horaire : ({_FIG})"
)


def _energy(text: str, flat: str, contract: _ContractDef, vat: float) -> FixedRates | IndexedRates:
    price = _PRICE_RE.search(text)
    fee = _FEE_RE.search(text)
    if price is None or fee is None:
        raise ExtractorError("Mega: energy price block not found")
    yearly_fee = to_float(fee.group(1))
    if contract.kind == "fixed":
        return FixedRates(price=to_float(price.group(1)) / 100.0, yearly_fixed_fee=yearly_fee)

    formula = _FORMULA_RE.search(flat)
    definition = _INDEX_DEFINITION_RE.search(flat)
    if formula is None or definition is None:
        raise ExtractorError("Mega: indexation formula not found")
    if formula.group(2) != definition.group(1):
        raise ExtractorError("Mega: the formula and its index definition disagree")
    # The price at the last month the index is known for is a fact; the
    # headline is a twelve-month forecast, kept for a card that stops
    # printing the other.
    last_known = _LAST_KNOWN_RE.search(flat)
    printed = last_known.group(1) if last_known else price.group(1)
    base = parse_sign(formula.group(4)) * to_float(formula.group(5))
    return IndexedRates(
        # c EUR/kWh on an index in c EUR/kWh is EUR/kWh per 1000 EUR/MWh.
        factor=to_float(formula.group(3)) / 1000.0 * vat,
        base=base / 100.0 * vat,
        index=_INDEX_NAMES[formula.group(2)],
        price=to_float(printed) / 100.0,
        yearly_fixed_fee=yearly_fee,
        formula=formula.group(1),
    )


# The distribution table as the header prints it: the three proportional
# terms (c EUR/kWh) then the three fixed ones (EUR/year), then Flanders's
# data management or Brussels's yearly metering fee. Wallonia has neither.
_TIERS = (T1_PROP, T2_PROP, T3_PROP, T1_FIXED, T2_FIXED, T3_FIXED)
_COLUMNS: dict[str, tuple[str, ...]] = {
    REGION_FLANDERS: (*_TIERS, METERING),
    REGION_WALLONIA: _TIERS,
    REGION_BRUSSELS: (*_TIERS, METERING),
}
_LABELS: dict[str, dict[str, str]] = {
    REGION_FLANDERS: FLUVIUS_LABELS,
    REGION_WALLONIA: {**ORES_LABELS, "RESA": DSO_RESA},
    REGION_BRUSSELS: {"Sibelga": DSO_SIBELGA},
}
_FIGURE_LINE_RE = re.compile(_FIG)
_TRANSPORT_RE = re.compile(rf"Coût du transport\s*\n\s*({_FIG})\s*\n")


def _table_rows(text: str) -> str:
    """The distribution table with each row on one line.

    pypdf gives one cell per line, the label first and wrapped where it is
    long ("ORES (Brabant" / "wallon)", "Fluvius Halle-" / "Vilvoorde"). A
    figure joins the row above it, and a line after a label left open by a
    hyphen or a parenthesis completes that label. The header's own wrapped
    lines end up as rows of the wrong width, which the readers skip.
    """
    start = text.find("Prix de la distribution et du transport")
    end = text.find("Taxes, redevances", start)
    if start < 0 or end < 0:
        raise ExtractorError("Mega: distribution table not found")
    rows: list[str] = []
    open_label = False
    for raw in text[start:end].splitlines():
        line = raw.strip()
        if not line:
            continue
        if rows and _FIGURE_LINE_RE.fullmatch(line):
            rows[-1] += " " + line
        elif open_label:
            rows[-1] += line if rows[-1].endswith("-") else " " + line
        else:
            rows.append(line)
        open_label = rows[-1].endswith("-") or rows[-1].count("(") > rows[-1].count(")")
    return "\n".join(rows)


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    # Transport is one Fluxys figure, printed once for every DSO.
    transport = _TRANSPORT_RE.search(text)
    if transport is None:
        raise ExtractorError("Mega: transport cost not found")
    dsos = read_dsos(
        _table_rows(text),
        _LABELS[region],
        _COLUMNS[region],
        supplier="Mega",
        transport=to_float(transport.group(1)) / 100.0,
    )
    require_region(dsos, region, "Mega")
    return dsos


# One excise row per slice, followed on the cards printed before August 2026
# by the energy contribution in a column of its own.
_EXCISE_ROW = rf"\s*\n\s*({_FIG})(?:\s*\n\s*({_FIG}))?\s*\n"
_EXCISE_LOW_RE = re.compile(r"Consommation entre 0 et 12\.000 kWh" + _EXCISE_ROW)
_EXCISE_HIGH_RE = re.compile(r"Consommation de plus de 12\.000 kWh" + _EXCISE_ROW)
_CONTRIBUTION_ZERO = "La contribution énergétique est fixée à 0"


def _excise(text: str, flat: str) -> tuple[tuple[tuple[float | None, float], ...], float]:
    """The excise bands and the energy contribution, both in EUR/kWh.

    A card without the contribution column states the levy is zero, and
    one stating neither is a layout change rather than a zero.
    """
    low = _EXCISE_LOW_RE.search(text)
    high = _EXCISE_HIGH_RE.search(text)
    if low is None or high is None:
        raise ExtractorError("Mega: federal excise rows not found")
    bands = excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0)
    if low.group(2) != high.group(2):
        raise ExtractorError("Mega: the energy contribution differs between the slices")
    if low.group(2) is not None:
        return bands, to_float(low.group(2)) / 100.0
    if _CONTRIBUTION_ZERO not in flat:
        raise ExtractorError("Mega: energy contribution not found")
    return bands, 0.0


_CONNECTION_FEE_RE = re.compile(rf"Redevance de raccordement\s*\n\s*({_FIG})\s*\n")


def _connection_fee(text: str) -> float:
    """The Walloon connection fee: a Walloon card without the row is a
    layout change, not a fee of zero."""
    match = _CONNECTION_FEE_RE.search(text)
    if match is None:
        raise ExtractorError("Mega: Walloon connection fee row not found")
    return to_float(match.group(1)) / 100.0


# "6 ou 10 m / 3 / /heure* / 3.56": the caliber, its unit split around the
# superscript, the footnote marks, then the amount on a line of its own.
_OSP_AMOUNT_RE = re.compile(rf"^/heure\**\s*\n\s*({_FIG})\s*$", re.MULTILINE)


def _osp(text: str) -> dict[str, float]:
    start = text.find("Obligations de Service Public")
    end = text.find("Lorsque la dernière consommation", start)
    if start < 0 or end < 0:
        raise ExtractorError("Mega: Brussels levy table not found")
    amounts = [to_float(value) for value in _OSP_AMOUNT_RE.findall(text[start:end])]
    return osp_table(amounts, supplier="Mega")


_INDEX_ROW_RE = re.compile(r'<tr data-line="([^"]+)"[^>]*>(.*?)</tr>', re.DOTALL)
_MONTH_START_RE = re.compile(r"01-(0[1-9]|1[0-2])-(\d{4})")
_INDEX_VALUE_RE = re.compile(r"€\s*(\d+[.,]\d+)")


def parse_index_page(page: str) -> IndexTable:
    """Mega's monthly ZTP and TTF values, by delivery month, in EUR/MWh.

    One row per month, newest first: "01-08-2026 | 01-09-2026 | EUR0.0617121"
    in EUR/kWh excluding VAT. A row that does not run from the first of a
    month to the first of the next is not a monthly value and is skipped.
    """
    table: IndexTable = {name: {} for name in _INDEX_NAMES.values()}
    for name, row in _INDEX_ROW_RE.findall(page):
        if name not in table:
            continue
        cells = html_cells(row)
        if len(cells) != 3:
            continue
        start = _MONTH_START_RE.fullmatch(cells[0])
        end = _MONTH_START_RE.fullmatch(cells[1])
        value = _INDEX_VALUE_RE.fullmatch(cells[2])
        if start is None or end is None or value is None:
            continue
        year, month = int(start.group(2)), int(start.group(1))
        if (int(end.group(2)), int(end.group(1))) != (year + month // 12, month % 12 + 1):
            continue
        table[name][f"{year}-{month:02d}"] = to_float(value.group(1)) * 1000.0
    missing = sorted(name for name, values in table.items() if not values)
    if missing:
        raise ExtractorError(f"Mega: index values not found: {', '.join(missing)}")
    return table


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """Mega's published gas index values."""
    return parse_index_page(await fetch_text(session, _INDEX_URL))


EXTRACTOR = SupplierExtractor(
    id="mega",
    label="Mega",
    contracts=tuple(
        Contract(id=c.contract_id, label=c.label, kind=c.kind, regions=c.regions)
        for c in _CONTRACTS
    ),
    fetch=fetch,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=2.1,
)
