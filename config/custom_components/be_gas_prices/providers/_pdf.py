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

"""Shared helpers for fetching and reading PDF tariff cards."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from io import BytesIO
from pathlib import Path
from typing import Any

import aiohttp
import pypdf

from ._parse import (
    to_float,
)
from .base import (
    CardNotReadableError,
    ExtractorError,
)

_LOGGER = logging.getLogger(__name__)


class _NoFontToolsAdvice(logging.Filter):
    """Drop pypdf's advice to install fontTools, and nothing else.

    pypdf logs it at WARNING for every CFF font it meets, several times per
    Engie card, and the cards read correctly without fontTools: the tests
    pin every figure. Left alone it would put a screenful of font
    dictionaries in the Home Assistant log on every fetch.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return not str(record.msg).startswith("fontTools is required")


logging.getLogger("pypdf._cmap").addFilter(_NoFontToolsAdvice())


def _read_version() -> str:
    manifest = Path(__file__).resolve().parent.parent / "manifest.json"
    try:
        return str(json.loads(manifest.read_text(encoding="utf-8")).get("version", "0"))
    except (OSError, ValueError):
        return "0"


USER_AGENT = f"Home Assistant be_gas_prices/{_read_version()}"


def is_transient_fetch_error(message: str) -> bool:
    """Whether an ExtractorError message describes a transient fetch
    failure a later refresh is likely to recover, rather than a permanent
    one (parse error, 404, non-PDF payload) that needs a code fix.

    The fetch helpers in this module wrap aiohttp surface errors with three
    stable prefixes: ``network error fetching`` (timeout / reset / DNS),
    ``storage error fetching`` (the object store behind the url refused the
    read) and ``HTTP <status>``. A bare ``network error`` is always
    transient. Among HTTP statuses, 5xx plus 408 / 429 / 403 are transient
    (the Cloudflare-fronted suppliers intermittently answer an otherwise
    healthy resource with a 403 anti-bot challenge or a 429 that succeeds
    on retry); 404 / 410 mean the card was renamed or withdrawn and must
    fail fast.
    """
    if message.startswith("network error fetching"):
        return True
    if message.startswith("storage error fetching"):
        return True
    if message.startswith("HTTP "):
        head = message[len("HTTP ") :].split(None, 1)[0]
        if head.isdigit():
            status = int(head)
            return status >= 500 or status in (403, 408, 429)
    return False


def error_text(err: BaseException) -> str:
    """The exception's message, or its class name when it carries none.

    aiohttp raises its timeouts argless, and ``str()`` of an argless
    exception is ``""``. Interpolated into a message that ends in ``": "``
    that produced a user-facing sentence trailing off after the colon, on
    all three surfaces that show ``last_error``: the ``snapshot_stale``
    Repairs card, the ``current_price`` sensor attribute, and diagnostics.
    Naming the class is the smallest thing that stays informative: the
    caller's own prefix already says what was being attempted.
    """
    return str(err) or type(err).__name__


# 64 MiB: far above any real tariff card, so it never trips on a legitimate
# one while bounding what a broken or hostile CDN can pull into the
# coordinator's memory in one fetch.
_MAX_PDF_BYTES = 64 * 1024 * 1024


async def _read_pdf_bytes(resp: aiohttp.ClientResponse, url: str) -> bytes:
    """Read a (PDF) response body, rejecting an endpoint that declares a
    Content-Length far larger than any real tariff card.

    Reading the whole body keeps the magic-byte / parse path simple; the
    guard only refuses payloads the server itself advertises as oversize
    (a streamed response with no Content-Length still reads normally,
    which is fine for the trusted supplier endpoints we fetch).
    """
    declared = resp.content_length
    if declared is not None and declared > _MAX_PDF_BYTES:
        raise ExtractorError(
            f"refusing PDF at {url}: declared {declared} bytes (limit {_MAX_PDF_BYTES})"
        )
    return await resp.read()


def is_pdf_payload(payload: bytes) -> bool:
    """Return True if the bytes look like a PDF.

    PDFs start with the magic bytes ``%PDF``. Some publishers prepend a
    UTF-8 BOM (3 bytes EF BB BF), as Luminus's pricelist API does, so the
    BOM is allowed as a one-time prefix.
    """
    return payload.startswith((b"%PDF", b"\xef\xbb\xbf%PDF"))


# An object store that refuses the read answers the proxy in front of it
# with its own XML error document, and the proxy passes that through as a
# 200. Azure Blob and S3 both shape it as a root <Error> carrying a <Code>.
_STORAGE_ERROR_RE = re.compile(
    rb"^(?:\xef\xbb\xbf)?\s*(?:<\?xml[^>]*\?>\s*)?<Error>\s*<Code>([^<]{1,64})</Code>",
    re.IGNORECASE,
)


def _storage_error_code(payload: bytes) -> str | None:
    """The error code if ``payload`` is an object-store error document.

    Luminus switched anonymous access off on the storage account behind
    ``api-next/get-pricelist``, which serves its gas cards too, on
    2026-08-10, and every card came back as a 248-byte
    ``PublicAccessNotPermitted`` document under a 200. Read as a plain
    non-PDF payload that is a permanent parse failure asking the user to
    report a layout change that had not happened. Nothing here could fix
    it, which is the definition of transient in this taxonomy.
    """
    match = _STORAGE_ERROR_RE.match(payload)
    if match is None:
        return None
    return match.group(1).decode("ascii", "replace").strip() or None


async def fetch_pdf_bytes(session: aiohttp.ClientSession, url: str, *, timeout: int = 30) -> bytes:
    """Download ``url`` and return its bytes once validated as a PDF.

    Shared by the three ``fetch_pdf_text*`` variants. Catches TimeoutError
    alongside ClientError: aiohttp's ClientTimeout fires
    asyncio.TimeoutError (== builtins.TimeoutError on 3.11+), which is NOT
    a ClientError subclass, so a slow supplier endpoint would otherwise
    bubble a bare TimeoutError out of discover/fetch and crash the
    live-check. The ``network error fetching`` prefix is load-bearing -
    :func:`is_transient_fetch_error` keys on it to decide whether to retry -
    so only this function and :func:`fetch_text` may write it.
    """
    try:
        async with session.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status >= 400:
                raise ExtractorError(f"HTTP {resp.status} fetching {url}")
            payload = await _read_pdf_bytes(resp, url)
    except (aiohttp.ClientError, TimeoutError) as err:
        raise ExtractorError(f"network error fetching {url}: {error_text(err)}") from err

    if not is_pdf_payload(payload):
        # An object store refusing the read is the one non-PDF payload no
        # code change can fix, so it gets its own prefix and lands on the
        # transient side of is_transient_fetch_error rather than asking
        # the user to report a layout change.
        code = _storage_error_code(payload)
        if code is not None:
            raise ExtractorError(f"storage error fetching {url}: {code}")
        # Some CDNs return 200 + text/html for a missing PDF (a 404
        # disguised as success, as TotalEnergies does for a card it does not
        # publish), and Engie's API serves valid ones as octet-stream, so
        # the magic bytes are more reliable than the Content-Type header.
        raise ExtractorError(f"expected a PDF at {url}, payload starts with {payload[:80]!r}")
    # Strip the BOM the validator above deliberately tolerates. Accepting it
    # there only keeps the download from being rejected; the bytes still have
    # to parse, and pdfplumber cannot read them: it fails a BOM-prefixed
    # file with "No /Root object! - Is this really a PDF?", which reads like a
    # corrupt card rather than three stray bytes. pypdf recovers on its own,
    # so the pdfplumber readers are the ones this protects.
    if payload.startswith(b"\xef\xbb\xbf"):
        payload = payload[3:]
    return payload


async def fetch_pdf_rendered(
    session: aiohttp.ClientSession,
    url: str,
    *,
    variant: str,
    timeout: int,
    render: Callable[[bytes], str],
) -> str:
    """Download ``url`` and extract its text, or serve both from the memo.

    The ``fetch_pdf_text*`` readers, and an extractor's own pdfplumber
    render, differ only in ``render``, so the memo lookup lives here once.
    Keyed by variant as well as URL: the same document read plain and read
    layout-preserving are different strings, and handing one back for the
    other would feed a parser a shape it has no regexes for.

    Extraction is offloaded to a worker thread: every variant is pure-Python
    parsing, and a multi-page tariff card would otherwise stall Home
    Assistant's event loop.
    """
    memo = _TEXT_MEMO.get()
    key = f"{variant}\0{url}"
    if memo is not None and key in memo:
        return memo[key]
    payload = await fetch_pdf_bytes(session, url, timeout=timeout)
    text = await render_pdf(variant, url, payload, render)
    if memo is not None:
        memo[key] = text
    return text


async def render_pdf(variant: str, url: str, payload: bytes, render: Callable[[bytes], str]) -> str:
    """Turn validated PDF bytes into text, through the render hook when one
    is installed and in a worker thread otherwise.

    The readers call it after their download. A provider that receives a
    card some other way calls it too, such as OCTA+'s archive, which hands
    the card over base64 inside a JSON answer: rendering those bytes
    directly would keep the card archiver, which listens on the hook, from
    ever seeing them. ``url`` is whatever names the card for that provider.
    """
    hook = _RENDER_HOOK.get()
    if hook is None:
        return await asyncio.to_thread(render, payload)
    return await hook(variant, url, payload, render)


async def fetch_pdf_text(session: aiohttp.ClientSession, url: str, *, timeout: int = 30) -> str:
    """Download ``url`` and return the concatenated extracted text."""
    return await fetch_pdf_rendered(
        session, url, variant="plain", timeout=timeout, render=extract_pdf_text
    )


# A tariff card that carries a text layer is never anywhere near this small:
# across the 152 gas cards collected while building this integration the least
# texty readable one holds 2049 characters (Sparki), while Ecofix's rasterized
# cards yield 60. Anything in between separates the two cleanly, and 600
# leaves a wide margin on both sides. Raising here only changes WHICH error the user is
# shown: a card with no text layer was already going to fail its parse.
MIN_TEXT_LAYER_CHARS = 600


def _require_text_layer(text: str, pages: int) -> None:
    """Raise :class:`CardNotReadableError` for an image-only PDF."""
    if pages and len(text.strip()) < MIN_TEXT_LAYER_CHARS:
        raise CardNotReadableError(
            f"card has no text layer: {len(text.strip())} characters across "
            f"{pages} page(s), so it is published as page images"
        )


def extract_pdf_text(payload: bytes) -> str:
    try:
        reader = pypdf.PdfReader(BytesIO(payload))
        pages = list(reader.pages)
        chunks: list[str] = []
        failures = 0
        for idx, page in enumerate(pages):
            text = page.extract_text()
            if text is None:
                # pypdf returns None when a page cannot be decoded (e.g.
                # an unsupported font). The caller would otherwise see a
                # corrupt snapshot with regex misses on whatever was on
                # that page; log so the failure is visible in HA logs.
                _LOGGER.warning("pypdf returned None for page %d/%d", idx + 1, len(pages))
                failures += 1
                continue
            chunks.append(text)
        if pages and failures == len(pages):
            raise ExtractorError("PDF parse error: every page failed to decode")
        text = "\n".join(chunks)
        _require_text_layer(text, len(pages))
        return text
    except ExtractorError:
        raise
    except Exception as err:
        raise ExtractorError(f"PDF parse error: {err}") from err


def pdfplumber_text(payload: bytes, kind: str, render: Callable[[Any], str]) -> str:
    """Open ``payload`` with pdfplumber, reconstruct text via ``render``,
    and rewrap failures uniformly.

    ``render`` receives the open pdfplumber document and returns the
    reconstructed text; ``kind`` only shapes the :class:`ExtractorError`
    message. A PDF with pages but no decodable
    text fails loud rather than returning "" and letting every downstream
    regex miss silently (only mandatory fields fail loud; nullable ones
    zero), matching the pypdf path's all-pages guard.
    """
    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(payload)) as pdf:
            text = render(pdf)
            # The text-layer check lives on both readers, or whether a card
            # counts as unreadable would depend on which reader its
            # extractor happens to use.
            _require_text_layer(text, len(pdf.pages))
            return text
    except ExtractorError:
        raise
    except Exception as err:
        raise ExtractorError(f"PDF {kind} parse error: {err}") from err


def word_rows(words: list[dict[str, Any]], tolerance: float = 3.0) -> list[list[dict[str, Any]]]:
    """pdfplumber ``words`` grouped by line, left to right: a word whose top
    is within ``tolerance`` points of a line's first word joins that line."""
    rows: list[list[dict[str, Any]]] = []
    for word in sorted(words, key=lambda w: float(w["top"])):
        if rows and float(word["top"]) - float(rows[-1][0]["top"]) <= tolerance:
            rows[-1].append(word)
        else:
            rows.append([word])
    return [sorted(row, key=lambda w: float(w["x0"])) for row in rows]


def word_centre(word: dict[str, Any]) -> float:
    """The horizontal centre of a pdfplumber word."""
    return (float(word["x0"]) + float(word["x1"])) / 2.0


def extract_pdf_text_layout(payload: bytes) -> str:
    """Extract PDF text via pdfplumber, preserving table layout.

    pdfplumber walks the character stream and reassembles rows from glyph
    coordinates, so each DSO row comes out as one line with its columns in
    order, where pypdf follows the content stream and can split a table.

    Pages are passed through ``dedupe_chars()`` first, which drops glyphs
    a publisher stacked twice at the same coordinates; read as they are,
    "5,09" comes out as "55,,09".
    """
    return pdfplumber_text(
        payload,
        "layout",
        lambda pdf: "\n".join((page.dedupe_chars().extract_text() or "") for page in pdf.pages),
    )


async def fetch_pdf_text_layout(
    session: aiohttp.ClientSession, url: str, *, timeout: int = 30
) -> str:
    """Layout-preserving variant of :func:`fetch_pdf_text`.

    Some CDNs return HTTP 200 with ``text/html`` for missing PDFs (404
    pages disguised as success). We treat those as fetch failures so the
    parser never tries to read a PDF that isn't.
    """
    return await fetch_pdf_rendered(
        session, url, variant="layout", timeout=timeout, render=extract_pdf_text_layout
    )


async def head_freshness_key(
    session: aiohttp.ClientSession,
    url: str,
    *,
    prefer: tuple[str, ...] = ("Last-Modified", "ETag"),
) -> str | None:
    """HEAD ``url`` and return the first present header from ``prefer``.

    Used as a cheap freshness probe by suppliers whose tariff cards live
    behind a CDN that honours ``If-Modified-Since`` / ``If-None-Match``.
    Returns ``None`` on any 4xx/5xx, network error, or when none of the
    preferred headers are populated; the coordinator treats ``None`` as
    "no signal" and falls back to its time-based TTL.

    A caller whose server flips ``Last-Modified`` on every CDN edge but
    keeps a stable ETag passes ``prefer`` the other way round.
    """
    try:
        async with session.head(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=10),
            allow_redirects=True,
        ) as resp:
            if resp.status >= 400:
                return None
            for key in prefer:
                value = resp.headers.get(key)
                if value:
                    return value
            return None
    except (aiohttp.ClientError, TimeoutError):
        # aiohttp's ClientTimeout fires asyncio.TimeoutError (==
        # builtins.TimeoutError on 3.11+), which is NOT a ClientError;
        # without this a slow HEAD would break the documented
        # None-on-failure contract and bubble out of the probe path.
        return None


def printed_vat_rate(text: str, *patterns: str | re.Pattern[str]) -> float | None:
    """The VAT rate a card states, as a fraction, or ``None`` where none of
    ``patterns`` matches.

    For a parser that records the rate on ``TaxOverlay.card_vat_rate``.
    Group 1 of the first pattern that matches is the percentage.
    """
    for pattern in patterns:
        match = re.search(pattern, text) if isinstance(pattern, str) else pattern.search(text)
        if match:
            return to_float(match.group(1)) / 100.0
    return None


# A caller that will read the same document many times in quick succession can
# ask fetch_text and the PDF readers to serve repeats from memory. Off by
# default: every existing caller wants a live read, and a global time-based
# cache would quietly hand a coordinator tick a stale page. This is opt-in,
# explicit, and scoped to the block that entered it.
_TEXT_MEMO: ContextVar[dict[str, str] | None] = ContextVar("_TEXT_MEMO", default=None)


@contextmanager
def memoise_text_fetches(store: dict[str, str]) -> Iterator[None]:
    """Serve repeat reads of one URL from ``store`` inside this block.

    Two kinds of repeat, both of them a sweep pricing several products of one
    supplier:

    Listing pages. A provider that resolves a per-supplier listing inside
    ``fetch()`` and then picks one product out of it would re-download the
    same page once per contract when a whole supplier is priced.

    Tariff cards. Where two products share one document (EBEM prints both
    its gas products on one card) the sweep would parse it twice, and the
    parse is the expensive half, not the download: pdfplumber takes tens of
    seconds on a large card on a Raspberry Pi against well under a second
    to fetch it.

    What is memoised is the EXTRACTED TEXT, not the bytes. It is the parse
    that is worth skipping, and a card's text is a few kB against a couple of
    MB of payload, so a whole sweep's worth stays small enough to hold.

    ``store`` is passed in rather than created here so a caller can share one
    memo across several tasks - an ``asyncio.Task`` copies the context at
    creation, which copies the reference and not the dict, so every candidate
    in a sweep sees what the first one fetched.

    Deliberately not a TTL cache inside the fetchers: the coordinator and the
    one-off quote both want a live read, and the failure mode of guessing a
    TTL for them is a stale card nobody asked for.
    """
    token = _TEXT_MEMO.set(store)
    try:
        yield
    finally:
        _TEXT_MEMO.reset(token)


# How a downloaded card becomes text, when someone other than the readers
# wants a say. The card archiver (scripts/archive_cards.py) downloads every
# card daily but keys the render on the bytes' hash, so a card that has not
# changed since it was last stored is neither rendered nor parsed again, and
# it keeps the bytes it has not seen before. None, the default everywhere in
# Home Assistant, renders in a worker thread as always.
RenderHook = Callable[[str, str, bytes, Callable[[bytes], str]], Awaitable[str]]
_RENDER_HOOK: ContextVar[RenderHook | None] = ContextVar("_RENDER_HOOK", default=None)


@contextmanager
def render_through(hook: RenderHook) -> Iterator[None]:
    """Route every PDF render inside this block through ``hook``.

    The hook receives the reader variant, the URL, the validated bytes and
    the renderer the reader would have used, and returns the text. Scoped
    to the block, like the text memo above, so nothing in the integration
    itself can end up on this path.
    """
    token = _RENDER_HOOK.set(hook)
    try:
        yield
    finally:
        _RENDER_HOOK.reset(token)


async def fetch_text(
    session: aiohttp.ClientSession,
    url: str,
    *,
    params: dict[str, str] | None = None,
    timeout: int = 20,
) -> str:
    """GET ``url`` and return the response body as text.

    Raises :class:`ExtractorError` on any HTTP non-2xx, network error,
    or aiohttp client failure. Use for HTML listing / index pages and
    other plain-text sources; reach for :func:`fetch_pdf_text` (or its
    layout variant) when the body is expected to be a PDF.

    ``params`` is passed straight to :meth:`aiohttp.ClientSession.get`
    for endpoints that carry their query in the URL string (a CMS query,
    an API's filters).

    Callers that prefer a soft None-on-failure can wrap this in a
    ``try / except ExtractorError`` block; concentrating the network /
    HTTP error handling here keeps the ~6 lines of boilerplate out of
    every provider, and routes every fetch through the one
    :func:`is_transient_fetch_error` taxonomy so transient failures
    retry uniformly.
    """
    memo = _TEXT_MEMO.get()
    # Keyed on the full request, not the bare URL: one endpoint answers
    # different questions by query string.
    memo_key = url if not params else f"{url}?{sorted(params.items())}"
    if memo is not None and memo_key in memo:
        return memo[memo_key]
    try:
        async with session.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status >= 400:
                raise ExtractorError(f"HTTP {resp.status} fetching {url}")
            # Not strict: a page in another charset than it declares (a
            # maintenance page in Latin-1) is then refused by the parser as
            # an ExtractorError rather than raised as a UnicodeDecodeError.
            body = await resp.text(errors="replace")
            # Only a success is memoised. A failure is re-attempted by the
            # next caller, which is what the negative cache one layer up is
            # for; caching it here would give it a second, untracked lifetime.
            if memo is not None:
                memo[memo_key] = body
            return body
    except (aiohttp.ClientError, TimeoutError) as err:
        raise ExtractorError(f"network error fetching {url}: {error_text(err)}") from err


def parse_json(body: str, what: str) -> Any:
    """``body`` decoded, or an :class:`ExtractorError` naming ``what``. Its
    shape is the caller's to check."""
    try:
        return json.loads(body)
    except ValueError as err:
        raise ExtractorError(f"{what} is not JSON: {err}") from err


# Full month names in calendar order (index 0 == January). The single
# source of truth for the per-supplier archive-validity checks, which
# match a card's spelled-out month against ``month_names[month - 1]``.
# Suppliers import the tuple for their card's language rather than
# re-listing the twelve names (and drifting on accents); dict-shaped
# lookups derive from these with ``enumerate(.., 1)``.
NL_MONTHS: tuple[str, ...] = (
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
)


# Month names as cards print them, lowercase, to their number: Dutch, French
# with and without its accents, and the English names that differ from both.
MONTH_NAMES: dict[str, int] = {
    **{name: number for number, name in enumerate(NL_MONTHS, 1)},
    "janvier": 1,
    "fevrier": 2,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
    "décembre": 12,
    # April, September, November and December are spelt as in Dutch.
    "january": 1,
    "february": 2,
    "march": 3,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "october": 10,
}
