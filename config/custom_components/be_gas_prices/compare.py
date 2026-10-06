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

"""Quoting other contracts against this household.

A quote is a year of the household's gas on a contract's current card: the
annual volume at today's all-in price plus a year of fixed costs, on the
household's own DSO, tier and meter caliber. Every row is priced the same
way, which is what makes the rows comparable: an indexed contract at the
last index value its supplier has published, a fixed one at its price. Both
are what a household signing today would see on the card, not a forecast.

The one-off quote, the ranked comparison and the daily ranking all go
through :func:`quote_contract`.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

import aiohttp

from .bill import bill_month
from .const import SUPPLIER_CUSTOM
from .month_cards import current_card
from .pricing import PricingError
from .providers import all_extractors
from .providers._pdf import memoise_text_fetches
from .providers._rates import IndexedRates
from .providers.base import ExtractorError, IndexTable, SupplierExtractor, SupplierSnapshot
from .running_costs import Household

_LOGGER = logging.getLogger(__name__)

# How many cards the ranking fetches at once. Enough to overlap the network,
# few enough that a Raspberry Pi parsing PDFs stays responsive.
_CONCURRENCY = 3


@dataclass(frozen=True)
class Quote:
    """One contract priced for the household, or why it could not be."""

    supplier: str
    contract: str
    label: str
    annual_cost: float | None
    all_in: float | None
    fixed: float | None
    indexed: bool
    provisional: bool
    error: str | None = None
    # Priced on the card archive's OCR reading of a card published as images.
    read_by_ocr: bool = False


@dataclass(frozen=True)
class OwnContract:
    """The household's own contract and the card it is quoted on: its card
    of the month with the energy leg the entry is billed on (the signing
    card's, the figures typed from the contract), or the typed card of a
    custom entry."""

    extractor: SupplierExtractor
    contract: str
    card: SupplierSnapshot
    # The card is the card archive's reading of one published as images.
    read_by_ocr: bool = False
    # The supplier's index values the entry prices on, which picked the
    # card's energy leg: the comparison prices the contract on them too.
    table: IndexTable | None = None


class IndexCache:
    """Each supplier's index table, fetched once per comparison."""

    def __init__(self, own: OwnContract | None = None) -> None:
        self._tables: dict[str, IndexTable | None] = {}
        # The entry's own table where it holds one; without one, the
        # supplier's is fetched like any other.
        if own is not None and own.table is not None:
            self._tables[own.extractor.id] = own.table
        self._lock = asyncio.Lock()

    async def table(
        self, session: aiohttp.ClientSession, extractor: SupplierExtractor
    ) -> IndexTable | None:
        async with self._lock:
            if extractor.id not in self._tables:
                table: IndexTable | None = None
                if extractor.fetch_index is not None:
                    try:
                        table = await extractor.fetch_index(session)
                    except ExtractorError as err:
                        _LOGGER.debug("%s index values unavailable: %s", extractor.label, err)
                self._tables[extractor.id] = table
            return self._tables[extractor.id]


async def quote_contract(
    session: aiohttp.ClientSession,
    extractor: SupplierExtractor,
    contract: str,
    region: str,
    household: Household,
    month: str,
    indices: IndexCache,
    *,
    use_archive: bool,
    card: SupplierSnapshot | None = None,
    read_by_ocr: bool = False,
) -> Quote:
    """A year of the household's gas on ``contract``'s current card, or on
    ``card`` when the caller holds it already (the household's own, which
    ``read_by_ocr`` says the card archive read off its image).
    ``use_archive`` lets a card published as page images be priced on the
    card archive's reading of it, as the entry itself is."""
    label = extractor.contract_label(contract) or contract
    source = "ocr" if read_by_ocr else "live"
    if card is None:
        try:
            card, source = await current_card(
                session, extractor, contract, region, month, use_archive=use_archive
            )
        except ExtractorError as err:
            return Quote(extractor.id, contract, label, None, None, None, False, False, str(err))
    table = await indices.table(session, extractor)
    try:
        # A year of the household's volume and of fixed costs, on the card as
        # this month bills it: the law's levies and the regulated figures a
        # card leaves out included.
        bill = bill_month(
            month=month,
            card=card,
            energy=card.energy,
            table=table,
            dso=household.dso,
            annual_kwh=household.annual_kwh,
            caliber=household.caliber,
            kwh=household.annual_kwh,
            days=365,
            days_in_year=365,
        )
    except PricingError as err:
        return Quote(extractor.id, contract, label, None, None, None, False, False, str(err))
    return Quote(
        supplier=extractor.id,
        contract=contract,
        label=label,
        annual_cost=bill.total,
        all_in=bill.breakdown.all_in,
        fixed=bill.fixed_cost,
        indexed=isinstance(card.energy, IndexedRates),
        provisional=bill.provisional,
        read_by_ocr=source == "ocr",
    )


def candidates(region: str) -> list[tuple[SupplierExtractor, str]]:
    """Every (supplier, contract) sold in ``region``, cheapest to fetch first."""
    pairs = [
        (extractor, contract.id)
        for extractor in all_extractors()
        if extractor.deprecated_until is None and extractor.id != SUPPLIER_CUSTOM
        for contract in extractor.contracts
        if region in contract.regions and not contract.professional
    ]
    return sorted(pairs, key=lambda pair: pair[0].sweep_cost_s)


async def rank(
    session: aiohttp.ClientSession,
    region: str,
    household: Household,
    today_month: str,
    *,
    use_archive: bool,
    budget_s: float | None = None,
    progress: Callable[[int, int], None] | None = None,
    own: OwnContract | None = None,
) -> tuple[list[Quote], int]:
    """Every contract in ``region`` quoted and sorted cheapest first.

    ``budget_s`` bounds how long the ranking spends fetching: past it the
    remaining contracts are not started, and their count is returned beside
    the ranking so the page can say so. Failed quotes sort last. ``own`` is
    the household's contract, quoted on its own card in place of the card
    of the month a new customer signs on, so the household sees where what
    it pays ranks; a custom entry's typed card is no supplier's and is only
    there this way.
    """
    pairs = [
        pair
        for pair in candidates(region)
        if own is None or (pair[0].id, pair[1]) != (own.extractor.id, own.contract)
    ]
    indices = IndexCache(own)
    started = time.monotonic()
    semaphore = asyncio.Semaphore(_CONCURRENCY)
    done = 0
    skipped = 0

    async def _one(extractor: SupplierExtractor, contract: str) -> Quote | None:
        nonlocal done, skipped
        async with semaphore:
            if budget_s is not None and time.monotonic() - started > budget_s:
                skipped += 1
                return None
            quote = await quote_contract(
                session,
                extractor,
                contract,
                region,
                household,
                today_month,
                indices,
                use_archive=use_archive,
            )
        done += 1
        if progress is not None:
            progress(done, len(pairs))
        return quote

    async def _supplier(extractor: SupplierExtractor, contracts: list[str]) -> list[Quote | None]:
        # One supplier's contracts in turn, so the listing page or the card
        # they share (EBEM prints both its products on one) is read once and
        # served to the others from the sweep's memo.
        return [await _one(extractor, contract) for contract in contracts]

    by_supplier: dict[str, tuple[SupplierExtractor, list[str]]] = {}
    for extractor, contract in pairs:
        by_supplier.setdefault(extractor.id, (extractor, []))[1].append(contract)
    with memoise_text_fetches({}):
        results = await asyncio.gather(
            *(_supplier(extractor, contracts) for extractor, contracts in by_supplier.values())
        )
    quotes = [quote for group in results for quote in group if quote is not None]
    if own is not None:
        quotes.append(
            await quote_contract(
                session,
                own.extractor,
                own.contract,
                region,
                household,
                today_month,
                indices,
                use_archive=False,
                card=own.card,
                read_by_ocr=own.read_by_ocr,
            )
        )
    quotes.sort(key=lambda q: (q.annual_cost is None, q.annual_cost or 0.0, q.label))
    return quotes, skipped
