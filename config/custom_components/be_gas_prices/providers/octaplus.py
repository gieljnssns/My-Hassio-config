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

"""OCTA+ gas tariff card extractor.

OCTA+ publishes one card per residential gas product and region at a stable
URL, overwritten in place every month:

    https://files.octaplus.be/tariffs/G_OCTA_<SLUG>_RE_<VL|WL>_FR.pdf

Residential gas is sold in Flanders and Wallonia only: the Brussels cards the
tariff page links are professional ones. Since October 2026 the slugs are
BASICONLINE, BOOSTFLEX, ECOBOOSTFLEX, SMARTVARIABLE, BOOSTFIX and
ECOBOOSTFIX. Flux, Eco Flux, Fixed and Eco Fixed were withdrawn that month.

Both regional cards print the same energy figures and both regions' DSO
tables; the Walloon one adds the connection fee column. Every figure is VAT
inclusive ("TVAC"), but no card states the rate, so the formulas are grossed
up by the statutory residential rate.

Every variable product indexes on "ZTP RLP M", the RLP-weighted mean
of the ZTP day-ahead quotes of the delivery month, known only once the month
is over. The card prints the formula in EUR/MWh excluding VAT and a price that
is not the formula at the last known value but a twelve-month estimate at the
forward "V-test" value OCTA+ publishes at octaplus.be/prixattendus. That
estimate is the only price the card prints, so it is the one the snapshot
carries. The realised monthly values are published at octaplus.be/prixgaz,
which is what :func:`fetch_index` reads.

The site's archive is two JSON endpoints: getTarifArchive names the cards a
month had for a region, and getTariffSheet hands one back as a base64 data URL.
The current template starts with the June 2026 cards. The ones checked from
September 2025 to May 2026 are an older template this module does not read,
so :func:`fetch_for_month` returns None for such months.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.parse import urlencode

import aiohttp
from homeassistant.util import dt as dt_util

from ..const import DSO_RESA, REGION_FLANDERS, REGION_WALLONIA, VAT_RATE_REDUCED
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
    read_dsos,
    require_region,
)
from ._parse import SIGN_CHARS, fold_accents, month_date, parse_sign, require_contract, to_float
from ._pdf import (
    MONTH_NAMES,
    extract_pdf_text_layout,
    fetch_pdf_text_layout,
    fetch_text,
    head_freshness_key,
    is_pdf_payload,
    parse_json,
    render_pdf,
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

_BASE_URL = "https://files.octaplus.be/tariffs"
_ARCHIVE_LISTING_URL = "https://srv.octaplus.be/websiterest/getTarifArchive"
_ARCHIVE_SHEET_URL = "https://srv.octaplus.be/websiterest/getTariffSheet"
# The short link the cards name; it redirects to the parameter PDF, whose file
# name is not something the cards promise.
_INDEX_URL = "https://www.octaplus.be/prixgaz"

_REGION_TO_CODE: dict[str, str] = {
    REGION_FLANDERS: "VL",
    REGION_WALLONIA: "WL",
}

# The index the variable cards name in their formula.
_INDEX = "ZTP RLP M"


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    kind: TariffKind
    slug: str  # as the live file name spells it


_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("octaplus_basiconline", "OCTA+ Basic Online", "indexed", "BASICONLINE"),
    _ContractDef("octaplus_boostflex", "OCTA+ Boost Flex", "indexed", "BOOSTFLEX"),
    _ContractDef("octaplus_ecoboostflex", "OCTA+ Eco Boost Flex", "indexed", "ECOBOOSTFLEX"),
    _ContractDef("octaplus_smartvariable", "OCTA+ Smart Variable", "indexed", "SMARTVARIABLE"),
    _ContractDef("octaplus_boostfix", "OCTA+ Boost Fix", "fixed", "BOOSTFIX"),
    _ContractDef("octaplus_ecoboostfix", "OCTA+ Eco Boost Fix", "fixed", "ECOBOOSTFIX"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _region_code(contract: _ContractDef, region: str) -> str:
    code = _REGION_TO_CODE.get(region)
    if code is None:
        raise ExtractorError(f"OCTA+ {contract.contract_id}: not sold in region {region!r}")
    return code


def _card_url(contract: _ContractDef, code: str) -> str:
    return f"{_BASE_URL}/G_OCTA_{contract.slug}_RE_{code}_FR.pdf"


async def probe(session: aiohttp.ClientSession, contract_id: str, region: str) -> str | None:
    """The card's Last-Modified, and the running month.

    OCTA+ overwrites the card in place, so the header moves exactly when the
    card does. The month is in the key because the card for the next month
    may go up on the last day of the one before, when the running month's
    card stands in for it, and must be read again once its month begins.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    code = _REGION_TO_CODE.get(region)
    if contract is None or code is None:
        return None
    key = await head_freshness_key(session, _card_url(contract, code))
    return None if key is None else f"{key} {dt_util.now().date():%Y-%m}"


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The configured region's card as it stands online.

    OCTA+ may put the next month's card up on the last day of the month
    before; an installation is then priced on the running month's card from
    the archive (``month_cards.current_card``).
    """
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "OCTA+")
    url = _card_url(contract, _region_code(contract, region))
    text = await fetch_pdf_text_layout(session, url)
    return parse_snapshot(contract_id, region, text, source_url=url)


def _archive_json(body: str, what: str) -> Any:
    """The ``Response`` member of an archive reply, or raise.

    A reply that is JSON of another shape must read as a failed fetch rather
    than escape as a TypeError further down.
    """
    payload = parse_json(body, f"OCTA+ archive {what}")
    if not isinstance(payload, dict) or "Response" not in payload:
        raise ExtractorError(f"OCTA+ archive {what}: no Response in the reply")
    return payload["Response"]


def _collapse(name: str) -> str:
    """``name`` with every run of one character reduced to one."""
    return re.sub(r"(.)\1+", r"\1", name)


def _pick_archive_name(
    names: list[str], contract: _ContractDef, code: str, month: date
) -> str | None:
    """The archive's file name for ``contract`` in one month, or None.

    The listing spells the name "2026-10 G OCTA+BOOSTFIX RE WL FR.pdf". The
    March 2026 one named its fixed cards FIXEDD and ECOFIXEDD instead, the
    Fixed one a revision valid from 16 March, so a name that differs only by a
    doubled letter is taken when it is the only one: no two products fold onto
    each other that way, and a month listing two such names is left unread
    rather than guessed.
    """
    wanted = f"{month:%Y-%m} G OCTA+{contract.slug} RE {code} FR.pdf"
    if wanted in names:
        return wanted
    near = [name for name in names if _collapse(name) == _collapse(wanted)]
    return near[0] if len(near) == 1 else None


def _sheet_url(name: str) -> str:
    return f"{_ARCHIVE_SHEET_URL}?{urlencode({'Canal': 'website', 'RequestedPDF': name})}"


async def _archive_name(
    session: aiohttp.ClientSession, contract: _ContractDef, code: str, month: date
) -> str | None:
    query = {
        "Lang": "FR",
        "Region": code,
        "AnneeMois": f"{month:%Y%m}",
        "Nrj": "G",
        "Canal": "website",
        "TypeContrat": "RE",
    }
    rows = _archive_json(
        await fetch_text(session, f"{_ARCHIVE_LISTING_URL}?{urlencode(query)}"), "listing"
    )
    if not isinstance(rows, list):
        raise ExtractorError("OCTA+ archive listing: Response is not a list")
    names = [
        row["NomPdf"]
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("NomPdf"), str)
    ]
    return _pick_archive_name(names, contract, code, month)


def _archive_pdf(body: str, name: str) -> bytes:
    """The card inside a getTariffSheet reply, as PDF bytes.

    A name the archive does not hold is answered 200 with ``"Ok": "False"``,
    which is a card that is not there rather than a failed fetch.
    """
    reply = _archive_json(body, "sheet")
    sheet = reply.get("TariffSheet") if isinstance(reply, dict) else None
    if not isinstance(sheet, str) or "base64," not in sheet:
        raise ExtractorError(f"OCTA+ archive sheet: no card in the reply for {name!r}")
    try:
        payload = base64.b64decode(sheet.split("base64,", 1)[1], validate=True)
    except ValueError as err:
        # binascii.Error, or plain ValueError for text that is not ASCII.
        raise ExtractorError(f"OCTA+ archive sheet: bad base64 for {name!r}") from err
    if not is_pdf_payload(payload):
        raise ExtractorError(f"OCTA+ archive sheet: {name!r} is not a PDF")
    return payload


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card OCTA+ published for a past month, or None.

    The card arrives inside JSON rather than through a reader, so its bytes
    go through the readers' render hook, where the card archiver keeps them.
    A transient failure raises so the month cache retries it; any other
    failure, a card from the older template included, is a month with no
    card, and a card naming another month than the one asked for is refused.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    code = _REGION_TO_CODE.get(region)
    if contract is None or code is None:
        return None
    return await month_card(_read_month(session, contract, code, region, year_month), year_month)


async def _read_month(
    session: aiohttp.ClientSession,
    contract: _ContractDef,
    code: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    name = await _archive_name(session, contract, code, year_month)
    if name is None:
        return None
    url = _sheet_url(name)
    payload = _archive_pdf(await fetch_text(session, url, timeout=60), name)
    text = await render_pdf("layout", url, payload, extract_pdf_text_layout)
    return parse_snapshot(contract.contract_id, region, text, source_url=url)


def parse_snapshot(
    contract_id: str, region: str, text: str, *, source_url: str | None = None
) -> SupplierSnapshot:
    """Parse one regional card's text as pdfplumber lays it out."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "OCTA+")
    code = _region_code(contract, region)
    _check_product(text, contract)
    card_month = _card_month(text)
    return SupplierSnapshot(
        supplier="octaplus",
        contract=contract_id,
        energy=_energy(text, contract),
        dsos=_dsos(text, region),
        taxes=_taxes(text, region),
        source_url=source_url or _card_url(contract, code),
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


def _check_product(text: str, contract: _ContractDef) -> None:
    """The card opens with its product, "GAZ SMARTVARIABLE", "GAZ BOOST FLEX"
    or "GAZ ECO BOOST FIX": its slug, spaced out. The archive match is loose
    enough to warrant making sure it found the product asked for."""
    # Words split by single spaces, so a malformed line cannot send the
    # match into backtracking.
    match = re.search(r"^GAZ (\S+(?: \S+)*)[ \t]*$", text, re.MULTILINE)
    if match is None:
        raise ExtractorError(f"OCTA+ {contract.contract_id}: product heading not found")
    if "".join(match.group(1).split()) != contract.slug:
        raise ExtractorError(f"OCTA+ {contract.contract_id}: the card is for {match.group(1)}")


_CARD_MONTH_RE = re.compile(r"FICHE TARIFAIRE\s+(\S+)\s+(\d{4})")


def _card_month(text: str) -> date:
    """The month of the banner, "FICHE TARIFAIRE SEPTEMBRE 2026". The fixed
    cards print no validity sentence, so the banner is what every card has."""
    match = _CARD_MONTH_RE.search(text)
    month = MONTH_NAMES.get(fold_accents(match.group(1))) if match else None
    if match is None or month is None:
        raise ExtractorError("OCTA+: card month not found")
    return month_date(match.group(2), month, "OCTA+")


_FEE_RE = re.compile(r"Redevance fixe \(€/an\)\s+(\d+,\d+)")
_PRICE_RE = re.compile(r"Coût du gaz \(c€/kWh\)\s+(\d+,\d+)")
# "ZTP RLP M * 1,010 + 2,160." on Flux and Eco Flux, "ZTP RLP M* 1,15+ 10
# EUR/MWh." on Smart Variable, both in EUR/MWh. Only the first says HTVA, but
# Smart Variable's printed estimate too is its formula grossed up by 6%.
# A figure printed with a decimal point is read whole, not cut at the point.
_FORMULA_RE = re.compile(
    rf"{_INDEX}\s*\*\s*(\d+(?:[.,]\d+)?)\s*([{SIGN_CHARS}])\s*(\d+(?:[.,]\d+)?)"
)


def _energy(text: str, contract: _ContractDef) -> FixedRates | IndexedRates:
    fee = _FEE_RE.search(text)
    price = _PRICE_RE.search(text)
    if fee is None or price is None:
        raise ExtractorError("OCTA+: energy block not found")
    if contract.kind == "fixed":
        return FixedRates(
            price=to_float(price.group(1)) / 100.0,
            yearly_fixed_fee=to_float(fee.group(1)),
        )
    formula = _FORMULA_RE.search(text)
    if formula is None:
        raise ExtractorError(f"OCTA+ {contract.contract_id}: {_INDEX} formula not found")
    vat = 1.0 + VAT_RATE_REDUCED
    return IndexedRates(
        factor=to_float(formula.group(1)) / 1000.0 * vat,
        base=parse_sign(formula.group(2)) * to_float(formula.group(3)) / 1000.0 * vat,
        index=_INDEX,
        price=to_float(price.group(1)) / 100.0,
        yearly_fixed_fee=to_float(fee.group(1)),
        formula=formula.group(0),
    )


# Distribution per tier as fixed then proportional, the data management fee
# ("-" in Wallonia), then transport. Each card prints both regions' tables.
_COLUMNS = (T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, METERING, TRANSPORT)
_LABELS: dict[str, dict[str, str]] = {
    REGION_FLANDERS: FLUVIUS_LABELS,
    REGION_WALLONIA: {**ORES_LABELS, "RESA": DSO_RESA},
}
_BLOCKS: dict[str, tuple[str, str]] = {
    REGION_FLANDERS: ("Région flamande", "Région wallonne"),
    REGION_WALLONIA: ("Région wallonne", "LES SURCHARGES"),
}


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    after, before = _BLOCKS[region]
    dsos = read_dsos(text, _LABELS[region], _COLUMNS, supplier="OCTA+", after=after, before=before)
    require_region(dsos, region, "OCTA+")
    return dsos


# The two excise rows carry the special excise, then the energy contribution,
# then on the Walloon card only the connection fee, all in c EUR/kWh.
_LOW_ROW_RE = re.compile(
    r"^Consommation entre 0 & 12\.000 kWh[ \t]+(\d+,\d+)[ \t]+(\d+,\d+)(?:[ \t]+(\d+,\d+))?[ \t]*$",
    re.MULTILINE,
)
_HIGH_ROW_RE = re.compile(
    r"^Consommation > 12\.000 kWh[ \t]+(\d+,\d+)[ \t]+(\d+,\d+)[ \t]*$", re.MULTILINE
)


def _taxes(text: str, region: str) -> TaxOverlay:
    """The levies as printed. The August and September 2026 cards still print
    the energy contribution 0,1058 on the first slice (and 0,00 on the second)
    although the law zeroed it in August; the delivery month's law corrects
    it."""
    low = _LOW_ROW_RE.search(text)
    high = _HIGH_ROW_RE.search(text)
    if low is None or high is None:
        raise ExtractorError("OCTA+: excise rows not found")
    connection_fee = 0.0
    if region == REGION_WALLONIA:
        if low.group(3) is None or "Redevance raccordement Wallonie" not in text:
            raise ExtractorError("OCTA+: Walloon connection fee not found")
        connection_fee = to_float(low.group(3)) / 100.0
    return TaxOverlay(
        excise_bands=excise_bands(to_float(low.group(1)) / 100.0, to_float(high.group(1)) / 100.0),
        energy_contribution=to_float(low.group(2)) / 100.0,
        connection_fee=connection_fee,
    )


# The table's heading, which says which column is which; the table is read
# only while its heading reads exactly so.
_INDEX_HEADER = "Periode TTF101 Mois TTF103 Trimestre TTF RLP Mois ZTP RLP Mois ZTP RLP Trimestre"
_INDEX_ROW_RE = re.compile(
    r"^(\d{2})/(\d{4})((?:[ \t]+(?:\d+(?:,\d+)?|-)){5})[ \t]*$", re.MULTILINE
)
_ZTP_RLP_COLUMN = 3


def parse_index(text: str) -> IndexTable:
    """The monthly ZTP RLP values of OCTA+'s parameter PDF, in EUR/MWh.

    One row per delivery month ("08/2026 53,734 45,112 61,729 61,899 -"); a
    month not over yet prints "-". The other columns (TTF101, TTF103, TTF RLP
    and the quarterly ZTP RLP) are no gas card's index and are not read.
    """
    if _INDEX_HEADER not in " ".join(text.split()):
        raise ExtractorError("OCTA+: index table heading not found")
    values: dict[str, float] = {}
    for month, year, cells in _INDEX_ROW_RE.findall(text):
        cell = cells.split()[_ZTP_RLP_COLUMN]
        if cell != "-":
            values[f"{year}-{month}"] = to_float(cell)
    if not values:
        raise ExtractorError(f"OCTA+: no {_INDEX} values in the index table")
    return {_INDEX: values}


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """OCTA+'s published ZTP RLP M values."""
    return parse_index(await fetch_pdf_text_layout(session, _INDEX_URL))


EXTRACTOR = SupplierExtractor(
    id="octaplus",
    label="OCTA+",
    contracts=tuple(
        Contract(
            id=c.contract_id,
            label=c.label,
            kind=c.kind,
            regions=frozenset(_REGION_TO_CODE),
        )
        for c in _CONTRACTS
    ),
    fetch=fetch,
    probe=probe,
    fetch_for_month=fetch_for_month,
    withdrawn={
        "octaplus_flux": "OCTA+ Flux",
        "octaplus_ecoflux": "OCTA+ Eco Flux",
        "octaplus_fixed": "OCTA+ Fixed",
        "octaplus_ecofixed": "OCTA+ Eco Fixed",
    },
    fetch_index=fetch_index,
    sweep_cost_s=4.5,
)
