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

"""The gross calorific value of the gas, per reception station and month.

A gas meter counts cubic metres and the bill counts kWh. The DSO converts one
into the other with the calorific value of the reception station (GOS) the
connection is fed from, published monthly for every station in Belgium by
Atrias, the market's clearing house:

    https://api.atrias.be/roots/download/SectorData/02 Gross Calorific Values/
        <YYYY>/GCV<YYYYMM>.txt?subscription-key=<key>

The key is the public one Atrias's own site carries in ``runtime-config.js``;
it is read from there rather than copied into this file. A month's file lands
in the first days of the next month. The value is in kWh per normal cubic
metre: the DSO also corrects the metered volume for pressure and temperature
(9 C is assumed without a volume converter), which this value leaves out,
so the factor printed on the bill is the default and this is for a household
without one at hand.

api.atrias.be does not send its intermediate certificate, so a plain TLS
handshake fails verification. The public "Go Daddy Secure Certificate
Authority - G2" intermediate ships beside this module and is added to an
otherwise standard client context, rather than verification being turned off.
"""

from __future__ import annotations

import csv
import io
import json
import re
import ssl
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import aiohttp
from homeassistant.util.ssl import create_client_context

from .const import ATRIAS_API_URL, ATRIAS_CONFIG_URL
from .providers._parse import to_float
from .providers._pdf import USER_AGENT, error_text
from .providers.base import ExtractorError

_INTERMEDIATE = Path(__file__).with_name("certs") / "godaddy_g2_intermediate.pem"
_KEY_RE = re.compile(r"apimSubscriptionKey\s*:\s*['\"]([0-9a-fA-F]+)['\"]")
_TIMEOUT = aiohttp.ClientTimeout(total=30)


class CalorificError(Exception):
    """The calorific values could not be fetched or read."""


@dataclass(frozen=True)
class Station:
    """One gas reception station as Atrias names it."""

    ean: str
    name: str


def build_ssl_context() -> ssl.SSLContext:
    """A client context that also trusts the intermediate Atrias omits.

    Blocking: it reads the CA bundle and the certificate from disk, so it is
    run in the executor.
    """
    context = create_client_context()
    context.load_verify_locations(cadata=_INTERMEDIATE.read_text(encoding="ascii"))
    return context


async def subscription_key(session: aiohttp.ClientSession) -> str:
    """The public API key Atrias's site publishes in its runtime config."""
    try:
        async with session.get(
            ATRIAS_CONFIG_URL, headers={"User-Agent": USER_AGENT}, timeout=_TIMEOUT
        ) as resp:
            if resp.status >= 400:
                raise CalorificError(f"HTTP {resp.status} fetching {ATRIAS_CONFIG_URL}")
            # Not strict, so a page in another charset fails the key search
            # below as a CalorificError rather than escaping as a decode error.
            body = await resp.text(errors="replace")
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CalorificError(
            f"network error fetching {ATRIAS_CONFIG_URL}: {error_text(err)}"
        ) from err
    match = _KEY_RE.search(body)
    if match is None:
        raise CalorificError("Atrias runtime config carries no subscription key")
    return match.group(1)


_FOLDER = "SectorData/02 Gross Calorific Values"
_FILE_RE = re.compile(r"^GCV(\d{4})(\d{2})\.txt$")


async def _get(
    session: aiohttp.ClientSession,
    context: ssl.SSLContext,
    url: str,
    params: dict[str, str],
) -> bytes:
    try:
        async with session.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT},
            ssl=context,
            timeout=_TIMEOUT,
        ) as resp:
            if resp.status >= 400:
                raise CalorificError(f"HTTP {resp.status} fetching {url}")
            return await resp.read()
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CalorificError(f"network error fetching {url}: {error_text(err)}") from err


async def list_months(
    session: aiohttp.ClientSession, context: ssl.SSLContext, key: str
) -> dict[str, str]:
    """Every month Atrias has published, as {"YYYY-MM": file path}.

    Listed rather than guessed: a month not published yet answers a 400
    wrapping the storage's "blob does not exist", which says nothing an
    ordinary failure would not.
    """
    payload = await _get(
        session,
        context,
        f"{ATRIAS_API_URL}/folder/list",
        {"folder": _FOLDER, "subscription-key": key},
    )
    try:
        years = json.loads(payload)
        months = {
            f"{match.group(1)}-{match.group(2)}": str(entry["url"])
            for year in years
            for entry in year.get("children", [])
            if (match := _FILE_RE.match(str(entry.get("name", ""))))
        }
    except (ValueError, TypeError, AttributeError, KeyError) as err:
        raise CalorificError(f"Atrias folder list is not what it was: {err}") from err
    if not months:
        raise CalorificError("Atrias lists no calorific value file")
    return months


def parse_gcv_file(payload: bytes) -> dict[Station, float]:
    """One month's file as {station: kWh/m3(n)}.

    The files vary from month to month: a byte order mark or a preamble line
    before the header, a header misspelt "SGCVMonth", the columns in another
    order, the decimal a quoted comma or a dot. A station listed at 0 is not
    in use that month and is left out, as is one with no value at all.
    """
    text = payload.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if "ARSName" in line)
    except StopIteration:
        raise CalorificError("calorific value file has no header") from None
    try:
        rows = list(csv.reader(io.StringIO("\n".join(lines[start:]))))
    except csv.Error as err:
        raise CalorificError(f"calorific value file is not CSV: {err}") from None
    header = [cell.strip().lstrip("﻿") for cell in rows[0]]
    try:
        name_at = header.index("ARSName")
        ean_at = header.index("ARSEanGSRN")
        value_at = header.index("GCVValue")
    except ValueError:
        raise CalorificError(f"calorific value file has an unknown header {header}") from None
    out: dict[Station, float] = {}
    for row in rows[1:]:
        if len(row) <= max(name_at, ean_at, value_at):
            continue
        cell = row[value_at].strip()
        if not cell:
            # No value that month, like a station listed at 0.
            continue
        try:
            value = to_float(cell)
        except ExtractorError:
            raise CalorificError(f"calorific value file has a bad value {cell!r}") from None
        if value > 0:
            out[Station(ean=row[ean_at].strip(), name=row[name_at].strip())] = value
    if not out:
        raise CalorificError("calorific value file lists no station")
    return out


async def fetch_month(
    session: aiohttp.ClientSession, context: ssl.SSLContext, key: str, path: str
) -> dict[Station, float]:
    """The calorific values of the month file at ``path``, as listed."""
    url = f"{ATRIAS_API_URL}/download/{quote(path, safe='')}"
    return parse_gcv_file(await _get(session, context, url, {"subscription-key": key}))
