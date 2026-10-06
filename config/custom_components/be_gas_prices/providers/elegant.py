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

"""Elegant gas tariff card extractor.

Elegant sells in Flanders only ("Sinds 2012 voor iedereen in Vlaanderen").
Its listing page, https://www.elegant.be/tariefkaarten, is server-rendered
Next.js. Since 1 October 2026 it links the current residential cards at a
stable address, overwritten in place:

    https://cdn.elegant.be/Pricing/TariffCharts/Current/<Product>Gas_Residential.pdf

Before, it linked them as DatoCMS assets, which is still understood:

    https://www.datocms-assets.com/198110/<upload id>-<product>gas_residential[-<MMYY>].pdf

The upload id is the upload's Unix time and cannot be guessed, so the
listing is read rather than a URL built.

Three products: Flex (open-ended) and ComfortFlex (one year) print the same
formula figure for figure, "(1,0250 x TTFDAM + 0,470) x 1,06", in c EUR/kWh
against the index in c EUR/kWh and with the VAT inside. The index is the
RLP-weighted TTF Day Ahead End Of Day value of the delivery month, which the
card calls TTFDAMRLP in its footnote and TTFDAM in the formula. The monthly
price it prints is the formula at the last known value, which the footnote
names ("de waarde van augustus 2026. Deze bedroeg 6,166 c EUR/kWh"). Zeker &
Vast is a one-year fixed price.

Past cards come from the archive the site's tarief-archief page queries:
the tRPC call ``tariefArchief.search`` returns the product offers in force on
a date, each with a ``tariffChartUrl`` that ``/api/tarief-archief/tariff-chart``
turns into the PDF. Zeker & Vast is reissued within a month when its price
moves (March 2026 has offers dated the 1st, the 6th and the 21st), so the
archive serves the card in force on the first day of the month. Before 2026
the offers carry other product keys (BEGreenFlexGas and the like) and a
combined electricity and gas card, which this does not read.

The index values come from the same site's ``energyExchanges`` tRPC calls
behind elegant.be/indexatie, the page the card refers to: one row per
delivery month. The answer names no unit; its 61,66 for August 2026 where
the card prints 6,166 c EUR/kWh makes it EUR/MWh.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.parse import quote

import aiohttp

from ..const import DSO_FLUVIUS_MIDDEN_VLAANDEREN, REGION_FLANDERS
from ._network import (
    FLUVIUS_LABELS,
    T1_FIXED,
    T1_PROP,
    T2_FIXED,
    T2_PROP,
    excise_bands,
    read_dsos,
    require_region,
)
from ._parse import fold_accents, month_date, require_contract, to_float
from ._pdf import (
    MONTH_NAMES,
    fetch_pdf_text_layout,
    fetch_text,
    head_freshness_key,
    printed_vat_rate,
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

_SITE = "https://www.elegant.be"
_LISTING_URL = f"{_SITE}/tariefkaarten"
_CURRENT_URL = "https://cdn.elegant.be/Pricing/TariffCharts/Current"
_ARCHIVE_SEARCH_URL = f"{_SITE}/api/trpc/tariefArchief.search"
_ARCHIVE_CHART_URL = f"{_SITE}/api/tarief-archief/tariff-chart"
_LIST_INDEXES_URL = f"{_SITE}/api/trpc/energyExchanges.listIndexes"
_GET_RATES_URL = f"{_SITE}/api/trpc/energyExchanges.getRates"
_INDEX = "TTFDAM"


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    kind: TariffKind
    # The product as the card's second line names it.
    name: str
    # The DatoCMS file name token, "<token>gas_residential".
    token: str
    # The archive's product offer key, "<key>_<YYYYMMDD>", and the current
    # card's file name, "<key>_Residential.pdf".
    archive_key: str


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("elegant_flex", "Elegant Flex", "indexed", "Flex", "flex", "FlexGas"),
    _ContractDef(
        "elegant_comfortflex",
        "Elegant ComfortFlex",
        "indexed",
        "ComfortFlex",
        "comfortflex",
        "ComfortFlexGas",
    ),
    _ContractDef(
        "elegant_zeker_vast",
        "Elegant Zeker & Vast",
        "fixed",
        "Zeker & Vast",
        "zekervast",
        "ZekerVastGas",
    ),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _contract(contract_id: str, region: str) -> _ContractDef:
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Elegant")
    if region != REGION_FLANDERS:
        raise ExtractorError(f"Elegant {contract_id}: not sold in region {region!r}")
    return contract


def _current_url(contract: _ContractDef) -> str:
    return f"{_CURRENT_URL}/{contract.archive_key}_Residential.pdf"


def _card_url(html: str, contract: _ContractDef) -> str:
    """The residential gas card the listing links for ``contract``: its
    stable address, or else the DatoCMS asset uploaded last.

    The address and the upload id are directly followed by the product, so
    "Flex" cannot pick up the ComfortFlex card.
    """
    current = _current_url(contract)
    if current in html:
        return current
    pattern = re.compile(
        rf"(https://www\.datocms-assets\.com/198110/(\d+)-{contract.token}"
        r"gas_residential(?:-\d{4})?\.pdf)"
    )
    found: dict[int, str] = {int(upload): url for url, upload in pattern.findall(html)}
    if not found:
        raise ExtractorError(f"Elegant: no {contract.name} gas card on the listing")
    return found[max(found)]


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The card the listing links today."""
    contract = _contract(contract_id, region)
    url = _card_url(await fetch_text(session, _LISTING_URL), contract)
    return await _read(session, contract_id, region, url)


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    text = await fetch_pdf_text_layout(session, url)
    return parse_snapshot(contract_id, region, text, source_url=url)


async def probe(session: aiohttp.ClientSession, contract_id: str, region: str) -> str | None:
    """The listing's ETag, which changes when the page is regenerated with
    new card links, and the current card's Last-Modified, which changes when
    the card at its stable address is overwritten."""
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region != REGION_FLANDERS:
        return None
    listing = await head_freshness_key(session, _LISTING_URL, prefer=("ETag",))
    card = await head_freshness_key(session, _current_url(contract))
    if listing is None and card is None:
        return None
    return f"{listing} {card}"


def _trpc_params(query: dict[str, Any]) -> dict[str, str]:
    """A tRPC GET query in the batch form the site's own pages send."""
    return {"batch": "1", "input": json.dumps({"0": query})}


def _trpc_data(body: str, label: str) -> dict[str, Any]:
    """The ``result.data`` object of a one-call tRPC batch answer, or raise."""
    try:
        data = json.loads(body)[0]["result"]["data"]
    except (ValueError, KeyError, IndexError, TypeError) as err:
        raise ExtractorError(f"Elegant: unexpected {label} answer") from err
    if not isinstance(data, dict):
        raise ExtractorError(f"Elegant: unexpected {label} answer")
    return data


def _trpc_list(body: str, key: str, label: str) -> list[Any]:
    """The list under ``key`` in a tRPC answer, empty where it is missing."""
    items = _trpc_data(body, label).get(key)
    if items is None:
        return []
    if not isinstance(items, list):
        raise ExtractorError(f"Elegant: unexpected {label} answer")
    return items


def _archived_chart_path(body: str, contract: _ContractDef) -> str | None:
    """The ``tariffChartUrl`` of ``contract`` in an archive search answer,
    or None where the date has no offer for it."""
    offers = _trpc_data(body, "archive search").get("productOffers")
    if not isinstance(offers, list):
        raise ExtractorError("Elegant: archive search answer has no offer list")
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        key = str(offer.get("productOfferKey", ""))
        if key.split("_", 1)[0] == contract.archive_key and "tariffChartUrl" in offer:
            return str(offer["tariffChartUrl"])
    return None


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card in force on the first day of ``year_month``, or None.

    A month the archive has no offer for, or only a legacy one, is None; so
    is a card that names another month. A transient failure raises so the
    month cache retries it.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region != REGION_FLANDERS:
        return None
    return await month_card(_read_month(session, contract, region, year_month), year_month)


async def _read_month(
    session: aiohttp.ClientSession, contract: _ContractDef, region: str, year_month: date
) -> SupplierSnapshot | None:
    query = {"date": f"{year_month:%Y-%m}-01", "energyType": "Gas", "customerType": "Residential"}
    body = await fetch_text(session, _ARCHIVE_SEARCH_URL, params=_trpc_params(query))
    path = _archived_chart_path(body, contract)
    if path is None:
        return None
    url = f"{_ARCHIVE_CHART_URL}?tariffChartPath={quote(path, safe='')}"
    return await _read(session, contract.contract_id, region, url)


def parse_index_id(body: str) -> int:
    """The id the index list gives TTFDAM, the name the formula prints.

    Looked up by name rather than kept as a number: the id is the site's
    database key, and a renumbering would otherwise hand back another
    index's values without a word.
    """
    for entry in _trpc_list(body, "indexes", "index list"):
        if isinstance(entry, dict) and entry.get("name") == _INDEX and "id" in entry:
            try:
                return int(entry["id"])
            except (TypeError, ValueError) as err:
                raise ExtractorError(f"Elegant: {_INDEX} has no usable id") from err
    raise ExtractorError(f"Elegant: index list has no {_INDEX}")


def parse_rates(body: str) -> IndexTable:
    """The TTFDAM values by delivery month, in EUR/MWh.

    Only rows spanning one calendar month count. The answer can carry stray
    ones: in September 2026 the rates filtered on 2026 ended with a one-day
    row for 1 January holding December's value, which read by its start
    would have replaced January's.
    """
    values: dict[str, float] = {}
    for rate in _trpc_list(body, "rates", "index rates"):
        try:
            start = datetime.fromisoformat(rate["startDate"]).date()
            end = datetime.fromisoformat(rate["endDate"]).date()
            price = float(rate["price"])
        except (KeyError, TypeError, ValueError):
            continue
        following = date(start.year + start.month // 12, start.month % 12 + 1, 1)
        if start.day == 1 and end == following:
            values[f"{start:%Y-%m}"] = price
    if not values:
        raise ExtractorError(f"Elegant: no monthly {_INDEX} value published")
    return {_INDEX: values}


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """Elegant's published TTFDAM values."""
    listing = await fetch_text(
        session, _LIST_INDEXES_URL, params=_trpc_params({"energyType": "Gas"})
    )
    query = {"exchangeId": parse_index_id(listing)}
    return parse_rates(await fetch_text(session, _GET_RATES_URL, params=_trpc_params(query)))


def parse_snapshot(
    contract_id: str,
    region: str,
    text: str,
    *,
    source_url: str = _LISTING_URL,
) -> SupplierSnapshot:
    """Parse one card's text as pdfplumber lays it out."""
    contract = _contract(contract_id, region)
    card_month = _check_heading(text, contract)
    return SupplierSnapshot(
        supplier="elegant",
        contract=contract_id,
        energy=_energy(text, contract),
        dsos=_dsos(text),
        taxes=TaxOverlay(
            excise_bands=_excise(text),
            energy_contribution=_energy_contribution(text),
            card_vat_rate=printed_vat_rate(text, _VAT_RE),
        ),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


# "Tariefkaart Aardgas", the product ("Flex", or "Flex 09.26" on an archived
# card), then "Variabel Onbepaalde duur Versie september 2026 Particulier".
_HEADING_RE = re.compile(
    r"Tariefkaart Aardgas\s*\n(?P<name>[^\n]+?)(?:\s+\d{2}\.\d{2})?\s*\n"
    r"[^\n]*?Versie\s+(?P<month>[A-Za-z]+)\s+(?P<year>\d{4})\s+(?P<segment>\w+)"
)


def _check_heading(text: str, contract: _ContractDef) -> date:
    """The card month, once the card is shown to be the product's own.

    Flex and ComfortFlex print the same figures, so nothing below the
    heading would tell one card from the other.
    """
    match = _HEADING_RE.search(text)
    month = MONTH_NAMES.get(fold_accents(match.group("month"))) if match else None
    if match is None or month is None:
        raise ExtractorError("Elegant: card heading not found")
    if match.group("name") != contract.name or match.group("segment") != "Particulier":
        raise ExtractorError(
            f"Elegant: card is for {match.group('name')} {match.group('segment')}, "
            f"not {contract.name} Particulier"
        )
    return month_date(match.group("year"), month, "Elegant")


_VAT_RE = re.compile(r"Prijzen inclusief (\d+)\s*% btw")
_FEE_RE = re.compile(r"Vaste vergoeding \(€/jaar\)\(\d+\)\s+(\d+,\d+)")
_PRICE_RE = re.compile(r"\(c€/kWh\)\s+(\d+,\d+)\s+Maandelijkse prijzen")
_FORMULA_RE = re.compile(r"\((\d+,\d+)\s*x\s*TTFDAM\s*\+\s*(\d+,\d+)\)\s*x\s*(\d+,\d+)")


def _energy(text: str, contract: _ContractDef) -> FixedRates | IndexedRates:
    fee = _FEE_RE.search(text)
    price = _PRICE_RE.search(text)
    if fee is None or price is None:
        raise ExtractorError("Elegant: energy price or fixed fee not found")
    if contract.kind == "fixed":
        return FixedRates(
            price=to_float(price.group(1)) / 100.0, yearly_fixed_fee=to_float(fee.group(1))
        )
    formula = _FORMULA_RE.search(text)
    if formula is None:
        raise ExtractorError("Elegant: TTFDAM formula not found")
    # c EUR/kWh against an index in c EUR/kWh: per EUR/MWh of index the factor
    # takes another tenth. The VAT is the multiplier the formula prints.
    vat = to_float(formula.group(3))
    return IndexedRates(
        factor=to_float(formula.group(1)) * vat / 1000.0,
        base=to_float(formula.group(2)) * vat / 100.0,
        index=_INDEX,
        price=to_float(price.group(1)) / 100.0,
        yearly_fixed_fee=to_float(fee.group(1)),
        formula=formula.group(0),
    )


# "Fluvius Antwerpen 15,68 2,26 83,22 0,91": per tier "vast (€/jaar)" then
# "var (c€/kWh)". The card abbreviates one area, "Fluvius Midden-Vl.", too
# far from the full name for the label matching to take it.
_COLUMNS = (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP)
_LABELS = {**FLUVIUS_LABELS, "Fluvius Midden-Vl.": DSO_FLUVIUS_MIDDEN_VLAANDEREN}
# Printed once below the table for every DSO.
_METERING_RE = re.compile(r"Tarief databeheer\s+(\d+,\d+)\s*€/jaar")
_TRANSPORT_RE = re.compile(r"Transportkosten\s+(\d+,\d+)\s*c€/kWh")


def _dsos(text: str) -> dict[str, DsoOverlay]:
    metering = _METERING_RE.search(text)
    transport = _TRANSPORT_RE.search(text)
    if metering is None or transport is None:
        raise ExtractorError("Elegant: data management or transport line not found")
    dsos = read_dsos(
        text,
        _LABELS,
        _COLUMNS,
        supplier="Elegant",
        after="Nettarieven",
        before="Tarief databeheer",
        transport=to_float(transport.group(1)) / 100.0,
        metering=to_float(metering.group(1)),
    )
    require_region(dsos, REGION_FLANDERS, "Elegant")
    return dsos


_EXCISE_LOW_RE = re.compile(r"Verbruik 0 - 12000 kWh\s+(\d+,\d+)\s*c€/kWh")
_EXCISE_HIGH_RE = re.compile(r"Verbruik > 12000 kWh\s+(\d+,\d+)\s*c€/kWh")


def _excise(text: str) -> tuple[tuple[float | None, float], ...]:
    low = _EXCISE_LOW_RE.search(text)
    high = _EXCISE_HIGH_RE.search(text)
    if low is None or high is None:
        raise ExtractorError("Elegant: federal excise rows not found")
    return excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0)


_CONTRIBUTION_RE = re.compile(r"Energiebijdrage\s+(\d+,\d+)\s*c€/kWh")


def _energy_contribution(text: str) -> float:
    """Printed 0,00000 since August 2026, when the law zeroed it, and
    0,10577 before. A card that drops the row follows the law, so a missing
    row is zero."""
    match = _CONTRIBUTION_RE.search(text)
    return 0.0 if match is None else to_float(match.group(1)) / 100.0


EXTRACTOR = SupplierExtractor(
    id="elegant",
    label="Elegant",
    contracts=tuple(
        Contract(
            id=c.contract_id,
            label=c.label,
            kind=c.kind,
            regions=frozenset({REGION_FLANDERS}),
        )
        for c in _CONTRACTS
    ),
    fetch=fetch,
    probe=probe,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=3.0,
)
