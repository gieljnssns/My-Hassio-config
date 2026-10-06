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

"""Luminus gas tariff card extractor.

Luminus publishes the current month's card per (product, region) through the
endpoint its electricity cards come from, with ``energyType=gas``:

    https://www.luminus.be/api-next/get-pricelist/
        ?documentSlug=<slug>&energyType=gas&language=fr
        &tabValue=<Wallonia|Flanders>

There is no Brussels card: ``tabValue=Brussels`` answers 404. The endpoint
never refuses a slug it has no gas card for: an electricity-only slug is
served another product's gas card (``smartflex`` gets ComfyFlex, ``dynamic``
MaxxFlex), and the file name does not tell Comfy+ from Comfy either, so the
product named in the card's title is checked against the contract. The body
starts with a UTF-8 BOM, which the shared PDF fetcher strips.

The card is served from a storage blob that is rewritten without the card
changing: on 29 September 2026 all sixteen carried a Last-Modified of 01:00
that night while the PDFs inside were generated on 17 September. The blob's
Content-MD5 is the MD5 of the bytes, so unlike Last-Modified and ETag it only
moves when the card does, which makes it the probe.

Since January 2026 each region has its own card, and the energy price differs
between them. Until December 2025 one card served both: a DSO table with the
Flemish data management fee as a last column and a tax block with one column
of figures per region ("Taxes et redevances : FL WAL"). Both layouts are read.
Every figure is 6% VAT inclusive; the formulas are printed excluding VAT and
grossed up here by the card's own rate.

The indexed products all settle on a mean of the ICIS TTF day-ahead and
weekend assessments over the delivery period, known once it is over, so each
card prints its price at the last known value and none is settled:

  - ComfyFlex and ComfyFlex+ on TTF DAHW, the mean over the delivery quarter
    ("0,1004 x TTF DAHW + 0,0000 x TTF 1-0-3 + 2,0204", the forward term
    weighted zero).
  - MaxxFlex on TTF DAH M, the mean over the delivery month.
  - BasicFlex on TTF DAH RLP M, the same month weighted by the RLP load
    profiles Synergrid publishes.

Luminus publishes every value in one PDF, titled by month ("Septembre 2026"),
linked from its indexation page. It is a CMS asset whose id changes with each
upload and whose old versions are deleted, so the page is read for the link
first. The PDF sets its tables side by side and leaves the cells of periods
not yet known empty, which its text layer cannot tell apart, so the figures
are placed under their year by position.

The archive is two endpoints: one lists a signing month's products with
their ids, the other serves a product's card for that month and region.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

import aiohttp

from ..const import DSO_RESA, REGION_FLANDERS, REGION_WALLONIA
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
    TRANSPORT,
    excise_bands,
    read_dsos,
    require_region,
)
from ._parse import (
    SIGN_CHARS,
    cell_value,
    fold_accents,
    month_date,
    parse_sign,
    require_contract,
    to_float,
)
from ._pdf import (
    MONTH_NAMES,
    fetch_pdf_rendered,
    fetch_pdf_text,
    fetch_text,
    head_freshness_key,
    parse_json,
    pdfplumber_text,
    printed_vat_rate,
    word_centre,
    word_rows,
)
from ._rates import Contract, FixedRates, IndexedRates, IndexPeriod, TariffKind
from ._validity import end_of_month, future_month, month_card
from .base import (
    DsoOverlay,
    ExtractorError,
    IndexTable,
    SupplierExtractor,
    SupplierSnapshot,
    TaxOverlay,
)

_API_URL = "https://www.luminus.be/api-next/get-pricelist/"
_ARCHIVE_PRODUCTS_URL = "https://www.luminus.be/api/pricelist/products"
_ARCHIVE_PDF_URL = "https://www.luminus.be/api/pricelist/pdf"
_INDEX_PAGE_URL = "https://www.luminus.be/fr/particuliers/energie/parametres-d-indexation/"
# With the trailing slash: the bare path answers a 308 to this one.
_DOWNLOAD_URL = "https://www.luminus.be/api-next/download/"

_REGION_TO_TAB: dict[str, str] = {
    REGION_FLANDERS: "Flanders",
    REGION_WALLONIA: "Wallonia",
}
# How the tax block heading names each region.
_REGION_TO_TAG: dict[str, str] = {
    REGION_FLANDERS: "FL",
    REGION_WALLONIA: "WAL",
}


@dataclass(frozen=True)
class _ContractDef:
    contract_id: str
    label: str
    kind: TariffKind
    slug: str  # the documentSlug query parameter


# Every residential gas product in the archive's product list. The social
# tariff is set by the CREG and assigned rather than chosen, so it is left out.
_CONTRACTS: tuple[_ContractDef, ...] = (
    _ContractDef("luminus_comfy", "Luminus Comfy", "fixed", "comfy"),
    _ContractDef("luminus_comfy_plus", "Luminus Comfy+", "fixed", "comfy-plus"),
    _ContractDef("luminus_comfyflex", "Luminus ComfyFlex", "indexed", "comfyflex"),
    _ContractDef("luminus_comfyflex_plus", "Luminus ComfyFlex+", "indexed", "comfyflex-plus"),
    _ContractDef("luminus_maxxfix", "Luminus MaxxFix", "fixed", "maxxfix"),
    _ContractDef("luminus_maxxflex", "Luminus MaxxFlex", "indexed", "maxxflex"),
    _ContractDef("luminus_basicfix", "Luminus BasicFix Online", "fixed", "basicfix"),
    _ContractDef("luminus_basicflex", "Luminus BasicFlex Online", "indexed", "basicflex"),
)
_CONTRACTS_BY_ID = {c.contract_id: c for c in _CONTRACTS}


def _document_url(contract: _ContractDef, region: str) -> str:
    tab = _REGION_TO_TAB.get(region)
    if tab is None:
        raise ExtractorError(f"Luminus {contract.contract_id}: not sold in region {region!r}")
    return f"{_API_URL}?documentSlug={contract.slug}&energyType=gas&language=fr&tabValue={tab}"


def _product_key(name: str) -> str:
    """A product name without the brand, the energy and the Online marker.

    The card titles, the archive list and the labels name one product three
    ways: "Luminus BasicFix Online Gaz" in the archive, "BasicFix Online Gaz"
    on the 2026 cards and "BasicFix Gaz" on the earlier ones.
    """
    return " ".join(w for w in name.split() if w not in ("Luminus", "Gaz", "Online"))


async def fetch(session: aiohttp.ClientSession, contract_id: str, region: str) -> SupplierSnapshot:
    """The configured region's current card for ``contract_id``."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Luminus")
    return await _read(session, contract_id, region, _document_url(contract, region))


async def _read(
    session: aiohttp.ClientSession, contract_id: str, region: str, url: str
) -> SupplierSnapshot:
    return parse_snapshot(contract_id, region, await fetch_pdf_text(session, url), url)


async def probe(session: aiohttp.ClientSession, contract_id: str, region: str) -> str | None:
    """The card's Content-MD5, which only changes with its bytes."""
    contract = _CONTRACTS_BY_ID.get(contract_id)
    if contract is None or region not in _REGION_TO_TAB:
        return None
    return await head_freshness_key(
        session, _document_url(contract, region), prefer=("Content-MD5",)
    )


async def _archive_product_id(
    session: aiohttp.ClientSession, contract: _ContractDef, tab: str, month: str
) -> str | None:
    """The archive's id for ``contract`` in the product list of ``month``, or
    None when that month lists no such product."""
    url = (
        f"{_ARCHIVE_PRODUCTS_URL}?language=FR&customerSegment=Residential"
        f"&energyType=Gas&region={tab}&signing={month}"
    )
    rows = parse_json(await fetch_text(session, url, timeout=15), "Luminus: archive product list")
    if not isinstance(rows, list):
        raise ExtractorError("Luminus: archive product list is not a list")
    wanted = _product_key(contract.label)
    for row in rows:
        if isinstance(row, dict) and _product_key(str(row.get("Product", ""))) == wanted:
            product_id = row.get("ProductId")
            if isinstance(product_id, str) and product_id:
                return product_id
    return None


async def fetch_for_month(
    session: aiohttp.ClientSession,
    contract_id: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    """The card Luminus published for a past month, or None.

    A month ahead of today in Home Assistant's zone is refused rather than
    asked for: the product list answers for it and the PDF endpoint then says
    "Pdf not available". The archive's cards are the "Direct Mail" edition of
    the month: the same figures as the online card, without the new-customer
    campaign. A transient failure raises so the month cache retries it; any
    other failure is a month with no card, and a card naming another month
    than the one asked for is refused too.
    """
    contract = _CONTRACTS_BY_ID.get(contract_id)
    tab = _REGION_TO_TAB.get(region)
    if contract is None or tab is None:
        return None
    if future_month(year_month):
        return None
    return await month_card(_read_month(session, contract, tab, region, year_month), year_month)


async def _read_month(
    session: aiohttp.ClientSession,
    contract: _ContractDef,
    tab: str,
    region: str,
    year_month: date,
) -> SupplierSnapshot | None:
    month = f"{year_month:%Y-%m}"
    product_id = await _archive_product_id(session, contract, tab, month)
    if product_id is None:
        return None
    url = (
        f"{_ARCHIVE_PDF_URL}?language=FR&productId={product_id}"
        f"&date={month}&region={tab}&inline=true"
    )
    return await _read(session, contract.contract_id, region, url)


def parse_snapshot(
    contract_id: str, region: str, text: str, source_url: str = _API_URL
) -> SupplierSnapshot:
    """Parse one card's text as pypdf extracts it, for ``region``."""
    contract = require_contract(_CONTRACTS_BY_ID, contract_id, "Luminus")
    if region not in _REGION_TO_TAB:
        raise ExtractorError(f"Luminus {contract_id}: not sold in region {region!r}")
    product, card_month = _title(text)
    if _product_key(product) != _product_key(contract.label):
        raise ExtractorError(f"Luminus: card is for {product!r}, expected {contract.label!r}")
    vat_rate = printed_vat_rate(text, _VAT_RE)
    if vat_rate is None:
        raise ExtractorError("Luminus: VAT statement not found")
    # The tax block names the regions the card covers, so it is read first.
    taxes = _taxes(text, region, vat_rate)
    return SupplierSnapshot(
        supplier="luminus",
        contract=contract_id,
        energy=_energy(text, contract.kind, 1.0 + vat_rate),
        dsos=_dsos(text, region),
        taxes=taxes,
        source_url=source_url,
        publication_label=f"{card_month:%Y-%m}",
        valid_until=end_of_month(card_month.year, card_month.month),
    )


# The title of the card, "Luminus ComfyFlex Gaz(septembre 2026)", and from
# October 2026 without the brand, "ComfyFlex Gaz(octobre 2026)". The 2021
# cards of the quarterly products name a quarter ("juillet-septembre 2021"),
# which is no month and is refused.
_TITLE_RE = re.compile(r"^(?:Luminus )?(\S.*?) Gaz\s*\(\s*(\S+)\s+(\d{4})\s*\)", re.MULTILINE)


def _title(text: str) -> tuple[str, date]:
    match = _TITLE_RE.search(text)
    month = MONTH_NAMES.get(fold_accents(match.group(2))) if match else None
    if match is None or month is None:
        raise ExtractorError("Luminus: card title and month not found")
    return match.group(1), month_date(match.group(3), month, "Luminus")


_VAT_RE = re.compile(r"La TVA sur les prix indiqués[^%]{0,80}?(\d+(?:,\d+)?)\s*%")

# "Prix du jour" then "Énergie (c€/kWh) 7,00": the price at the last known
# index. The "Estimation annuelle" row below it is a forecast and not read.
_PRICE_RE = re.compile(r"^Énergie \(c€/kWh\)\s+(\d+,\d+)\s*$", re.MULTILINE)
_FEE_RE = re.compile(r"^Redevance fixe \(€/an\)\s+(\d+,\d+)\s*$", re.MULTILINE)

# The formula on the whitespace-collapsed text, c EUR/kWh excluding VAT for
# an index in EUR/MWh: "0,1001 x TTF DAH M + 1,5650", and on the quarterly
# products "0,1004 x TTF DAHW + 0,0000 x TTF 1-0-3 + 2,0204".
_S = f"[{SIGN_CHARS}]"
_FORMULA_RE = re.compile(
    rf"(\d+,\d+) x (TTF [A-Z]+(?: [A-Z]+)*) (?:({_S}) (\d+,\d+) x TTF 1-0-3 )?({_S}) (\d+,\d+)"
)
# The indices a formula can name, as the card spells them, with the title of
# their table in the index PDF and the period each one averages over.
_INDICES: dict[str, tuple[str, IndexPeriod]] = {
    "TTF DAHW": ("TTFDAHW", "quarter"),
    "TTF DAH M": ("TTFDAHM", "month"),
    "TTF DAH RLP M": ("TTFDAH RLP M", "month"),
}


def _energy(text: str, kind: TariffKind, vat: float) -> FixedRates | IndexedRates:
    price = _PRICE_RE.search(text)
    fee = _FEE_RE.search(text)
    if price is None or fee is None:
        raise ExtractorError("Luminus: energy price or fixed fee not found")
    if kind == "fixed":
        return FixedRates(
            price=to_float(price.group(1)) / 100.0, yearly_fixed_fee=to_float(fee.group(1))
        )
    flat = " ".join(text.split())
    start = flat.find("Index (HTVA)")
    formula = _FORMULA_RE.search(flat, start) if start >= 0 else None
    if formula is None:
        raise ExtractorError("Luminus: price formula not found")
    index = formula.group(2)
    if index not in _INDICES:
        raise ExtractorError(f"Luminus: formula on an unknown index {index!r}")
    # A forward term the price would also move with is something one index
    # cannot resolve. Every card so far weights it zero.
    if formula.group(4) is not None and to_float(formula.group(4)) != 0.0:
        raise ExtractorError(f"Luminus: formula carries a TTF 1-0-3 term: {formula.group(0)}")
    return IndexedRates(
        factor=to_float(formula.group(1)) / 100.0 * vat,
        base=parse_sign(formula.group(5)) * to_float(formula.group(6)) / 100.0 * vat,
        index=index,
        price=to_float(price.group(1)) / 100.0,
        yearly_fixed_fee=to_float(fee.group(1)),
        formula=formula.group(0),
        period=_INDICES[index][1],
    )


# "Variable (c€/kWh) Fixe (€/an)" for each of the three tiers, then transport,
# then on the cards until December 2025 "Tarif gestion des données / Activité
# de mesure et de comptage (€/an)", a figure on the Flemish rows and a dash on
# the Walloon ones. The 2026 cards print no data management fee.
_COLUMNS = (T1_PROP, T1_FIXED, T2_PROP, T2_FIXED, T3_PROP, T3_FIXED, TRANSPORT)
_METERING_HEADING = "Tarif gestion des"
_LABELS: dict[str, dict[str, str]] = {
    REGION_FLANDERS: FLUVIUS_LABELS,
    REGION_WALLONIA: {**ORES_LABELS, "TECTEO RESA": DSO_RESA},
}


def _dsos(text: str, region: str) -> dict[str, DsoOverlay]:
    columns = (*_COLUMNS, METERING) if _METERING_HEADING in text else _COLUMNS
    dsos = read_dsos(
        text,
        _LABELS[region],
        columns,
        supplier="Luminus",
        after="Coûts de distribution",
        before="Taxes et redevances :",
    )
    require_region(dsos, region, "Luminus")
    return dsos


# "3 Taxes et redevances : WAL", then the row labels, then their figures one
# a line in the same order: one run per region the heading names.
_TAX_HEADING_RE = re.compile(
    r"Taxes et redevances : ((?:FL|WAL)(?: (?:FL|WAL))*)\s*$", re.MULTILINE
)
_TAX_VALUE_RE = re.compile(r"-|\d+,\d+")
# What follows the block's footnotes. The February 2026 indexed cards left
# out the first heading and go straight on to the VAT note.
_TAX_BLOCK_ENDS = ("INFORMATION SUR VOTRE TARIF", "La TVA sur les prix indiqués")
# The excise is one row in the table and both bands in its footnote: "0-12.000
# kWh : 1,0929 c€/kWh, >= 12.001 kWh : 1,1830 c€/kWh".
_EXCISE_RE = re.compile(r"0-12\.000 kWh : (\d+,\d+) c€/kWh, >= 12\.001 kWh : (\d+,\d+) c€")


def _tax_rows(text: str, region: str) -> dict[str, float | None]:
    """The tax block's figures for ``region`` by row label, None for a dash.

    A card whose heading does not name the region is not the region's card.
    """
    heading = _TAX_HEADING_RE.search(text)
    if heading is None:
        raise ExtractorError("Luminus: tax block not found")
    tags = heading.group(1).split()
    tag = _REGION_TO_TAG[region]
    if tag not in tags:
        raise ExtractorError(f"Luminus: card is for {' '.join(tags)}, not {tag}")
    ends = [at for at in (text.find(e, heading.end()) for e in _TAX_BLOCK_ENDS) if at >= 0]
    if not ends:
        raise ExtractorError("Luminus: end of the tax block not found")
    end = min(ends)
    lines = [line.strip() for line in text[heading.end() : end].splitlines()]
    labels = [line for line in lines if line.endswith("(c€/kWh)")]
    values = [line for line in lines if _TAX_VALUE_RE.fullmatch(line)]
    if not labels or len(values) != len(labels) * len(tags):
        raise ExtractorError(
            f"Luminus: tax block has {len(values)} figures for {len(labels)} rows and {len(tags)} regions"
        )
    column = tags.index(tag) * len(labels)
    return {
        label: cell_value(value)
        for label, value in zip(labels, values[column : column + len(labels)], strict=True)
    }


def _tax_row(rows: dict[str, float | None], prefix: str) -> float | None:
    for label, value in rows.items():
        if label.startswith(prefix):
            return value
    raise ExtractorError(f"Luminus: tax row {prefix!r} not found")


def _taxes(text: str, region: str, vat_rate: float) -> TaxOverlay:
    rows = _tax_rows(text, region)
    excise = _EXCISE_RE.search(" ".join(text.split()))
    if excise is None:
        raise ExtractorError("Luminus: federal excise bands not found")
    contribution = _tax_row(rows, "Cotisation sur l")
    connection_fee = 0.0
    if region == REGION_WALLONIA:
        # Mandatory in Wallonia: a dash there is a misread, not a fee of zero.
        fee = _tax_row(rows, "Redevance de raccordement")
        if fee is None:
            raise ExtractorError("Luminus: Walloon connection fee not printed")
        connection_fee = fee / 100.0
    return TaxOverlay(
        excise_bands=excise_bands(
            to_float(excise.group(1)) / 100.0, to_float(excise.group(2)) / 100.0
        ),
        energy_contribution=0.0 if contribution is None else contribution / 100.0,
        connection_fee=connection_fee,
        card_vat_rate=vat_rate,
    )


# The indexation page links the PDF from its "Télécharger les indices" buttons.
_INDEX_LINK_RE = re.compile(
    r'href="/api-next/download/?\?fileId=(file-[0-9a-f]+-pdf)[^"]*"[^>]*>\s*<span>Télécharger les indices'
)

_INDEX_BY_TITLE = {title: name for name, (title, _) in _INDICES.items()}
_YEAR_RE = re.compile(r"20\d\d")
_QUARTER_RE = re.compile(r"Q([1-4])")
_FIGURE_RE = re.compile(r"\d+,\d+")
# A title sits just above and left of its year headings, the rows' labels
# start at most this far left of the first year, and a row's words share
# their top to within a few points.
_TITLE_REACH = 60.0
_LABEL_REACH = 60.0
_ROW_TOLERANCE = 3.0


def parse_index_page(page: str) -> str:
    """The URL of the index PDF the indexation page links."""
    ids = set(_INDEX_LINK_RE.findall(page))
    if len(ids) != 1:
        raise ExtractorError(f"Luminus: {len(ids)} index PDF links on the indexation page")
    return f"{_DOWNLOAD_URL}?fileId={ids.pop()}&openFile=true"


def _year_headings(rows: list[list[dict[str, Any]]]) -> list[list[dict[str, Any]]]:
    """Every run of consecutive years printed side by side on one line."""
    headings: list[list[dict[str, Any]]] = []
    for row in rows:
        run: list[dict[str, Any]] = []
        for word in row:
            if _YEAR_RE.fullmatch(word["text"]) and (
                not run or int(word["text"]) == int(run[-1]["text"]) + 1
            ):
                run.append(word)
                continue
            if len(run) > 1:
                headings.append(run)
            run = [word] if _YEAR_RE.fullmatch(word["text"]) else []
        if len(run) > 1:
            headings.append(run)
    return headings


def _table_lines(
    title: str, heading: list[dict[str, Any]], words: list[dict[str, Any]]
) -> list[str]:
    """One table as text: its title and years, then a line per period with a
    dash in every cell the PDF leaves empty.

    The table is the words under the heading and between its label column
    and its last year, and it ends at the first line that is not a period.
    """
    columns = [word_centre(word) for word in heading]
    half = (columns[1] - columns[0]) / 2.0
    left = float(heading[0]["x0"]) - _LABEL_REACH
    right = columns[-1] + half
    top = float(heading[0]["top"]) + _ROW_TOLERANCE
    body = [
        w
        for w in words
        if float(w["top"]) > top and float(w["x0"]) >= left and word_centre(w) <= right
    ]
    lines = [" ".join([title, *(word["text"] for word in heading)])]
    for label, *figures in word_rows(body, _ROW_TOLERANCE):
        if _period_months(label["text"]) is None:
            break
        cells = ["-"] * len(columns)
        for figure in figures:
            column = min(range(len(columns)), key=lambda i: abs(columns[i] - word_centre(figure)))
            if (
                not _FIGURE_RE.fullmatch(figure["text"])
                or abs(columns[column] - word_centre(figure)) > half
                or cells[column] != "-"
            ):
                raise ExtractorError(
                    f"Luminus: {title} {label['text']} figure {figure['text']!r} fits no year"
                )
            cells[column] = figure["text"]
        lines.append(" ".join([label["text"], *cells]))
    return lines


def _render_index(pdf: Any) -> str:
    lines: list[str] = []
    for page in pdf.pages:
        words = [w for w in page.extract_words() if w["upright"]]
        rows = word_rows(words, _ROW_TOLERANCE)
        headings = _year_headings(rows)
        for row in rows:
            texts = [word["text"] for word in row]
            for title in _INDEX_BY_TITLE:
                size = len(title.split())
                for i in range(len(row) - size + 1):
                    if " ".join(texts[i : i + size]) != title:
                        continue
                    x0, top = float(row[i]["x0"]), float(row[i]["top"])
                    below = [
                        h
                        for h in headings
                        if top < float(h[0]["top"]) <= top + _TITLE_REACH
                        and x0 < float(h[0]["x0"]) <= x0 + _TITLE_REACH
                    ]
                    if below:
                        heading = min(below, key=lambda h: float(h[0]["top"]))
                        lines += _table_lines(title, heading, words)
    return "\n".join(lines)


def index_table_text(payload: bytes) -> str:
    """The three gas index tables of Luminus's index PDF as text.

    Each is its title and years ("TTFDAHW 2024 2025 2026"), then one line per
    quarter or month with a figure or a dash per year. The formula a title
    sits beside names it again ("A * TTFDAHW + B * TTF 103 + C"); only the
    title has the years just below it.
    """
    return pdfplumber_text(payload, "index", _render_index)


def parse_index_text(text: str) -> IndexTable:
    """The index values by the cards' index names and month, in EUR/MWh.

    A quarterly value fills each month of its quarter.
    """
    table: IndexTable = {}
    name: str | None = None
    years: list[str] = []
    for line in text.splitlines():
        words = line.split()
        size = len([w for w in words if not _YEAR_RE.fullmatch(w)])
        title = " ".join(words[:size])
        if title in _INDEX_BY_TITLE:
            name = _INDEX_BY_TITLE[title]
            years = words[size:]
            if name in table:
                raise ExtractorError(f"Luminus: two {title} tables in the index PDF")
            table[name] = {}
            continue
        months = _period_months(words[0]) if words else None
        if name is None or months is None or len(words) != len(years) + 1:
            raise ExtractorError(f"Luminus: unreadable index row {line!r}")
        if (_INDICES[name][1] == "quarter") != (len(months) == 3):
            raise ExtractorError(f"Luminus: {name} row {words[0]!r} is not its period")
        for year, cell in zip(years, words[1:], strict=True):
            value = cell_value(cell)
            if value is not None:
                for month in months:
                    table[name][f"{year}-{month:02d}"] = value
    for title, name in _INDEX_BY_TITLE.items():
        if not table.get(name):
            raise ExtractorError(f"Luminus: no {title} values in the index PDF")
    return table


def _period_months(label: str) -> list[int] | None:
    """The months a row label covers: three for "Q2", one for "Février"."""
    quarter = _QUARTER_RE.fullmatch(label)
    if quarter is not None:
        return [3 * int(quarter.group(1)) - 2 + k for k in range(3)]
    month = MONTH_NAMES.get(fold_accents(label))
    return None if month is None else [month]


async def fetch_index(session: aiohttp.ClientSession) -> IndexTable:
    """Luminus's published gas index values."""
    url = parse_index_page(await fetch_text(session, _INDEX_PAGE_URL))
    text = await fetch_pdf_rendered(
        session, url, variant="luminus-index", timeout=30, render=index_table_text
    )
    return parse_index_text(text)


EXTRACTOR = SupplierExtractor(
    id="luminus",
    label="Luminus",
    contracts=tuple(
        Contract(
            id=c.contract_id,
            label=c.label,
            kind=c.kind,
            regions=frozenset(_REGION_TO_TAB),
        )
        for c in _CONTRACTS
    ),
    fetch=fetch,
    probe=probe,
    fetch_for_month=fetch_for_month,
    fetch_index=fetch_index,
    sweep_cost_s=1.0,
)
