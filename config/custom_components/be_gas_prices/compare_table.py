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

"""The comparison as a Markdown table for the options flow's pages."""

from __future__ import annotations

from .compare import Quote


def _cost(value: float | None) -> str:
    return "-" if value is None else f"{value:,.2f}"


def _price(value: float | None) -> str:
    return "-" if value is None else f"{value:.4f}"


def quote_table(quotes: list[Quote], *, own: Quote | None) -> str:
    """One row per quote, cheapest first as given, the household's own row in
    bold and the gap to it signed. A row marked with a dagger is provisional:
    priced at the last index value its supplier published, or at the price
    its card prints where the supplier publishes none, which the month may
    still move. OCR marks a card the card archive read off its image."""
    base = None if own is None else own.annual_cost
    lines = [
        "| # | Contract | EUR/year | Gap | EUR/kWh |",
        "|---|---|---:|---:|---:|",
    ]
    for rank, quote in enumerate(quotes, start=1):
        label = (
            quote.label
            + (" OCR" if quote.read_by_ocr else "")
            + (" †" if quote.provisional else "")
        )
        if quote is own or (
            own is not None and (quote.supplier, quote.contract) == (own.supplier, own.contract)
        ):
            label = f"**{label}**"
        gap = "-"
        if base is not None and quote.annual_cost is not None:
            gap = f"{quote.annual_cost - base:+,.2f}"
        position = str(rank) if quote.annual_cost is not None else "-"
        lines.append(
            f"| {position} | {label} | {_cost(quote.annual_cost)} | {gap} | {_price(quote.all_in)} |"
        )
    return "\n".join(lines)
