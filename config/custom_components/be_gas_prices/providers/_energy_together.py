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

"""The Energy Together gas card template, shared by its brands and Belvus.

Energy Together bv prints the gas card of each of its six brands from one
template (an Excel export), and Belvus printed its own on a copy of it until
August 2026. From September Belvus lays the card out its own way but keeps
the wording and every figure, so one reader takes both layouts. What it
reads, with pypdf:

  - the month and the product, "Particulier gas", then the product ("NOVA
    GAS", "FLEX ONLINE GAS", "FlexOnline"), then "september 2026". Evident
    Energie prints no product ("Tariefkaart particulier gas - september
    2026").
  - the fee, "Jaarlijkse abonnementskost €96", VAT inclusive like everything
    the card does not mark otherwise.
  - two energy prices excluding VAT: "*" the VNR estimate for the next twelve
    months and "**" the formula at the last known month ("laatst gekende
    waarde van TTF-DAM 8/2026: €61,72903/MWh"). The template prints
    "**€c7,67/kWh"; the Belvus layout puts the figure on the line above its
    "**".
  - the formula "(TTF_RLP x 1) + €15/MWh", excluding VAT, the index in EUR/MWh.
    The card states no VAT rate, so it is grossed up at the residential rate.
  - the excise bands and the energy contribution, VAT inclusive.
  - databeheer and transport, printed once for every Fluvius area: a lone
    "18,92 0,165" line out of a merged cell on the template, "€ 18,92/jaar"
    and "€ c 0,165/kW jaar" on the Belvus layout. The transport unit reads
    "€c/kW jaar"; the figure is the national Fluxys rate in c EUR/kWh.
  - the distribution table, "Variabel (€c/kWh) Vast (€/jaar)" for the tier up
    to 5 000 kWh and then for the one up to 150 000 kWh.

The distribution table's labels are wrong. The template prints them in the
order Antwerpen, Limburg, West, Imewo, Midden-Vlaanderen, Kempen,
Zenne-Dijle, Halle-Vilvoorde, while the figures follow the alphabetical order
every other card and the Flemish regulator use: the row labelled Limburg
carries Halle-Vilvoorde's 17,59 / 2,50 / 93,38 / 0,98, the one labelled
Midden-Vlaanderen carries Limburg's 14,59 / 2,24 / 77,46 / 0,98, and so on
down the table; only Antwerpen is right. So the rows are mapped by position,
and a card whose labels come in any other order is refused: were either the
labels or the figures moved, the position would no longer say whose figures
a row carries. The 2025 table is another matter: its rows carry their own
labels' figures, which by position would give seven areas out of eight
another area's tariff, and it breaks one row ("FLUVIUS LIMBURG 2,09 13,32
70,72 70,72"), whose mid tier :func:`._network.dso_overlay` drops as not
degressive. That broken row is what tells the 2025 table, and a card
printing it is refused.
"""

from __future__ import annotations

import re
from datetime import date

from ..const import (
    DSO_FLUVIUS_ANTWERPEN,
    DSO_FLUVIUS_HALLE_VILVOORDE,
    DSO_FLUVIUS_IMEWO,
    DSO_FLUVIUS_KEMPEN,
    DSO_FLUVIUS_LIMBURG,
    DSO_FLUVIUS_MIDDEN_VLAANDEREN,
    DSO_FLUVIUS_WEST,
    DSO_FLUVIUS_ZENNE_DIJLE,
    TIER_T2,
    VAT_RATE_REDUCED,
)
from ._network import T1_FIXED, T1_PROP, T2_FIXED, T2_PROP, dso_overlay, excise_bands
from ._parse import fold_accents, month_date, split_row, to_float
from ._pdf import NL_MONTHS
from ._rates import IndexedRates
from ._validity import end_of_month
from .base import DsoOverlay, ExtractorError, SupplierSnapshot, TaxOverlay

# The index the formula names, and the name its values are published under.
INDEX = "TTF_RLP"

_MONTHS = "|".join(NL_MONTHS)
_CARD_MONTH_RE = re.compile(
    rf"Particulier\s+gas\b(.{{0,60}}?)\b({_MONTHS})\s+(20\d{{2}})\b",
    re.IGNORECASE | re.DOTALL,
)


def product_key(name: str) -> str:
    """A product name as the cards and listings compare it: letters and
    digits only, lower case, without the trailing "gas" the card adds."""
    return re.sub(r"[^0-9a-z]", "", fold_accents(name)).removesuffix("gas")


def card_month(text: str, label: str) -> tuple[date, str]:
    """The card's month and the product it names ("" when it names none)."""
    match = _CARD_MONTH_RE.search(text)
    if match is None:
        raise ExtractorError(f"{label}: card month not found")
    month = NL_MONTHS.index(match.group(2).lower()) + 1
    return date(int(match.group(3)), month, 1), product_key(match.group(1))


_FEE_RE = re.compile(r"Jaarlijkse abonnementskost[^€\n]*€\s*(\d+(?:,\d+)?)")
_LAST_KNOWN_PRICE_RE = re.compile(
    r"\*\*\s*€c\s*(\d+,\d+)\s*/kWh|^(\d+,\d+)[ \t]*\n\*\*[ \t]*$", re.MULTILINE
)
_FORMULA_RE = re.compile(
    r"\(\s*TTF_RLP\s*[x×]\s*(\d+(?:,\d+)?)\s*\)\s*\+\s*€\s*(\d+(?:,\d+)?)\s*/MWh"
)


def _energy(text: str, label: str) -> IndexedRates:
    fee = _FEE_RE.search(text)
    price = _LAST_KNOWN_PRICE_RE.search(text)
    formula = _FORMULA_RE.search(text)
    if fee is None or price is None or formula is None:
        raise ExtractorError(f"{label}: fee, price or formula not found")
    vat = 1.0 + VAT_RATE_REDUCED
    return IndexedRates(
        factor=to_float(formula.group(1)) / 1000.0 * vat,
        base=to_float(formula.group(2)) / 1000.0 * vat,
        index=INDEX,
        price=to_float(price.group(1) or price.group(2)) / 100.0 * vat,
        yearly_fixed_fee=to_float(fee.group(1)),
        formula=formula.group(0),
    )


# "laatst gekende waarde van TTF-DAM 8/2026: €61,72903/MWh". Belvus's cards
# up to April 2026 read "Belpex TTF-DAM 12/2025: €27,652/MWh", and the April
# one wraps after "TTF-" and drops the colon. From October 2026 Belvus names
# the same value "TTF RLP-M 9/2026: €75,35/MWh".
_LAST_KNOWN_INDEX_RE = re.compile(
    r"laatst\s+gekende\s+waarde\s+van\s+(?:Belpex\s+)?TTF(?:-\s*DAM|\s+RLP-M)\s+"
    r"(\d{1,2})/(\d{4}):?\s*€\s*(\d+,\d+)\s*/MWh"
)


def last_known_index(text: str) -> tuple[date, float] | None:
    """The month and the EUR/MWh value the card's "**" price is computed on,
    or None for a card that does not state them.

    The month is as printed, which is not always right: Evident Energie's
    August 2026 card reads "7/2036".
    """
    match = _LAST_KNOWN_INDEX_RE.search(text)
    if match is None:
        return None
    try:
        month = month_date(match.group(2), match.group(1), "Energy Together")
    except ExtractorError:
        return None
    return month, to_float(match.group(3))


_EXCISE_RE = re.compile(
    r"Bijzondere accijns op Energie\s*<\s*12\.000 kWh(.*?)Bijdrage op Energie", re.DOTALL
)
_EXCISE_HIGH_LABEL_RE = re.compile(r"Bijzondere accijns op Energie\s*>\s*12\.000 kWh")
_CENT_RE = re.compile(r"€\s*c\s*(\d+,\d+)")
_CONTRIBUTION_RE = re.compile(r"Bijdrage op Energie\s*€\s*c\s*(\d+,\d+)")


def _taxes(text: str, label: str) -> TaxOverlay:
    """The excise bands and the energy contribution.

    Both excise labels come first on the August Belvus card and their two
    rates after them, so the rates are read in order between the first label
    and the contribution rather than off each label's line.
    """
    block = _EXCISE_RE.search(text)
    rates = _CENT_RE.findall(block.group(1)) if block else []
    contribution = _CONTRIBUTION_RE.search(text)
    if block is None or not _EXCISE_HIGH_LABEL_RE.search(block.group(1)) or len(rates) != 2:
        raise ExtractorError(f"{label}: excise rows not found")
    if contribution is None:
        raise ExtractorError(f"{label}: energy contribution not found")
    return TaxOverlay(
        excise_bands=excise_bands(to_float(rates[0]) / 100.0, to_float(rates[1]) / 100.0),
        energy_contribution=to_float(contribution.group(1)) / 100.0,
    )


_NETWORK_FEES_RE = re.compile(
    r"^[ \t]*(\d+,\d+)[ \t]+(\d+,\d+)[ \t]*$"
    r"|€\s*(\d+,\d+)\s*/jaar[ \t]*\n[^\n]*\n\s*€\s*c\s*(\d+,\d+)\s*/kW jaar",
    re.MULTILINE,
)


def _network_fees(text: str, label: str) -> tuple[float, float]:
    """Databeheer in EUR/year and transport in EUR/kWh."""
    matches = list(_NETWORK_FEES_RE.finditer(text))
    if len(matches) != 1:
        raise ExtractorError(f"{label}: data management and transport not found")
    match = matches[0]
    metering = match.group(1) or match.group(3)
    transport = match.group(2) or match.group(4)
    return to_float(metering), to_float(transport) / 100.0


# The Fluvius labels in the order the template prints them, and whose figures
# each of those rows actually carries: alphabetical order.
_PRINTED_LABELS = (
    "ANTWERPEN",
    "LIMBURG",
    "WEST",
    "IMEWO",
    "MIDDEN-VLAANDEREN",
    "KEMPEN",
    "ZENNE-DIJLE",
    "HALLE-VILVOORDE",
)
_ROW_OWNERS = (
    DSO_FLUVIUS_ANTWERPEN,
    DSO_FLUVIUS_HALLE_VILVOORDE,
    DSO_FLUVIUS_IMEWO,
    DSO_FLUVIUS_KEMPEN,
    DSO_FLUVIUS_LIMBURG,
    DSO_FLUVIUS_MIDDEN_VLAANDEREN,
    DSO_FLUVIUS_WEST,
    DSO_FLUVIUS_ZENNE_DIJLE,
)
_COLUMNS = (T1_PROP, T1_FIXED, T2_PROP, T2_FIXED)


def _dsos(text: str, label: str) -> dict[str, DsoOverlay]:
    """The eight Fluvius areas, mapped by the position of their row.

    The August Belvus card wraps "FLUVIUS MIDDEN-" above "VLAANDEREN" and its
    figures, so a line ending in a hyphen is joined to the next first.
    """
    metering, transport = _network_fees(text, label)
    rows: list[tuple[str, list[str]]] = []
    for line in re.sub(r"-[ \t]*\n[ \t]*", "-", text).splitlines():
        row_label, cells = split_row(line)
        words = row_label.upper().split()
        if len(cells) == len(_COLUMNS) and len(words) == 2 and words[0] == "FLUVIUS":
            rows.append((words[1], cells))
    printed = tuple(name for name, _ in rows)
    if printed != _PRINTED_LABELS:
        raise ExtractorError(
            f"{label}: Fluvius rows read {', '.join(printed) or 'none'}, not the order "
            "this reader maps by position"
        )
    overlays = {
        owner: dso_overlay(
            cells, _COLUMNS, supplier=label, label=owner, transport=transport, metering=metering
        )
        for owner, (_, cells) in zip(_ROW_OWNERS, rows, strict=True)
    }
    if any(TIER_T2 not in overlay.tiers for overlay in overlays.values()):
        raise ExtractorError(
            f"{label}: a Fluvius row is not degressive, as on the 2025 table, whose rows "
            "carry their own labels' figures rather than this reader's positions"
        )
    return overlays


def parse_card(
    text: str,
    *,
    supplier: str,
    label: str,
    contract: str,
    product: str,
    source_url: str,
) -> SupplierSnapshot:
    """One card of the template, as pypdf extracts it.

    ``product`` is the product as the card names it, compared through
    :func:`product_key` so spacing and case do not matter; "" for a card
    that names none. A card naming another product is refused, since the
    brands link one card from several product groups and a wrong link would
    otherwise price the wrong product.
    """
    month, printed = card_month(text, label)
    if printed != product_key(product):
        raise ExtractorError(f"{label}: card is for {printed or 'no product'!r}, not {product!r}")
    return SupplierSnapshot(
        supplier=supplier,
        contract=contract,
        energy=_energy(text, label),
        dsos=_dsos(text, label),
        taxes=_taxes(text, label),
        source_url=source_url,
        publication_label=f"{month:%Y-%m}",
        valid_until=end_of_month(month.year, month.month),
    )
