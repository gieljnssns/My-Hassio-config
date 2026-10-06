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

"""Supplier extractor registry.

Each supplier module exposes a top-level ``EXTRACTOR``; adding a supplier
means adding its module and one line below.
"""

from __future__ import annotations

from .base import ExtractorError, SupplierExtractor
from .belvus import EXTRACTOR as _BELVUS
from .bolt import EXTRACTOR as _BOLT
from .custom import EXTRACTOR as _CUSTOM
from .dots import EXTRACTOR as _DOTS
from .ebem import EXTRACTOR as _EBEM
from .ecofix import EXTRACTOR as _ECOFIX
from .elegant import EXTRACTOR as _ELEGANT
from .eneco import EXTRACTOR as _ENECO
from .energiebe import EXTRACTOR as _ENERGIEBE
from .energy_together import EXTRACTORS as _ENERGY_TOGETHER
from .energyvision import EXTRACTOR as _ENERGYVISION
from .engie import EXTRACTOR as _ENGIE
from .frank import EXTRACTOR as _FRANK
from .luminus import EXTRACTOR as _LUMINUS
from .mega import EXTRACTOR as _MEGA
from .octaplus import EXTRACTOR as _OCTAPLUS
from .sparki import EXTRACTOR as _SPARKI
from .totalenergies import EXTRACTOR as _TOTALENERGIES
from .trevion import EXTRACTOR as _TREVION

EXTRACTORS: dict[str, SupplierExtractor] = {
    _ENECO.id: _ENECO,
    _ENGIE.id: _ENGIE,
    _LUMINUS.id: _LUMINUS,
    _MEGA.id: _MEGA,
    _TOTALENERGIES.id: _TOTALENERGIES,
    _OCTAPLUS.id: _OCTAPLUS,
    _BOLT.id: _BOLT,
    _ENERGYVISION.id: _ENERGYVISION,
    _ELEGANT.id: _ELEGANT,
    _TREVION.id: _TREVION,
    # One card template, six brands, each a supplier of its own to a household.
    **{extractor.id: extractor for extractor in _ENERGY_TOGETHER},
    _BELVUS.id: _BELVUS,
    _SPARKI.id: _SPARKI,
    _DOTS.id: _DOTS,
    _ENERGIEBE.id: _ENERGIEBE,
    _EBEM.id: _EBEM,
    _FRANK.id: _FRANK,
    # Its cards are page images: an entry prices on the card archive's OCR
    # reading of them.
    _ECOFIX.id: _ECOFIX,
    # The expert escape hatch, last so it sorts to the end of the list.
    _CUSTOM.id: _CUSTOM,
}


def get(supplier_id: str) -> SupplierExtractor:
    """The registered extractor for ``supplier_id``."""
    try:
        return EXTRACTORS[supplier_id]
    except KeyError as err:
        raise ExtractorError(f"no extractor registered for supplier {supplier_id!r}") from err


def all_extractors() -> tuple[SupplierExtractor, ...]:
    return tuple(EXTRACTORS.values())
