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

"""HTML scraping helpers for water-utility tariff pages.

Most Belgian water utilities publish their numerical tariff card on a
plain HTML page, often in a ``<table>``. This module provides:

* :func:`fetch_html` -- async GET wrapper that mirrors :func:`_pdf.fetch_text`
  but returns the raw HTML body. (Re-exported from ``_pdf`` so a future
  caller does not need to import both modules.)
* :func:`extract_amounts` -- regex helper that pulls every ``€ 12,34``
  amount from a string in document order.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from ._pdf import fetch_text, to_float

# Re-export so callers can import everything they need from this module.
fetch_html = fetch_text
__all__ = [
    "BeautifulSoup",
    "extract_amounts",
    "fetch_and_parse",
    "fetch_html",
    "to_float",
]


async def fetch_and_parse[T](
    session: aiohttp.ClientSession,
    url: str,
    parser: Callable[..., T],
    *args: Any,
    verify_ssl: bool = True,
    **kwargs: Any,
) -> T:
    """GET ``url`` then run ``parser`` on the body off the event loop.

    HTML parsing (BeautifulSoup, or a heavy regex over a large page) is
    pure-CPU work. Running it inline after the ``await`` would block the
    asyncio loop for tens of milliseconds on a real tariff page, which
    HA's blocking-I/O guard cannot detect. Hand it to a worker thread,
    mirroring the PDF helpers, which already offload extraction.
    """
    html = await fetch_html(session, url, verify_ssl=verify_ssl)
    return await asyncio.to_thread(parser, html, *args, **kwargs)


# The integer part is either a plain digit run or groups of three split
# by one of the space-family thousands separators Belgian publications
# use, which ``to_float`` strips. Dot-grouped thousands are left alone on
# purpose: SWDE prints dot decimals with three digits ("€ 2.748"), and no
# rule can tell that from a grouped thousand. The digit guards on both
# sides keep "Tarif 2025 100,00 €" from reading as 25100.
_NUMBER = (
    r"(?<![0-9])((?:[0-9]{1,3}(?:[     ][0-9]{3})+|[0-9]+)"
    r"(?:[.,][0-9]+)?)(?![0-9])"
)
# A minus glued to the euro sign ("-€ 4,00") or to the number ("€ -6,00",
# "-6,00 €") is a discount; a dash standing on its own between blanks
# ("2025 - € 10,00") is punctuation and does not touch the sign.
_AMOUNT_BEFORE_EURO = re.compile(r"(-?)€\s*(-?)" + _NUMBER)
_AMOUNT_AFTER_EURO = re.compile(r"(-?)" + _NUMBER + r"\s*€")


def extract_amounts(text: str) -> list[float]:
    """Return every euro amount found in ``text``, in order.

    Accepts both Dutch / English layout (``€ 12,34``) and French layout
    (``12,34 €``); some Walloon utility pages publish the symbol after
    the number. A space-grouped thousand (``€ 1 234,56``, with any of
    the space variants) is one amount. A minus written against the sign
    or the number makes it negative, as a discount line prints. Hits are
    de-duplicated by start position so a string like "€ 12,34 €" reports
    12.34 once.
    """
    seen: dict[int, float] = {}
    for pattern in (_AMOUNT_BEFORE_EURO, _AMOUNT_AFTER_EURO):
        for m in pattern.finditer(text):
            number = m.lastindex or 1
            value = to_float(m.group(number))
            if "-" in m.groups()[: number - 1]:
                value = -value
            seen[m.start(number)] = value
    return [seen[k] for k in sorted(seen)]
