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

"""A household's region and gas DSO from its postcode.

The table comes from scripts/refresh_postcodes.py (bpost's postcode list and
Synergrid's DSO lookup per locality). A postcode can name several DSOs when
its localities differ, or none where no locality has gas; the setup flow
then asks. Part of a postcode can also be on a DSO no Belgian card prices
(Baarle-Hertog's Enexis), which the setup flow warns about.
"""

from __future__ import annotations

from dataclasses import dataclass

from .const import REGION_BRUSSELS, REGION_DSO_KEYS, REGION_FLANDERS, REGION_WALLONIA
from .postcode_map import POSTCODES, UNPRICED

_REGION_OF_DSO: dict[str, str] = {
    dso: region for region, dsos in REGION_DSO_KEYS.items() for dso in dsos
}


@dataclass(frozen=True)
class PostcodeMatch:
    """The region of a postcode, the sorted gas DSO keys serving it, and the
    names of the gas DSOs serving part of it that no card prices."""

    region: str
    dsos: tuple[str, ...]
    unpriced: tuple[str, ...] = ()


def _region_of_range(code: int) -> str:
    """The region by bpost's postcode ranges, for a postcode without gas."""
    if 1000 <= code <= 1299:
        return REGION_BRUSSELS
    if 1300 <= code <= 1499 or 4000 <= code <= 7999:
        return REGION_WALLONIA
    return REGION_FLANDERS


def resolve(postcode: str) -> PostcodeMatch | None:
    """The match for a Belgian postcode, None for any other string."""
    dsos = POSTCODES.get(postcode)
    if dsos is None:
        return None
    unpriced = UNPRICED.get(postcode, ())
    if dsos:
        return PostcodeMatch(_REGION_OF_DSO[dsos[0]], dsos, unpriced)
    return PostcodeMatch(_region_of_range(int(postcode)), dsos, unpriced)
