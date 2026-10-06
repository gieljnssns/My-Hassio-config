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

"""EnergyVision gas tariff card extractor, Brusol in Brussels.

EnergyVision sells gas only alongside an electricity contract ("Fossiel gas
mogelijk: in combinatie"), in two products: GSG, "Goedkope stroom - Gas",
indexed monthly, and GS1JVG, "Goedkope stroom 1 jaar vast - gas", fixed for
a year. Both have a Flemish card in Dutch and a Walloon one in French,
linked from https://www.energyvision.be/nl-be/tariefkaart as

    /sites/default/files/inline-files/EV-<MMYY>-<CODE>-<nl|WAL-fr>[_N].pdf

``_N`` is Drupal's suffix for a re-upload, so the current card is read off
the listing. In Brussels the company sells as Brusol, on brusol.be, and only
GSG, alongside its "Goedkope Stroom" electricity, which is "exclusief
voorbehouden aan eigenaars van Brusol-zonnepanelen". The Brussels card is
linked from the Goedkope Stroom signup page and filed under the month it was
uploaded: ``/sites/default/files/<YYYY-MM>/EV-<MMYY>-GSG-BXL-nl.pdf``.

GSG bills "1,02 x ZTP-RLP-M + 4,5 EUR/MWh", excluding VAT: the card states
only that its prices include 6%, and EnergyVision's parameter document says
the formulas on its cards are "steeds weergegeven exclusief btw". ZTP-RLP-M
is the RLP-weighted ZTP EGSI day-ahead mean of the delivery month. The price
the card prints is not the formula at the last known value but the VNR's
yearly estimate of it: 7,20 in September 2026 is the formula at 62,209, the
estimate the parameter document gives beside August's realised 61,822.

The realised values are published in that parameter document,
``inline-files/EV-<MMYY>-Indexatieparameters-nl.pdf``, linked from
https://www.energyvision.be/nl-be/indexatieparameters: page 5, "Fossiel gas
ZTP-RLP-M (EUR/MWh)", one row per month with the VNR estimate beside it.

Past cards resolve under their plain name: EnergyVision's for every month
from November 2025 on but GSG's January 2026, Brusol's in the upload folder
of the delivery month or of the month before. Where a month was uploaded
twice the two differ. EnergyVision's history page links a re-upload of the
August 2026 Walloon card (``_0``) that has the new excise but no connection
fee row, while the plain name has both old federal levies and the fee;
Brusol's August card sits in both folders and the later upload has the new
excise. The later Brusol one is tried first, the plain EnergyVision one is
the only one tried, and the law corrects the federal levies of both either
way.

Card errors this reads as printed and does not correct:

  - The September 2026 Walloon cards print the connection fee as 0,07500 c
    EUR/kWh, ten times the regulated 0,0075 that every other supplier
    prints and EnergyVision's own Walloon cards printed from November 2025
    to August 2026: the Walloon order of 19 June 2003 sets 0,00075 EUR/kWh
    for low-voltage electricity and 0,000075 for gas. The law's rate is
    billed for the months const.py knows it for (_resolve.py).
  - The Walloon GS1JVG cards of August and September 2026 print a single
    "Accise speciale 4,876 c EUR/kWh" instead of the two gas bands: the
    residential electricity excise since 1 August 2026, not a gas rate.
    The August one also has no connection fee row, which makes that card
    unreadable. The delivery months the gas excise law covers are billed
    at the law's rate regardless.
  - The Walloon distribution terms are cut to two decimals rather than
    rounded (ORES 4,28 where the CWaPE grid says 4,28944), and TECTEO RESA
    prints 5,25 / 3,14 / 2,86 on the February, May and June 2026 cards
    against 4,63 / 2,52 / 2,24 in the months between.
  - The Flemish GS1JVG card of April 2026 prints the excise the law set
    from August (1,09286 / 1,18296) and no energy contribution.
  - Cards before February 2026 print no transport term at all, so they are
    refused, and the Walloon cards of December 2025 to February 2026 were
    published in Dutch (``WAL-nl``), which this does not read.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import urljoin

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
from ._parse import fold_accents, require_contract, to_float
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

_SITE = "https://www.energyvision.be"
_LISTING_URL = f"{_SITE}/nl-be/tariefkaart"
_INDEX_PAGE_URL = f"{_SITE}/nl-be/indexatieparameters"
_BRUSOL_SITE = "https://www.brusol.be"
_BRUSOL_PAGE_URL = (
    f"{_BRUSOL_SITE}/nl/elektriciteit-en-gas/schrijf-je-in-voor-goedkope-stroom-van-brusol"
)
_INDEX = "ZTP-RLP-M"


@dataclass(frozen=True)
class _Card:
    """Where one region's card of a product is published."""

    # The file name token after the product code.
    token: str
    site: str
    # The page that links the current card.
    page: str
    # Brusol files a card under the month it uploaded it; EnergyVision keeps
    # every month in one folder.
    upload_folders: bool = False


_FLANDERS_CARD = _Card("nl", _SITE, _LISTING_URL)
_WALLONIA_CARD = _Card("WAL-fr", _SITE, _LISTING_URL)
_BRUSSELS_CARD = _Card("BXL-nl", _BRUSOL_SITE, _BRUSOL_PAGE_URL, upload_folders=True)


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    kind: TariffKind
    code: str
    cards: Mapping[str, _Card]


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef(
        "energyvision_gas",
        "EnergyVision Goedkope stroom - Gas",
        "indexed",
        "GSG",
        {
            REGION_FLANDERS: _FLANDERS_CARD,
            REGION_WALLONIA: _WALLONIA_CARD,
            REGION_BRUSSELS: _BRUSSELS_CARD,
        },
    ),
    # Not in Brussels: Brusol's page links no GS1JVG card and the name it
    # would carry answers 404 in both upload folders.
    _ContractDef(
        "energyvision_gas_1_jaar_vast",
        "EnergyVision Goedkope stroom 1 jaar vast - Gas",
        "fixed",
        "GS1JVG",
        {REGION_FLANDERS: _FLANDERS_CARD, REGION_WALLONIA: _WALLONIA_CARD},
    ),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _contract(contract_id: str, region: str) -> tuple[_ContractDef, _Card]:
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "EnergyVision")
    card = contract.cards.get(region)
    if card is None:
        raise ExtractorError(f"EnergyVision {contract_id}: not sold in region {region!r}")
    return contract, card


def _card_url(html: str, contract: _ContractDef, card: _Card) -> str:
    """The newest card of ``contract`` for ``card`` that ``html`` links.

    The href is site-relative on EnergyVision's listing and absolute on
    Brusol's page. The token follows the product code directly, so the
    Flemish "nl" cannot pick up a "BXL-nl" or "WAL-nl" card.
    """
    pattern = re.compile(
        r'href="((?:https?://[^"/]+)?/sites/default/files/[^"]*?'
        rf'EV-(\d{{2}})(\d{{2}})-{contract.code}-{re.escape(card.token)}[^"/]*\.pdf)"'
    )
    found: dict[tuple[int, int], str] = {
        (int(year), int(month)): href for href, month, year in pattern.findall(html)
    }
    if not found:
        raise ExtractorError(
            f"EnergyVision: no {contract.code} {card.token} card linked from {card.page}"
        )
    return urljoin(card.page, found[max(found)])


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The card the region's page links today."""
    contract, card = _contract(contract_id, region)
    return await _read(
        session,
        contract_id,
        region,
        _card_url(await fetch_text(session, card.page), contract, card),
    )


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    text = await fetch_pdf_text_layout(session, url)
    return parse_snapshot(contract_id, region, text, source_url=url)


async def probe(session: aiohttp.ClientSession, contract_id: str, region: str) -> str | None:
    """The ETag of the page that links the card. EnergyVision's listing
    sends one; Brusol's page sends neither header, which leaves Brussels on
    the time-based refresh."""
    contract = _CONTRACTS_BY_ID.get(contract_id)
    card = None if contract is None else contract.cards.get(region)
    if card is None:
        return None
    return await head_freshness_key(session, card.page, prefer=("ETag", "Last-Modified"))


def _archive_urls(contract: _ContractDef, card: _Card, month: date) -> tuple[str, ...]:
    """Where the card for ``month`` (a first of the month) can sit, in the
    order to try them."""
    name = f"EV-{month:%m%y}-{contract.code}-{card.token}.pdf"
    if not card.upload_folders:
        return (f"{card.site}/sites/default/files/inline-files/{name}",)
    previous = month - timedelta(days=1)
    return tuple(
        f"{card.site}/sites/default/files/{folder:%Y-%m}/{name}" for folder in (month, previous)
    )


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card published for ``year_month``, or None.

    A name that does not resolve, a card that does not parse and a card for
    another month all move on to the next candidate; a transient failure
    raises so the month cache retries the month.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    card = None if contract is None else contract.cards.get(region)
    if contract is None or card is None:
        return None
    first = date(year_month.year, year_month.month, 1)
    for url in _archive_urls(contract, card, first):
        snapshot = await month_card(_read(session, contract_id, region, url), first)
        if snapshot is not None:
            return snapshot
    return None


_INDEX_PDF_RE = re.compile(
    r'href="((?:https?://[^"/]+)?/sites/default/files/[^"]*?EV-\d{4}-Indexatieparameters-nl[^"/]*\.pdf)"'
)


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """ZTP-RLP-M by month, off the parameter document the index page links."""
    match = _INDEX_PDF_RE.search(await fetch_text(session, _INDEX_PAGE_URL))
    if match is None:
        raise ExtractorError("EnergyVision: no parameter document linked")
    url = urljoin(_INDEX_PAGE_URL, match.group(1))
    return parse_index_document(await fetch_pdf_text_layout(session, url))


# One month of the gas table: the realised value, then the VNR estimate.
# Months not published yet print nothing and the oldest print "/ /". A row
# with a single figure would not say which column it is in, so it does not
# match.
_INDEX_ROW_RE = re.compile(r"^([A-Za-z]+) (20\d{2}) (\d+[.,]\d+) (\d+[.,]\d+)$", re.MULTILINE)


def parse_index_document(text: str) -> IndexTable:
    """The gas table of the parameter document as pdfplumber lays it out.

    The electricity tables before it have rows of the same shape, so the
    read starts at the gas heading and stops at that page's footer. A value
    may be printed with a dot ("Maart 2026 50.358").
    """
    start = text.find("ZTP-RLP-M (EUR/MWh)")
    if start < 0:
        raise ExtractorError("EnergyVision: gas index table not found")
    end = text.find("EnergyVision NV", start)
    values: dict[str, float] = {}
    for name, year, realised, _estimate in _INDEX_ROW_RE.findall(
        text[start : end if end >= 0 else None]
    ):
        month = MONTH_NAMES.get(name.lower())
        if month is not None:
            values[f"{year}-{month:02d}"] = to_float(realised)
    if not values:
        raise ExtractorError("EnergyVision: gas index table has no values")
    return {_INDEX: values}


def parse_snapshot(
    contract_id: str,
    region: str,
    text: str,
    *,
    source_url: str = _LISTING_URL,
) -> SupplierSnapshot:
    """Parse one card's text as pdfplumber lays it out."""
    contract, _card = _contract(contract_id, region)
    card_month = _card_month(text)
    vat_rate = printed_vat_rate(text, *_VAT_RES)
    if vat_rate is None:
        raise ExtractorError("EnergyVision: VAT statement not found")
    return SupplierSnapshot(
        supplier="energyvision",
        contract=contract_id,
        energy=_energy(text, contract, 1.0 + vat_rate),
        dsos=_dsos(text, region),
        taxes=TaxOverlay(
            excise_bands=_excise(text),
            energy_contribution=_energy_contribution(text),
            connection_fee=_connection_fee(text) if region == REGION_WALLONIA else 0.0,
            osp_by_caliber=_osp(text) if region == REGION_BRUSSELS else None,
            card_vat_rate=vat_rate,
        ),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


# "Tariefkaart september 2026" or "Carte tarifaire septembre 2026".
_CARD_MONTH_RE = re.compile(r"(?:Tariefkaart|Carte tarifaire)\s+([A-Za-zÀ-ÿ]+)\s+(20\d{2})")


def _card_month(text: str) -> date:
    match = _CARD_MONTH_RE.search(text)
    month = MONTH_NAMES.get(fold_accents(match.group(1))) if match else None
    if match is None or month is None:
        raise ExtractorError("EnergyVision: card month not found")
    return date(int(match.group(2)), month, 1)


# "Alle prijzen en tarieven zijn inclusief 6% BTW", "Tous les prix et tarifs
# incluent la TVA à 6 %".
_VAT_RES = (re.compile(r"inclusief (\d+)\s*% BTW"), re.compile(r"TVA à (\d+)\s*%"))
# "Fossiel gas – variabel 7,20€cent/kWh", "Gaz fossile – fixe 7,96 €cent/kWh";
# Brusol prints a hyphen for the dash.
_ENERGY_RE = re.compile(
    r"(?:Fossiel gas|Gaz fossile)\s*[–-]\s*(variabel|variable|vast|fixe)\s+(\d+,\d+)\s*€cent/kWh"
)
_FEE_RE = re.compile(r"(?:Vaste vergoeding|Frais fixes)\s+(\d+(?:,\d+)?)\s*€/(?:jaar|an)")
_FORMULA_RE = re.compile(r"(\d+(?:,\d+)?)\s*x\s*ZTP-RLP-M\s*\+\s*(\d+(?:,\d+)?)\s*EUR/MWh")


def _energy(text: str, contract: _ContractDef, vat: float) -> FixedRates | IndexedRates:
    energy = _ENERGY_RE.search(text)
    fee = _FEE_RE.search(text)
    if energy is None or fee is None:
        raise ExtractorError("EnergyVision: energy price or fixed fee not found")
    # The price row names the product's kind, which is what tells the fixed
    # card from the variable one; the history page has filed one as the other.
    fixed = energy.group(1) in ("vast", "fixe")
    if fixed != (contract.kind == "fixed"):
        raise ExtractorError(f"EnergyVision: {energy.group(0)!r} is not a {contract.code} card")
    price = to_float(energy.group(2)) / 100.0
    if fixed:
        return FixedRates(price=price, yearly_fixed_fee=to_float(fee.group(1)))
    formula = _FORMULA_RE.search(text)
    if formula is None:
        raise ExtractorError("EnergyVision: ZTP-RLP-M formula not found")
    # EUR/MWh excluding VAT: per EUR/MWh of index the factor is a thousandth
    # of a EUR/kWh, grossed by the card's rate.
    return IndexedRates(
        factor=to_float(formula.group(1)) * vat / 1000.0,
        base=to_float(formula.group(2)) * vat / 1000.0,
        index=_INDEX,
        price=price,
        yearly_fixed_fee=to_float(fee.group(1)),
        formula=formula.group(0),
    )


_WALLONIA_LABELS = {
    "BRABANT WALLON": DSO_ORES,
    "HAINAUT GAZ": DSO_ORES,
    "ORES LUXEMBOURG": DSO_ORES,
    "MOUSCRON": DSO_ORES,
    "NAMUR": DSO_ORES,
    "TECTEO RESA": DSO_RESA,
}
# Each region's table in its own column order. Flanders: per tier "Vaste
# vergoeding" then "Afname", then databeheer and transport. Wallonia: per
# tier "Consommation" then "Terme fixe", then transport, no metering.
# Brussels: per tier "Afname" then "Vaste vergoeding", then transport and
# the metering fee last.
_TABLES: dict[str, tuple[str, Mapping[str, str], Sequence[str]]] = {
    REGION_FLANDERS: (
        "Vlaams Gewest",
        FLUVIUS_LABELS,
        (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, METERING, TRANSPORT),
    ),
    REGION_WALLONIA: (
        "la Région Wallonne",
        _WALLONIA_LABELS,
        (T1_PROP, T1_FIXED, T2_PROP, T2_FIXED, T3_PROP, T3_FIXED, TRANSPORT),
    ),
    REGION_BRUSSELS: (
        "Transport- en distributiekosten",
        {"SIBELGA": DSO_SIBELGA},
        (T1_PROP, T1_FIXED, T2_PROP, T2_FIXED, T3_PROP, T3_FIXED, TRANSPORT, METERING),
    ),
}


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    after, labels, columns = _TABLES[region]
    dsos = read_dsos(text, labels, columns, supplier="EnergyVision", after=after)
    require_region(dsos, region, "EnergyVision")
    return dsos


# The two bands, worded differently over the months: "Verbruik tussen 0 &
# 12.000 kWh", then "Verbruik boven 12.000 kWh", "Verbruik tussen 12.000 &
# 150.000 kWh", "Consommation au-dessus de 12 000 kWh" and more.
_EXCISE_RE = re.compile(
    r"^(?:Verbruik|Consommation) (?:tussen|entre) 0 & 12[ .]000 kWh (\d+,\d+)[^\n]*\n"
    r"(?:Verbruik|Consommation) [^\n]*?12[ .]000[^\n]*? kWh (\d+,\d+)",
    re.MULTILINE,
)
_SINGLE_EXCISE_RE = re.compile(r"Accise spéciale (\d+,\d+)\s*€cent/kWh")


def _excise(text: str) -> tuple[tuple[float | None, float], ...]:
    bands = _EXCISE_RE.search(text)
    if bands is not None:
        return excise_bands(to_float(bands.group(1)) / 100.0, to_float(bands.group(2)) / 100.0)
    # The Walloon fixed card's single rate, which is not a gas excise; see
    # the module docstring.
    single = _SINGLE_EXCISE_RE.search(text)
    if single is None:
        raise ExtractorError("EnergyVision: federal excise rows not found")
    return excise_bands(to_float(single.group(1)) / 100.0, None)


_CONTRIBUTION_RE = re.compile(r"(?:Energiebijdrage|Contribution énergétique) (\d+,\d+)")


def _energy_contribution(text: str) -> float:
    """0,10577 up to July 2026 on every card but the April GS1JVG one. The
    law zeroed the levy from August and the cards dropped the row, so a
    missing row is zero."""
    match = _CONTRIBUTION_RE.search(text)
    return 0.0 if match is None else to_float(match.group(1)) / 100.0


_CONNECTION_FEE_RE = re.compile(r"Redevance de raccordement (\d+,\d+)")


def _connection_fee(text: str) -> float:
    """The Walloon connection fee as printed, which from September 2026 is
    ten times the regulated one; see the module docstring."""
    match = _CONNECTION_FEE_RE.search(text)
    if match is None:
        raise ExtractorError("EnergyVision: Walloon connection fee row not found")
    return to_float(match.group(1)) / 100.0


# "<= 10 m3/h 2 3,56": the smallest caliber carries its footnote digit
# inline, so the amount is the row's last figure.
_OSP_ROW_RE = re.compile(r"^(?:<=|Tussen|>)[^\n]*?m3/h[^\n]*?\s(\d+,\d+)\s*$", re.MULTILINE)


def _osp(text: str) -> dict[str, float]:
    start = text.find("openbaredienstverplichtingen")
    if start < 0:
        raise ExtractorError("EnergyVision: Brussels levy table not found")
    amounts = [to_float(value) for value in _OSP_ROW_RE.findall(text[start:])]
    return osp_table(amounts, supplier="EnergyVision")


EXTRACTOR = SupplierExtractor(
    id="energyvision",
    label="EnergyVision",
    contracts=tuple(
        Contract(id=c.contract_id, label=c.label, kind=c.kind, regions=frozenset(c.cards))
        for c in _CONTRACTS
    ),
    fetch=fetch,
    probe=probe,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=4.5,
)
