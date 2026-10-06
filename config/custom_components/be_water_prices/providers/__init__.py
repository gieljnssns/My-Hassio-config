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

"""Water-utility extractor registry.

Each utility module exposes a top-level ``EXTRACTOR``. Adding a new
utility means appending its module name to ``_MODULE_NAMES`` below.

The registry is built lazily on first call so importing a sibling
sub-module (e.g. ``_postcodes``) from a stdlib-only refresh script
does not pull in aiohttp / BeautifulSoup / pdfplumber via every
extractor module at package init time.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from .base import (
    ExtractorError,
    TransientFetchError,
    WaterExtractor,
    WaterTariff,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Insertion order is the user-facing order in the manual-picker
# dropdown. VIVAQUA is Brussels, the six after it are the Flemish
# operators, and the nine below those are Walloon.
_MODULE_NAMES: tuple[str, ...] = (
    "vivaqua",
    "de_watergroep",
    "pidpa",
    "aquaduin",
    "agso_knokke",
    "water_link",
    "farys",
    "swde",
    "inbw",
    "cile",
    "inasep",
    "ieg",
    "aiem",
    "aiec",
    "ciesac",
    "iden",
    # Still deferred:
    #   - ~30 régies communales: no central publication channel found yet;
    #     deferred indefinitely on dev-hours / customer ratio.
)

_REGISTRY: dict[str, WaterExtractor] | None = None


def _build_registry() -> dict[str, WaterExtractor]:
    global _REGISTRY
    if _REGISTRY is None:
        out: dict[str, WaterExtractor] = {}
        for name in _MODULE_NAMES:
            mod = import_module(f".{name}", __package__)
            out[mod.EXTRACTOR.id] = mod.EXTRACTOR
        _REGISTRY = out
    return _REGISTRY


def get(utility_id: str) -> WaterExtractor:
    try:
        return _build_registry()[utility_id]
    except KeyError as err:
        raise ExtractorError(f"no extractor registered for utility {utility_id!r}") from err


def all_extractors() -> tuple[WaterExtractor, ...]:
    return tuple(_build_registry().values())


async def async_load(hass: HomeAssistant) -> None:
    """Build the registry off the event loop.

    Importing the extractor modules pulls in pdfplumber / BeautifulSoup /
    aiohttp and reads manifest.json for the User-Agent string -- blocking
    work Home Assistant forbids on the loop thread. Async callers run this
    once so the later synchronous ``get`` / ``all_extractors`` lookups hit
    the cached registry instead of importing on the loop.
    """
    await hass.async_add_executor_job(_build_registry)


def __getattr__(name: str) -> dict[str, WaterExtractor]:
    # Back-compat alias for callers that imported ``EXTRACTORS`` (the
    # dict) directly. Building lazily keeps the import side-effect-free.
    if name == "EXTRACTORS":
        return _build_registry()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "EXTRACTORS",
    "ExtractorError",
    "TransientFetchError",
    "WaterExtractor",
    "WaterTariff",
    "all_extractors",
    "async_load",
    "get",
]
