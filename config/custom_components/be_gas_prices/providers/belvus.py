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

"""Belvus gas card extractor.

Belvus publishes one card per product and month at a static path named by
the price month:

    https://www.belvus.be/public/tariefkaarten/<YYYY-MM>/Tariefkaart_<Product>_GAS.pdf

and lists every month since January 2026 on /historische-tariefkaarten,
newest first, which is how the current month's folder is found: the new
folder answers 404 until Belvus uploads it. The same path pattern is the
archive. Both residential gas products are Flanders only and indexed monthly
on TTF_RLP; the Pro twins are professional cards and are not read.

Up to August 2026 the card was a copy of the Energy Together template; from
September it has a layout of its own with the same wording and figures,
including the Fluvius labels printed out of order. :mod:`._energy_together`
reads both. The archive's January to March 2026 cards reprint a 2025
distribution table with a broken row and the April card a mangled one, so
the reader refuses those four months.

Belvus publishes no index values. The realised value of a month is printed
on the next month's card, as the one its "**" price is computed on
("laatst gekende waarde van TTF-DAM 8/2026: €61,729/MWh" on the September
card, "Belpex TTF-DAM" up to April), TTF-DAM naming the TTF_RLP the formula
uses: the "**" price is the formula at that value. So the index table is read
from the archived cards, each giving the month before its own, and only when
the month it names is that month.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

import aiohttp

from ..const import REGION_FLANDERS
from ._energy_together import INDEX, card_month, last_known_index, parse_card
from ._parse import require_contract
from ._pdf import fetch_pdf_text, fetch_text, is_transient_fetch_error
from ._rates import Contract
from ._validity import future_month, month_card
from .base import ExtractorError, IndexTable, SupplierExtractor, SupplierSnapshot

_HOST = "https://www.belvus.be"
_LISTING_URL = f"{_HOST}/historische-tariefkaarten"


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    file: str  # <Product> in the file name, which is also how the card names it


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("belvus_flex_online", "Belvus Flex Online", "FlexOnline"),
    _ContractDef("belvus_smart_plus", "Belvus Smart Plus", "SmartPlus"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _card_url(contract: _ContractDef, year: int, month: int) -> str:
    return f"{_HOST}/public/tariefkaarten/{year}-{month:02d}/Tariefkaart_{contract.file}_GAS.pdf"


def listed_months(page: str, contract: _ContractDef) -> list[date]:
    """Every month the listing links a card of ``contract`` for, newest first.
    A folder whose name is no month ("2026-13", "0000-09") is skipped rather
    than failing the listing."""
    pattern = rf"/public/tariefkaarten/(\d{{4}})-(\d{{2}})/Tariefkaart_{contract.file}_GAS\.pdf"
    months: set[date] = set()
    for year, month in re.findall(pattern, page):
        try:
            months.add(date(int(year), int(month), 1))
        except ValueError:
            continue
    return sorted(months, reverse=True)


def _contract(contract_id: str, region: str) -> _ContractDef:
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Belvus")
    if region != REGION_FLANDERS:
        raise ExtractorError(f"Belvus {contract_id}: not sold in region {region!r}")
    return contract


def parse_snapshot(contract_id: str, region: str, text: str, source_url: str) -> SupplierSnapshot:
    """Parse one card's text as pypdf extracts it, in either layout."""
    contract = _contract(contract_id, region)
    # The January to March 2026 cards reprint the 2025 distribution table
    # for months Fluvius billed on its 2026 tariffs, which the shared reader
    # refuses.
    return parse_card(
        text,
        supplier="belvus",
        label="Belvus",
        contract=contract_id,
        product=contract.file,
        source_url=source_url,
    )


async def _read(
    session: aiohttp.ClientSession, contract: _ContractDef, month: date
) -> SupplierSnapshot:
    url = _card_url(contract, month.year, month.month)
    return parse_snapshot(
        contract.contract_id, REGION_FLANDERS, await fetch_pdf_text(session, url), url
    )


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The newest card the listing links for ``contract_id``."""
    contract = _contract(contract_id, region)
    months = listed_months(await fetch_text(session, _LISTING_URL), contract)
    if not months:
        raise ExtractorError(f"Belvus: no {contract.file} gas card listed")
    return await _read(session, contract, months[0])


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card in the month's folder, or None.

    A month ahead of today in Home Assistant's zone is not asked for.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region != REGION_FLANDERS:
        return None
    if future_month(year_month):
        return None
    return await month_card(_read(session, contract, year_month), year_month)


# How many archived cards one index refresh reads: a year of delivery months.
_INDEX_MONTHS = 12


def index_value(text: str) -> tuple[str, float] | None:
    """The month and the TTF_RLP value a card states for the month before its
    own, or None when it states none or names another month."""
    card, _ = card_month(text, "Belvus")
    stated = last_known_index(text)
    if stated is None or stated[0] != (card - timedelta(days=1)).replace(day=1):
        return None
    return f"{stated[0]:%Y-%m}", stated[1]


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """TTF_RLP by month, from the last year of Flex Online cards."""
    contract = _CONTRACTS[0]
    months = listed_months(await fetch_text(session, _LISTING_URL), contract)
    values: dict[str, float] = {}
    for month in months[:_INDEX_MONTHS]:
        try:
            stated = index_value(
                await fetch_pdf_text(session, _card_url(contract, month.year, month.month))
            )
        except ExtractorError as err:
            # One dead link or unreadable card is no reason to lose every
            # other month; a supplier that is down is.
            if is_transient_fetch_error(str(err)):
                raise
            continue
        if stated is not None:
            values[stated[0]] = stated[1]
    if not values:
        raise ExtractorError("Belvus: no card states a TTF_RLP value")
    return {INDEX: values}


EXTRACTOR = SupplierExtractor(
    id="belvus",
    label="Belvus",
    contracts=tuple(
        Contract(
            id=c.contract_id,
            label=c.label,
            kind="indexed",
            regions=frozenset({REGION_FLANDERS}),
        )
        for c in _CONTRACTS
    ),
    fetch=fetch,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=0.5,
)
