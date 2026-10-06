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

"""Commune redaction shared by the diagnostics dump and the sensor attributes.

Both surfaces leave the household's location behind if they publish a raw
string from the tariff snapshot: the diagnostics file is attached to GitHub
issues, and sensor attributes are written to the recorder and show up in
screenshots and exports.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import CONF_COMMUNE, CONF_COMMUNE_LABEL


def sensitive_tokens(entry: ConfigEntry) -> list[str]:
    """Commune strings that must not survive into a published string.

    Only the commune id and label leak (through the tariff's source_url,
    publication_label and last_error). The postcode is deliberately
    excluded: a bare 4-digit postcode would match years and ISO dates, e.g.
    valid_until or a label's publication year, and corrupt the output. A
    postcode embedded in a commune label is still scrubbed via the label.
    """
    tokens: set[str] = set()
    for src in (entry.data, entry.options):
        for key in (CONF_COMMUNE, CONF_COMMUNE_LABEL):
            value = src.get(key)
            if isinstance(value, str) and value:
                tokens.add(value)
    # Longest first so a label that contains the slug is replaced whole.
    return sorted(tokens, key=len, reverse=True)


def scrub_tokens(value: Any, tokens: list[str], placeholder: str = "**REDACTED**") -> Any:
    """Replace every token with ``placeholder`` throughout ``value``."""
    if isinstance(value, str):
        for token in tokens:
            value = value.replace(token, placeholder)
        return value
    if isinstance(value, dict):
        return {k: scrub_tokens(v, tokens, placeholder) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub_tokens(v, tokens, placeholder) for v in value]
    return value


def source_url_without_commune(source_url: str, commune: str | None) -> str:
    """Redact a per-commune slug from the tariff source URL.

    The Pidpa per-commune URL ends in the commune slug (the town name),
    so a published source_url would otherwise leak the household
    location into the recorder / screenshots just like the publication
    label. Other per-commune utilities do not carry the commune in the
    URL, so the substring check leaves them untouched.
    """
    if commune and commune in source_url:
        return source_url.replace(commune, "**redacted**")
    return source_url
