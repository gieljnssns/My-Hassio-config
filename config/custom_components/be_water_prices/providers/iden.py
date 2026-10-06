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


"""IDEN -- Intercommunale de Distribution d'Eau de Nandrin, Tinlot et environs.

Three communes (Nandrin, Tinlot, Modave), tiny population. The operator
publishes its own card on ``iden_web/fr/Tarification.awp``: three
read-only form fields, each headed "Depuis le 1er janvier <year> :" and
labelled Distribution, Assainissement and Fonds Social de l'Eau.

Read from the operator rather than from an aggregator. Callmepower
carried 3,555 where IDEN's own page says 3,3552, a transposed digit that
over-stated an 80 m3 bill by 18 EUR a year, and nothing could see it: a
drift check compares the parser against its source, so a source that is
itself wrong is invisible to it.

Source: https://www.iden-eau.be/iden_web/fr/Tarification.awp
"""

from __future__ import annotations

import logging
import re

import aiohttp
from bs4 import BeautifulSoup

from ..const import REGION_WALLONIA, WALLONIA_CVA_EUR_PER_M3, WALLONIA_FSE_EUR_PER_M3
from ._html import fetch_and_parse
from ._pdf import to_float
from ._walloon_simple import build_tariff, detect_published_year, warn_constant_drift
from .base import ExtractorError, WaterExtractor, WaterTariff

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "iden"
LABEL = "IDEN"
SOURCE_URL = "https://www.iden-eau.be/iden_web/fr/Tarification.awp"
_LABEL_PREFIX = "IDEN tarification"

# The three rates sit in readonly <input> fields, so they are attributes
# rather than text and get_text() drops them. Inline each value where the
# input stands, then the labels and the values read in document order.
_INPUT_VALUE_RE = re.compile(r"<input\b[^>]*?\bvalue\s*=\s*\"([^\"]*)\"[^>]*>", re.IGNORECASE)
_VALUE_OPEN = "‹"
_VALUE_CLOSE = "›"

# The page wraps each initial in <strong>, so the rendered text reads
# "C oût- V érité à la D istribution". Anchor on the tail of the word that
# survives that split, and require the value to follow within one field so
# the explanatory FAQ further down the page cannot supply it.
_CVD_RE = re.compile(rf"istribution[^{_VALUE_OPEN}]{{0,40}}{_VALUE_OPEN}\s*(\d+,\d{{3,5}})")
_CVA_RE = re.compile(rf"ssainissement[^{_VALUE_OPEN}]{{0,40}}{_VALUE_OPEN}\s*(\d+,\d{{3,5}})")
_FSE_RE = re.compile(
    rf"ocial de l.\s*E\s*au[^{_VALUE_OPEN}]{{0,40}}{_VALUE_OPEN}\s*(\d+,\d{{3,5}})"
)


def _text_with_field_values(html: str) -> str:
    """The page's text with each input's value inlined where the input sits."""
    inlined = _INPUT_VALUE_RE.sub(lambda m: f" {_VALUE_OPEN}{m.group(1)}{_VALUE_CLOSE} ", html)
    soup = BeautifulSoup(inlined, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def _amount(text: str, pattern: re.Pattern[str], label: str) -> float:
    match = pattern.search(text)
    if match is None:
        raise ExtractorError(f"could not locate IDEN's {label} on {SOURCE_URL}")
    return to_float(match.group(1))


def parse_tariff(html: str, year: int | None = None) -> WaterTariff:
    """Parse IDEN's own tariff card."""
    text = _text_with_field_values(html)
    cvd = _amount(text, _CVD_RE, "CVD")
    # The page prints the two flat-Wallonia components next to the CVD, so
    # hold them to the SPGE constants the same way every other Walloon
    # extractor does.
    warn_constant_drift(
        published=_amount(text, _CVA_RE, "CVA"),
        constant=WALLONIA_CVA_EUR_PER_M3,
        label=f"{UTILITY_ID} CVA",
        logger=_LOGGER,
    )
    warn_constant_drift(
        published=_amount(text, _FSE_RE, "FSE"),
        constant=WALLONIA_FSE_EUR_PER_M3,
        label=f"{UTILITY_ID} FSE",
        logger=_LOGGER,
        threshold=0.001,
    )
    target = year or detect_published_year(text)
    if target is None:
        raise ExtractorError(f"IDEN states no tariff year on {SOURCE_URL}")
    return build_tariff(
        utility_id=UTILITY_ID,
        cvd=cvd,
        source_url=SOURCE_URL,
        publication_label=f"{_LABEL_PREFIX} {target}",
        year=target,
    )


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    return await fetch_and_parse(session, SOURCE_URL, parse_tariff)


EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_WALLONIA,
    fetch=fetch,
)
