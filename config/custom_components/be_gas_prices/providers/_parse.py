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

"""Reading a figure off a line of a tariff card.

Belgian cards print numbers in several ways: a comma decimal, a dot decimal,
a thousands separator beside a decimal comma, a dash for an empty cell. These
turn a line of extracted text, or a row of an HTML table, into numbers, or
refuse rather than guess. They know nothing about which supplier printed it.
"""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Mapping
from datetime import date
from difflib import SequenceMatcher

from .base import ExtractorError

# Every Unicode space variant Belgian PDFs use inside a figure, as a
# thousands separator or as padding.
_NUMERIC_SEPARATORS = (
    " ",  # ASCII space
    " ",  # NO-BREAK SPACE
    " ",  # THIN SPACE
    " ",  # NARROW NO-BREAK SPACE, the CLDR French thousands separator
    " ",  # LINE SEPARATOR
)

# Every character a card has used for a minus sign or a dash: hyphen-minus,
# hyphen, non-breaking hyphen, figure dash, en dash, em dash, minus sign.
_DASHES = ("-", "‐", "‑", "‒", "–", "—", "−")
SIGN_CHARS = r"+\-‐‑‒–—−"
"""Drop into a regex character class: ``[`` + SIGN_CHARS + ``]``."""

# One table cell: a figure, or a lone dash for an empty cell. A figure may
# carry thousands separators and a decimal part in either convention.
_CELL = re.compile(r"^(?:\d+(?:[.,]\d+)*|[" + "".join(_DASHES) + r"])$")
_FIGURE = re.compile(r"\d+(?:[.,]\d+)*")


def month_date(year: str | int, month: str | int, label: str) -> date:
    """The first day of the month a card names, or an ExtractorError naming
    ``label`` when the figures are no month ("0000", "13")."""
    try:
        return date(int(year), int(month), 1)
    except ValueError:
        raise ExtractorError(f"{label}: {year}-{month} is no month") from None


def fold_accents(text: str) -> str:
    """Lowercase and strip Latin diacritics, so an extraction that lost its
    accents ("aout") still matches the spelled one ("août")."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c)
    )


def to_float(text: str) -> float:
    """Parse a figure as Belgian cards print it.

    A comma is the decimal separator; so is a lone dot, which Mega and a few
    others print. When both appear the dot groups thousands and the comma is
    the decimal ("1.001,55", EnergyVision's Sibelga T3). Every space variant
    is dropped first, since cards also group thousands with a narrow space.
    """
    cleaned = text.strip()
    for sep in _NUMERIC_SEPARATORS:
        cleaned = cleaned.replace(sep, "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "")
    try:
        return float(cleaned.replace(",", "."))
    except ValueError as err:
        raise ExtractorError(f"not a figure: {text!r}") from err


def parse_sign(char: str) -> float:
    """-1.0 for any dash or minus variant, +1.0 otherwise."""
    return -1.0 if char in _DASHES else 1.0


def require_contract[T](by_id: Mapping[str, T], contract_id: str, label: str) -> T:
    """The contract definition for ``contract_id``, or raise."""
    try:
        return by_id[contract_id]
    except KeyError:
        raise ExtractorError(f"unknown {label} contract {contract_id!r}") from None


_HTML_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
_HTML_CELL_RE = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def html_cells(row: str) -> list[str]:
    """The text of each cell of one HTML table row, tags dropped, entities
    decoded and whitespace collapsed."""
    return [
        " ".join(html.unescape(_HTML_TAG_RE.sub(" ", cell)).split())
        for cell in _HTML_CELL_RE.findall(row)
    ]


def html_rows(page: str) -> list[list[str]]:
    """Every ``<tr>`` of ``page`` as its cells' text."""
    return [html_cells(row) for row in _HTML_ROW_RE.findall(page)]


def split_row(line: str) -> tuple[str, list[str]]:
    """A table line as its label and its cells.

    The cells are read from the right: the trailing run of figures and lone
    dashes. Everything before them is the label, so a label that carries a
    dash of its own ("TECTEO - RESA") or a figure in the middle keeps it.
    """
    words = line.split()
    end = len(words)
    while end and _CELL.match(words[end - 1]):
        end -= 1
    return " ".join(words[:end]).rstrip(":").strip(), words[end:]


def cell_value(cell: str) -> float | None:
    """A cell as a float, or None for a dash."""
    if cell in _DASHES:
        return None
    return to_float(cell)


def table_row(
    text: str,
    label: str,
    columns: int | None = None,
    *,
    after: str | None = None,
    before: str | None = None,
    threshold: float = 0.82,
) -> list[str] | None:
    """The cells of the table row whose label reads as ``label``.

    The label is matched by similarity rather than spelling, because a card
    misspells now and then ("Fuvius Halle-Vilvoorde") and pads others
    ("Fluvius (Antwerpen )"). A row's cells are all on ONE line; the only
    line looked past is a label too long for its column that wrapped above
    its own cells, leaving them alone on the next line. Where the caller
    knows the column count from the card's headings it has to match.
    ``after`` and ``before`` bound the search to the block the row belongs
    to.

    Returns the cells as printed, or None when nothing matches well enough.
    A wrong row is worse than no row, so the caller raises where the card
    promises one.
    """
    body = text
    if after is not None:
        start = body.find(after)
        if start < 0:
            return None
        body = body[start + len(after) :]
    if before is not None:
        end = body.find(before)
        if end >= 0:
            body = body[:end]

    best: tuple[float, list[str]] | None = None
    lines = body.splitlines()
    for index, line in enumerate(lines):
        row_label, cells = split_row(line)
        if not cells or not any(_FIGURE.fullmatch(c) for c in cells):
            continue
        if columns is not None and len(cells) != columns:
            continue
        if not row_label and index:
            previous_label, previous_cells = split_row(lines[index - 1])
            if not previous_cells:
                row_label = previous_label
        score = SequenceMatcher(None, row_label.lower(), label.lower()).ratio()
        if score >= threshold and (best is None or score > best[0]):
            best = (score, cells)
    return None if best is None else best[1]
