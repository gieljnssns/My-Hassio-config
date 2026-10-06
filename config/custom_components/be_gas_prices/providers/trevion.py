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

"""Trevion gas tariff card extractor.

Trevion sells one residential gas product, Gas Flex, in Flanders only: the
card covers households "aangesloten in Vlaanderen" using under 150 MWh. Its
listing page links every card it still serves, one per month:

    https://trevion.be/tariefkaarten/Tariefkaart-Gas-Flex-Particulier-<YYYYMM>[-N].pdf

``-N`` is a reissue. The unsuffixed name of a reissued month keeps answering
(both ``-202608.pdf`` and ``-202608-1.pdf`` do), so the listing's href is
what counts and a URL is never built. The listing is also the archive: it
reaches back to March 2026. It sends neither ETag nor Last-Modified, so
there is no cheap probe.

The cards are Word exports. pdfplumber reads their header and energy block
one glyph per line, because stray whitespace glyphs sit at almost every
height; pypdf reads every card from March to September 2026 cleanly, so it
is the reader here.

The energy price is "(0,102 x TTF_RLP + 0,50) x 1,06" in c EUR/kWh against
TTF_RLP in EUR/MWh, with the VAT already inside, and the card prints it at
"the last known value". That sentence is only half reliable. Its value is
always the TTF RLP of the month before the card, as OCTA+ and HOA publish
it (the September card's 61,72 is OCTA+'s 61,729 for August), but the month
it names is not: the March 2026 card says "maart 2026 (33,30 €/MWh)" for
February's 33,296, and the April card names March again with March's
51,264. The value can also carry a dot ("53.07" in August).

Trevion publishes no index table of its own (its market page is
electricity only), so a realised value appears nowhere but on the next
month's card. :func:`fetch_index` reads it there, and only where the named
month is the month before the card's own. On every card but the March one
both readings agree; that card is left out rather than filed under either
month.
"""

from __future__ import annotations

import re
from datetime import date
from urllib.parse import urljoin

import aiohttp

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
    read_dsos,
    require_region,
)
from ._parse import fold_accents, month_date, require_contract, to_float
from ._pdf import (
    MONTH_NAMES,
    fetch_pdf_text,
    fetch_text,
    is_transient_fetch_error,
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

_LISTING_URL = "https://trevion.be/tariefkaarten/"
_INDEX = "TTF_RLP"

_CONTRACT = Contract(
    id="trevion_gas_flex",
    label="Trevion Gas Flex",
    kind="indexed",
    regions=frozenset({REGION_FLANDERS}),
)
_CONTRACTS_BY_ID = {_CONTRACT.id: _CONTRACT}

# The residential card only: the listing carries a Professioneel twin
# printed excluding VAT.
_CARD_RE = re.compile(
    r'href="((?:https://trevion\.be)?/tariefkaarten/'
    r'Tariefkaart-Gas-Flex-Particulier-(\d{4})(\d{2})(?:-(\d+))?\.pdf)"'
)


def _listed_cards(html: str) -> dict[date, str]:
    """The card URL the listing gives for each month, the latest reissue
    winning where a month is listed twice."""
    best: dict[date, tuple[int, str]] = {}
    for href, year, month, reissue in _CARD_RE.findall(html):
        # Six digits that are not a month are a file this does not know,
        # not a reason to lose every other card on the page.
        try:
            key = date(int(year), int(month), 1)
        except ValueError:
            continue
        rank = int(reissue or 0)
        if key not in best or rank > best[key][0]:
            best[key] = (rank, urljoin(_LISTING_URL, href))
    return {key: url for key, (_rank, url) in best.items()}


def _check(contract_id: str, region: str) -> None:
    require_contract(_CONTRACTS_BY_ID, contract_id, "Trevion")
    if region != REGION_FLANDERS:
        raise ExtractorError(f"Trevion {contract_id}: not sold in region {region!r}")


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The newest card on the listing."""
    _check(contract_id, region)
    cards = _listed_cards(await fetch_text(session, _LISTING_URL))
    if not cards:
        raise ExtractorError("Trevion: no Gas Flex card on the listing")
    return await _read(session, contract_id, region, cards[max(cards)])


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(contract_id, region, await fetch_pdf_text(session, url), source_url=url)


async def _read_month(
    session: aiohttp.ClientSession, contract_id: str, region: str, year_month: date
) -> SupplierSnapshot | None:
    cards = _listed_cards(await fetch_text(session, _LISTING_URL))
    url = cards.get(date(year_month.year, year_month.month, 1))
    if url is None:
        return None
    return await _read(session, contract_id, region, url)


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card the listing gives for ``year_month``, or None where it gives
    none. A card naming another month is refused; a transient failure raises
    so the month cache retries it."""
    if contract_id not in _CONTRACTS_BY_ID or region != REGION_FLANDERS:
        return None
    return await month_card(_read_month(session, contract_id, region, year_month), year_month)


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """TTF_RLP by month, off the cards that name it (see the module
    docstring for which ones count)."""
    cards = _listed_cards(await fetch_text(session, _LISTING_URL))
    values: dict[str, float] = {}
    for url in cards.values():
        try:
            text = await fetch_pdf_text(session, url)
        except ExtractorError as err:
            # One dead link on the listing is no reason to lose every other
            # month; a supplier that is down is.
            if is_transient_fetch_error(str(err)):
                raise
            continue
        found = published_index(text)
        if found is not None:
            values[f"{found[0]:%Y-%m}"] = found[1]
    if not values:
        raise ExtractorError("Trevion: no card names a TTF_RLP value")
    return {_INDEX: values}


# "Trevion Gas Flex Particulier", bracketed from October 2026: "Trevion Gas
# Flex (Particulier)".
_PRODUCT_RE = re.compile(r"Trevion Gas Flex \(?Particulier\b")


def parse_snapshot(
    contract_id: str,
    region: str,
    text: str,
    *,
    source_url: str = _LISTING_URL,
) -> SupplierSnapshot:
    """Parse one card's text as pypdf extracts it."""
    _check(contract_id, region)
    # The Professioneel card shares the layout and prints excluding VAT.
    if not _PRODUCT_RE.search(text):
        raise ExtractorError("Trevion: not the Gas Flex Particulier card")
    card_month = _card_month(text)
    if card_month is None:
        raise ExtractorError("Trevion: card month not found")
    return SupplierSnapshot(
        supplier="trevion",
        contract=contract_id,
        energy=_energy(text),
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


def _month(name: str, year: str) -> date | None:
    month = MONTH_NAMES.get(fold_accents(name))
    return None if month is None else month_date(year, month, "Trevion")


# "Geldig voor particuliere contracten afgesloten in september 2026".
_CARD_MONTH_RE = re.compile(r"contracten afgesloten in\s+([A-Za-z]+)\s+(\d{4})")


def _card_month(text: str) -> date | None:
    match = _CARD_MONTH_RE.search(text)
    return None if match is None else _month(match.group(1), match.group(2))


# "De laatst gekende waarde is deze van augustus 2026 (61,72 €/MWh)".
_KNOWN_VALUE_RE = re.compile(
    r"laatst gekende waarde is deze van\s+([A-Za-z]+)\s+(\d{4})\s*\(\s*(\d+[.,]\d+)\s*€/MWh\)"
)


def published_index(text: str) -> tuple[date, float] | None:
    """The TTF_RLP month and value in EUR/MWh a card names, or None where
    the card names none or names a month other than the one before its own.
    """
    match = _KNOWN_VALUE_RE.search(text)
    try:
        card_month = _card_month(text)
        named = None if match is None else _month(match.group(1), match.group(2))
    except ExtractorError:
        # A month that is no month names no value.
        return None
    if match is None or card_month is None or named is None:
        return None
    if named.year * 12 + named.month + 1 != card_month.year * 12 + card_month.month:
        return None
    return named, to_float(match.group(3))


_VAT_RE = re.compile(r"Incl\.\s*(\d+)\s*%\s*BTW")
# The energy block's two headings and, on the next line, their figures:
# "Energiekost Variabel (c€/kWh) Abonnementskost (€/jaar)" then "7,20 39".
_PRICE_RE = re.compile(
    r"Energiekost Variabel \(c€/kWh\) Abonnementskost \(€/jaar\)\s*\n"
    r"\s*(\d+,\d+)\s+(\d+(?:,\d+)?)\s*\n"
)
_FORMULA_RE = re.compile(
    r"\(\s*(\d+,\d+)\s*x\s*TTF_RLP\s*\+\s*(\d+,\d+)\s*\)\s*x\s*(\d+,\d+)",
)


def _energy(text: str) -> IndexedRates:
    price = _PRICE_RE.search(text)
    formula = _FORMULA_RE.search(text)
    if price is None or formula is None:
        raise ExtractorError("Trevion: energy price or formula not found")
    # c EUR/kWh against TTF_RLP in EUR/MWh, grossed by the multiplier the
    # formula prints rather than by the card's stated rate.
    vat = to_float(formula.group(3))
    return IndexedRates(
        factor=to_float(formula.group(1)) * vat / 100.0,
        base=to_float(formula.group(2)) * vat / 100.0,
        index=_INDEX,
        price=to_float(price.group(1)) / 100.0,
        yearly_fixed_fee=to_float(price.group(2)),
        formula=formula.group(0),
    )


# "Fluvius Antwerpen 15,68 2,26 83,22 0,91 0,165 18,92": per tier the fixed
# term then the proportional one, then transport and databeheer. The card
# spells "Fuvius Halle-Vilvoorde", which the label matching absorbs.
_COLUMNS = (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, TRANSPORT, METERING)


def _dsos(text: str) -> dict[str, DsoOverlay]:
    dsos = read_dsos(
        text,
        FLUVIUS_LABELS,
        _COLUMNS,
        supplier="Trevion",
        after="Netbeheerder",
        before="Bijzondere accijns",
    )
    require_region(dsos, REGION_FLANDERS, "Trevion")
    return dsos


# The two band labels print above their two rates.
_EXCISE_RE = re.compile(
    r"Bijzondere accijns op Energie \(c€/kWh\)\s*\n\s*≤ 12 MWh\s*\n\s*≥ 12 MWh\s*\n"
    r"\s*(\d+,\d+)\s*\n\s*(\d+,\d+)"
)


def _excise(text: str) -> tuple[tuple[float | None, float], ...]:
    match = _EXCISE_RE.search(text)
    if match is None:
        raise ExtractorError("Trevion: federal excise rows not found")
    return excise_bands(to_float(match.group(1)) / 100.0, to_float(match.group(2)) / 100.0)


# Trevion prints some figures with a decimal point ("53.07", "0.98"): one is
# read whole, not cut at the point.
_CONTRIBUTION_RE = re.compile(r"Bijdrage op de Energie \(c€/kWh\)\s+(\d+(?:[.,]\d+)?)")


def _energy_contribution(text: str) -> float:
    """Printed 0 since August 2026, when the law zeroed it, and 0,10577
    before. A card that drops the row follows the law rather than a layout
    change, so a missing row reads as zero."""
    match = _CONTRIBUTION_RE.search(text)
    return 0.0 if match is None else to_float(match.group(1)) / 100.0


EXTRACTOR = SupplierExtractor(
    id="trevion",
    label="Trevion",
    contracts=(_CONTRACT,),
    fetch=fetch,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=3.0,
)
