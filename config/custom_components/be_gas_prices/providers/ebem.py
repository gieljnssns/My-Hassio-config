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

"""EBEM gas tariff card extractor.

EBEM (Merksplas) sells two residential gas products in Flanders, both
open-ended and variable: Aardgas Variabel and G@S+, the web-only one. They
share one monthly PDF, linked from the tariff page under an opaque media
folder that changes with every file:

    https://www.ebem.be/tarieven/
        /media/<hash>/ebem_tariefkaart-gas-MM-YYYY.pdf

The same page keeps every past month, which makes it the archive. Names
before 2025 break the pattern (``gas-10-2024_web2.pdf``,
``gas-09-20244_web.pdf``, ``gas-mei-2023_web.pdf``), and those cards print
the Fluvius areas that no longer exist, so they are left alone.

Both products index on ZTP weighted by the average Flemish RLP ("ZTP" over
"RLP0" in the formula cell): 0,105 ZTP + base in c EUR/kWh excluding VAT,
with ZTP in EUR/MWh. The card cannot know the delivery month's value ("Voor
de huidige maand is deze index nog niet gekend"), so it prints the formula
at the previous month's value ("Vorige maand bedroeg deze index 61,82"),
excluding and including VAT, and again at a VNR estimate. The first is the
figure at a known index and is what is read.

The realised values are in EBEM's own parameters document, linked from the
same page (``ebem_parameters_indexen-MM-YYYY.pdf``), page 4, column "Argus
ZTP-RLP" ("Argus ZTP-RPL" until September 2026). Every month from December
2024 to August 2026 it holds is the figure the following card names as the
previous month's.

The network table is printed VAT inclusive with transport in EUR/MWh.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import aiohttp

from ..const import REGION_FLANDERS
from ._network import (
    FLUVIUS_LABELS,
    METERING,
    T1_FIXED,
    T1_PROP,
    T2_FIXED,
    T2_PROP,
    T3_FIXED,
    T3_PROP,
    TRANSPORT_MWH,
    excise_bands,
    read_dsos,
    require_region,
)
from ._parse import SIGN_CHARS, fold_accents, month_date, parse_sign, require_contract, to_float
from ._pdf import (
    MONTH_NAMES,
    fetch_pdf_text_layout,
    fetch_text,
    printed_vat_rate,
)
from ._rates import Contract, IndexedRates
from ._validity import end_of_month, month_card
from .base import (
    DsoOverlay,
    ExtractorError,
    IndexTable,
    SupplierExtractor,
    SupplierSnapshot,
    TaxOverlay,
)

_LISTING_URL = "https://www.ebem.be/tarieven/"
_SITE = "https://www.ebem.be"
_CARD_RE = re.compile(r'href="(/media/[^"]+/ebem_tariefkaart-gas-(\d{2})-(\d{4})\.pdf)"')
_PARAMETERS_RE = re.compile(r'href="(/media/[^"]+/ebem_parameters_indexen-(\d{2})-(\d{4})\.pdf)"')

# The index as EBEM defines it ("De gewogen parameter ZTP-RLP0"), and the
# name fetch_index files it under.
_INDEX = "ZTP-RLP0"

_REGIONS = frozenset({REGION_FLANDERS})


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    title: str  # how the card heads the product's block


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("ebem_variable", "EBEM Aardgas Variabel", "Aardgas Variabel"),
    _ContractDef("ebem_gas_plus", "EBEM G@S+", "G@S+"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _links(page: str, pattern: re.Pattern[str]) -> dict[date, str]:
    """The listing's documents of one kind by month. A name that is no month
    ("-13-2026", "-09-0000") is skipped rather than failing the listing."""
    links: dict[date, str] = {}
    for path, month, year in pattern.findall(page):
        try:
            links[month_date(year, month, "EBEM")] = _SITE + path
        except ExtractorError:
            continue
    return links


def _latest(page: str, pattern: re.Pattern[str], what: str) -> str:
    links = _links(page, pattern)
    if not links:
        raise ExtractorError(f"EBEM: no {what} linked on {_LISTING_URL}")
    return links[max(links)]


def _region(region: str) -> None:
    if region != REGION_FLANDERS:
        raise ExtractorError(f"EBEM: gas is not sold in region {region!r}")


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The newest card on the listing, read for ``contract_id``."""
    require_contract(_CONTRACTS_BY_ID, contract_id, "EBEM")
    _region(region)
    url = _latest(await fetch_text(session, _LISTING_URL), _CARD_RE, "gas card")
    return await _read(session, contract_id, region, url)


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(
        contract_id, region, await fetch_pdf_text_layout(session, url), source_url=url
    )


async def _read_month(
    session: aiohttp.ClientSession, contract_id: str, region: str, year_month: date
) -> SupplierSnapshot | None:
    page = await fetch_text(session, _LISTING_URL)
    url = _links(page, _CARD_RE).get(date(year_month.year, year_month.month, 1))
    if url is None:
        return None
    return await _read(session, contract_id, region, url)


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card EBEM published for ``year_month``, or None.

    The listing names each card by its month, so no clock is involved. A
    month it does not link is a month with no card; only a transient failure
    raises, so the month cache retries it. A card naming another month than
    its file name is refused.
    """
    if contract_id not in _CONTRACTS_BY_ID or region != REGION_FLANDERS:
        return None
    return await month_card(_read_month(session, contract_id, region, year_month), year_month)


def parse_snapshot(
    contract_id: str, region: str, text: str, *, source_url: str = _LISTING_URL
) -> SupplierSnapshot:
    """Parse one card's text as pdfplumber lays it out."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "EBEM")
    _region(region)
    block, network = _split(text, contract)
    card_month = _card_month(block, contract)
    vat_rate = printed_vat_rate(block, _VAT_RE)
    if vat_rate is None:
        raise ExtractorError("EBEM: VAT rate not found")
    return SupplierSnapshot(
        supplier="ebem",
        contract=contract_id,
        energy=_energy(block, 1.0 + vat_rate),
        dsos=_dsos(network),
        taxes=TaxOverlay(
            excise_bands=_excise(network),
            energy_contribution=_energy_contribution(network),
            card_vat_rate=vat_rate,
        ),
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


_HEADING = "TARIEFKAART EBEM "
_NETWORK = "Nettarieven aardgas"


def _split(text: str, contract: _ContractDef) -> tuple[str, str]:
    """The product's own block of the card, and the shared network and tax
    part below both blocks.

    Each block runs from its "TARIEFKAART EBEM <product>" heading to the next
    heading or to the network table, whichever comes first, so a block never
    lends the other product its formula.
    """
    start = text.find(_HEADING + contract.title)
    network = text.find(_NETWORK)
    if start < 0 or network < start:
        raise ExtractorError(f"EBEM: no {contract.title} block on the card")
    end = text.find(_HEADING, start + len(_HEADING))
    if end < 0 or end > network:
        end = network
    return text[start:end], text[network:]


# "TARIEFKAART EBEM Aardgas Variabel_26_04 september 2026", a version code
# glued to the product; the 2025 cards put a dash before the month
# ("G@S+_24_01 - januari 2025").
_MONTH_RE = re.compile(r"\S*\s+(?:-\s+)?([a-z]+)\s+(\d{4})\b", re.IGNORECASE)


def _card_month(block: str, contract: _ContractDef) -> date:
    match = _MONTH_RE.match(block, len(_HEADING + contract.title))
    month = MONTH_NAMES.get(fold_accents(match.group(1))) if match else None
    if match is None or month is None:
        raise ExtractorError(f"EBEM: {contract.title} card month not found")
    return month_date(match.group(2), month, "EBEM")


_VAT_RE = re.compile(r"INCL\.\s*BTW\s*(\d+)\s*%")
# "0,105 ZTP +0,675 7,1661 c€/kWh 7,5961 c€/kWh 7,2070 c€/kWh 7,6394 c€/kWh":
# the formula, then the price excluding and including VAT at the previous
# month's index, then both at the VNR estimate. G@S+ prints its second figure
# as "7,5431 €/kWh" and some months drop the space before the unit.
_UNIT = r"\s*c?€/kWh\s+"
_ENERGY_RE = re.compile(
    r"(\d+,\d+)\s*ZTP\s*([" + SIGN_CHARS + r"])\s*(\d+,\d+)\s+"
    r"(\d+,\d+)" + _UNIT + r"(\d+,\d+)" + _UNIT + r"(\d+,\d+)" + _UNIT + r"(\d+,\d+)"
)
# "Vaste vergoeding 66,04 €/jaar 70,00 €/jaar", excluding then including VAT.
_FEE_RE = re.compile(r"Vaste vergoeding\s+(\d+,\d+)\s*€/jaar\s+(\d+,\d+)\s*€/jaar")


def _energy(block: str, vat: float) -> IndexedRates:
    energy = _ENERGY_RE.search(block)
    fee = _FEE_RE.search(block)
    if energy is None or fee is None:
        raise ExtractorError("EBEM: energy price row or fixed fee not found")
    base = parse_sign(energy.group(2)) * to_float(energy.group(3))
    return IndexedRates(
        # c EUR/kWh per EUR/MWh of ZTP, excluding VAT, grossed by the card's
        # printed rate.
        factor=to_float(energy.group(1)) / 100.0 * vat,
        base=base / 100.0 * vat,
        index=_INDEX,
        price=to_float(energy.group(5)) / 100.0,
        yearly_fixed_fee=to_float(fee.group(2)),
        formula=f"{energy.group(1)} ZTP {energy.group(2)}{energy.group(3)} c€/kWh excl. BTW",
    )


# "NETBEHEERDER | T1 VAST VARIABEL | T2 VAST VARIABEL | T3 VAST VARIABEL |
# TARIEF DATABEHEER | TRANSPORT EUR/MWh": fixed before proportional within
# each tier.
_COLUMNS = (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, T3_FIXED, T3_PROP, METERING, TRANSPORT_MWH)
# The 2025 cards print Antwerpen's T2 fixed term as "75 ,60", which would
# split into two cells.
_SPLIT_DECIMAL_RE = re.compile(r"(\d) ,(\d)")


def _dsos(network: str) -> dict[str, DsoOverlay]:
    dsos = read_dsos(
        _SPLIT_DECIMAL_RE.sub(r"\1,\2", network),
        FLUVIUS_LABELS,
        _COLUMNS,
        supplier="EBEM",
        after="NETBEHEERDER",
        before="Belastingen, heffingen",
    )
    require_region(dsos, REGION_FLANDERS, "EBEM")
    return dsos


# "Staffel Huishoudelijk (incl BTW) 0-12 MWh 1,09286 c€/kWh ... 12-20.000 MWh
# 1,18296 c€/kWh", each on its own line between the lines of a paragraph.
_EXCISE_LOW_RE = re.compile(r"^0-12 MWh (\d+,\d+) c€/kWh$", re.MULTILINE)
_EXCISE_HIGH_RE = re.compile(r"^12-20\.000 MWh (\d+,\d+) c€/kWh$", re.MULTILINE)
_CONTRIBUTION_RE = re.compile(r"Huishoudelijk:\s*(\d+,\d+)\s*c€/kWh")


def _excise(network: str) -> tuple[tuple[float | None, float], ...]:
    low = _EXCISE_LOW_RE.search(network)
    high = _EXCISE_HIGH_RE.search(network)
    if low is None or high is None:
        raise ExtractorError("EBEM: federal excise rows not found")
    return excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0)


def _energy_contribution(network: str) -> float:
    match = _CONTRIBUTION_RE.search(network)
    if match is None:
        raise ExtractorError("EBEM: energy contribution not found")
    return to_float(match.group(1)) / 100.0


# ---- index values ------------------------------------------------------------

# "Argus ZTP-RPL" until the September 2026 document, "Argus ZTP-RLP" from
# October. The bare "ZTP-RLP" is no anchor: it is in the text above the
# table and would lead to the simulator's estimates.
_INDEX_HEADING_RE = re.compile(r"Argus ZTP-R(?:PL|LP)\b")
# "maand 2022 2023 maand 2024 2025 2026": the Argus table is the second one.
_YEARS_RE = re.compile(r"^maand (?:\d{4} )+maand ((?:\d{4} ?)+)$", re.MULTILINE)
_EMPTY_RE = re.compile(r"\.{3,}")


def parse_parameters(text: str) -> IndexTable:
    """The Argus ZTP-RLP table of EBEM's parameters document, in EUR/MWh.

    Page 4 prints it to the right of the TTF101 table, one line per month
    for both: "juni 93,05595 31,32900 juni 34,08 35,66 44,70". Its values
    follow the month name's second occurrence, one per year heading, with a
    run of dots for a month not over yet.
    """
    heading = _INDEX_HEADING_RE.search(text)
    years = _YEARS_RE.search(text, heading.start()) if heading is not None else None
    if years is None:
        raise ExtractorError("EBEM: Argus ZTP-RLP table not found")
    headings = years.group(1).split()
    values: dict[str, float] = {}
    for line in text[years.end() :].splitlines():
        words = line.split()
        month = MONTH_NAMES.get(words[0]) if words else None
        if month is None:
            if values:
                break
            continue
        cells = words[words.index(words[0], 1) + 1 :] if words.count(words[0]) == 2 else []
        if len(cells) != len(headings):
            raise ExtractorError(f"EBEM: unexpected Argus ZTP-RLP row {line!r}")
        for year, cell in zip(headings, cells, strict=True):
            if not _EMPTY_RE.fullmatch(cell):
                values[f"{year}-{month:02d}"] = to_float(cell)
    if not values:
        raise ExtractorError("EBEM: Argus ZTP-RLP table is empty")
    return {_INDEX: values}


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """EBEM's published ZTP-RLP0 values, from its newest parameters document."""
    url = _latest(await fetch_text(session, _LISTING_URL), _PARAMETERS_RE, "parameters document")
    return parse_parameters(await fetch_pdf_text_layout(session, url))


EXTRACTOR = SupplierExtractor(
    id="ebem",
    label="EBEM",
    contracts=tuple(
        Contract(id=c.contract_id, label=c.label, kind="indexed", regions=_REGIONS)
        for c in _CONTRACTS
    ),
    fetch=fetch,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=7.0,
)
