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

"""Shared helpers for fetching and reading PDF tariff cards.

Vendored subset of the sibling ``be_electricity_prices`` integration's
``providers/_pdf.py``: keeps only what water extractors need (sign /
formula parsing, hourly month resolution, layout-aligned PDF reading
are electricity-only).
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import unicodedata
import zlib
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from io import BytesIO
from urllib.parse import urlparse

import aiohttp

from ..const import INTEGRATION_VERSION
from .base import ExtractorError, TransientFetchError

_LOGGER = logging.getLogger(__name__)


def error_text(err: BaseException) -> str:
    """A message for ``err`` that is never empty.

    ``str()`` of an exception raised with no arguments is "", which
    leaves the surrounding message ending at its colon -- and that
    message reaches users through the last_error attribute and the
    stale-snapshot Repair card.
    """
    return str(err) or type(err).__name__


def _http_error(url: str, status: int) -> ExtractorError:
    """Map an HTTP status to the right error class.

    5xx (server error) and 429 (rate limited) are transient upstream
    conditions; 4xx (moved / forbidden / gone) usually means the page
    changed and is a real failure worth reporting. So is a 3xx that
    reaches the caller: one the client could not follow, or one it was
    told not to.
    """
    message = f"HTTP {status} fetching {url}"
    if status >= 500 or status == 429:
        return TransientFetchError(message)
    return ExtractorError(message)


USER_AGENT = f"Home Assistant be_water_prices/{INTEGRATION_VERSION}"

# Hard ceiling on a fetched response body. Real tariff PDFs and HTML
# pages are well under a megabyte; this only bounds memory if an upstream
# server -- or a MitM -- returns an arbitrarily large body.
MAX_RESPONSE_BYTES = 16 * 1024 * 1024


def _guard_content_length(resp: aiohttp.ClientResponse, url: str) -> None:
    """Reject a response whose declared length is over the cap."""
    length = resp.content_length
    if length is not None and length > MAX_RESPONSE_BYTES:
        raise ExtractorError(
            f"response from {url} declares {length} bytes, over the {MAX_RESPONSE_BYTES}-byte limit"
        )


async def _read_capped(resp: aiohttp.ClientResponse, url: str) -> bytes:
    """Read the body, refusing anything past ``MAX_RESPONSE_BYTES``.

    Content-Length is only a hint (absent on a chunked response, and a
    hostile server can lie), so the cap is also enforced on the bytes
    actually read.
    """
    _guard_content_length(resp, url)
    payload = bytearray()
    async for chunk in resp.content.iter_chunked(65536):
        payload.extend(chunk)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ExtractorError(f"response from {url} exceeded {MAX_RESPONSE_BYTES} bytes")
    return bytes(payload)


def _site(host: str) -> str:
    """The registrable part of ``host``: its last two labels."""
    return ".".join(host.lower().rstrip(".").split(".")[-2:])


def _guard_redirect(url: str, resp: aiohttp.ClientResponse) -> None:
    """Refuse a response that a redirect carried off the requested site.

    The PDF extractors validate the href they read off a page, but
    aiohttp follows 30x replies wherever they point, so a redirect from
    the validated URL reached any host or scheme, addresses only the
    Home Assistant host can see included, and the target's first bytes
    then landed in the last_error attribute. Staying on the requested
    site and never dropping from https are the two things the href
    checks exist for, so they hold for the final URL too.
    """
    if not resp.history:
        return
    requested = urlparse(url)
    final = resp.url
    # The message lands in last_error and the diagnostics dump, and the
    # target can be a LAN appliance or a captive portal: it goes to the
    # debug log only.
    if requested.scheme == "https" and final.scheme != "https":
        _LOGGER.debug("%s redirected to %s", url, final)
        raise ExtractorError(f"{url} redirected off https; refusing to read the answer")
    if _site(final.host or "") != _site(requested.hostname or ""):
        _LOGGER.debug("%s redirected to %s", url, final)
        raise ExtractorError(f"{url} redirected off-site; refusing to read the answer")


async def _read_text_capped(resp: aiohttp.ClientResponse, url: str) -> str:
    """Read a text body under the size cap, decoding leniently.

    Streams via :func:`_read_capped` so a chunked or Content-Length-less
    body cannot blow past the cap (``resp.text()`` reads unbounded), and
    decodes with the declared charset, falling back to UTF-8 with
    ``errors="replace"`` so a charset-mislabelled page yields a parseable
    string instead of raising an uncaught ``UnicodeDecodeError``.
    """
    payload = await _read_capped(resp, url)
    charset = resp.charset or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, UnicodeError):
        # An unknown charset label (a typo, or a vendor token like
        # "utf8mb4") raises LookupError before decoding, and a codec that
        # exists but has no "replace" handler (idna is one) raises
        # UnicodeError on the first non-ASCII byte. Neither is a page we
        # cannot read: fall back to UTF-8, mirroring aiohttp's get_encoding.
        return payload.decode("utf-8", errors="replace")


_UTF8_BOM = b"\xef\xbb\xbf"


def _strip_bom(payload: bytes) -> bytes:
    """Drop a leading UTF-8 BOM, or blank line, in front of %PDF.

    pdfplumber looks for %PDF at byte zero, so the BOM has
    to come off rather than merely be tolerated: accepting it and then
    handing the reader bytes it cannot open turned a clear "this is not
    a PDF" into an empty extraction with no error at all. A newline
    ahead of the signature, which some servers emit, is the same case.
    """
    if payload.startswith(_UTF8_BOM):
        payload = payload[len(_UTF8_BOM) :]
    return payload.lstrip(b"\r\n\t ")


def _is_pdf_payload(payload: bytes) -> bool:
    """Return True if the bytes look like a PDF.

    PDFs start with ``%PDF``; some publishers prepend a UTF-8 BOM.
    """
    return _strip_bom(payload).startswith(b"%PDF")


# What the streams inside one PDF may inflate to, in total. The three
# tariff cards on file inflate to under a megabyte; a card that needs more
# than this is not a tariff card.
MAX_INFLATED_BYTES = 64 * 1024 * 1024
# pdfminer starts a stream's data after the line the keyword is on: it
# reads to the first CR or LF, whatever else the line holds, and a CR
# followed by LF counts once. "endstream" is not a stream.
_STREAM_RE = re.compile(rb"(?<!end)stream")
_EOL_RE = re.compile(rb"\r\n|\r|\n")
_OBJ_HEADER_RE = re.compile(rb"(?<![0-9])[0-9]+[ \t\r\n]+[0-9]+[ \t\r\n]+\Z")
_FILTER_RE = re.compile(rb"/Filter\s*(\[[^\]]*\]|/[A-Za-z0-9]+|[0-9]+\s+[0-9]+\s+R)")
_PLAIN_FILTERS = frozenset({b"/FlateDecode", b"/DCTDecode"})
_HEAD_BYTES = 4096
_INFLATE_CHUNK = 65536


def _inflated_size(data: memoryview, budget: int) -> tuple[int, int]:
    """Inflate the deflate stream at the start of ``data``.

    Returns the bytes produced and the bytes consumed, stopping once the
    output passes ``budget``, the stream reaches its own end, or the
    bytes stop being deflate (pdfminer keeps what a corrupt stream
    yielded before the error, so that much counts too). The data is fed
    in chunks: handed the whole tail at once, the decompressor copies
    everything past the stream's end into its unconsumed tail, which is
    the rest of the file for every stream.
    """
    if len(data) < 2 or data[0] & 0x0F != 8 or (data[0] << 8 | data[1]) % 31:
        # Not a zlib header, so pdfminer would not inflate it either;
        # cheaper than raising through the decompressor.
        return 0, 0
    inflater = zlib.decompressobj()
    produced = consumed = 0
    for start in range(0, len(data), _INFLATE_CHUNK):
        chunk: bytes | memoryview = data[start : start + _INFLATE_CHUNK]
        while chunk:
            try:
                out = inflater.decompress(chunk, budget - produced + 1)
            except zlib.error:
                return produced, consumed
            produced += len(out)
            consumed += len(chunk) - len(inflater.unconsumed_tail) - len(inflater.unused_data)
            if produced > budget or inflater.eof:
                return produced, consumed
            chunk = inflater.unconsumed_tail
    return produced, consumed


def _object_start(payload: bytes, low: int, high: int) -> int:
    """Where the last "N G obj" header between ``low`` and ``high`` starts, else ``low``."""
    position = payload.rfind(b"obj", low, high)
    while position >= 0:
        header = _OBJ_HEADER_RE.search(payload, max(low, position - 40), position)
        if header is not None:
            return header.start()
        position = payload.rfind(b"obj", low, position)
    return low


def guard_pdf_streams(payload: bytes) -> None:
    """Refuse a PDF whose streams would inflate past the budget.

    The byte cap bounds what comes off the wire, not what pdfminer
    inflates: a FlateDecode stream of whitespace compresses about a
    thousand to one, so a hundred kilobytes on the wire became a hundred
    megabytes in memory, and the cap left room for tens of gigabytes,
    which is an OOM kill of the whole process rather than an error. Each
    stream is inflated here with a bounded decompressor and the total held
    to :data:`MAX_INFLATED_BYTES`. The stream's own end marks where the
    count stops, never the "endstream" keyword: stored deflate blocks
    carry any bytes verbatim, so a stream can spell "endstream" long
    before it is done. A filter chain, a filter held in another object,
    or a filter other than Flate and JPEG, is refused as well: a doubly
    deflated or ASCII85-wrapped stream is invisible to this pass, and no
    tariff card has used one.

    The pass is linear in the file: a keyword inside a stream's data is
    tried as a stream start and stops at the first byte that is not
    deflate, and the bytes fed to the decompressor over the whole pass may
    not exceed the file by more than a chunk, which is what any set of
    streams that do not overlap consumes.
    """
    view = memoryview(payload)
    inflated = consumed = previous_end = 0
    eol: re.Match[bytes] | None = None
    for match in _STREAM_RE.finditer(payload):
        # The data starts after the keyword's line. The line end is looked
        # up once per line, not once per keyword, so a line full of
        # keywords costs one scan; a keyword with no line end after it
        # reads no data in pdfminer, nor does any keyword behind it.
        if eol is None or eol.start() < match.end():
            eol = _EOL_RE.search(payload, match.end())
            if eol is None:
                break
        # The stream's dictionary sits between its "N G obj" and "stream",
        # after the previous keyword since streams do not nest.
        head_start = max(previous_end, match.start() - _HEAD_BYTES)
        previous_end = match.end()
        head = payload[_object_start(payload, head_start, match.start()) : match.start()]
        filters = _FILTER_RE.findall(head)
        if filters:
            spec = filters[-1]
            if spec.startswith(b"["):
                raise ExtractorError("PDF stream uses a filter chain, which cannot be bounded")
            if spec.endswith(b"R"):
                raise ExtractorError(
                    "PDF stream names its filter by reference; refusing to read it"
                )
            if spec not in _PLAIN_FILTERS:
                raise ExtractorError(
                    f"PDF stream uses the {spec.decode('ascii', 'replace')} filter"
                )
        produced, used = _inflated_size(view[eol.end() :], MAX_INFLATED_BYTES - inflated)
        inflated += produced
        consumed += used
        if inflated > MAX_INFLATED_BYTES:
            raise ExtractorError(
                f"PDF streams inflate past {MAX_INFLATED_BYTES} bytes; refusing to read it"
            )
        if consumed > len(payload) + _INFLATE_CHUNK:
            raise ExtractorError("PDF streams overlap; refusing to read it")


def extract_pdf_text_layout(payload: bytes) -> str:
    """Extract PDF text via pdfplumber, preserving table layout."""
    payload = _strip_bom(payload)
    guard_pdf_streams(payload)
    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(payload)) as pdf:
            text = "\n".join((page.dedupe_chars().extract_text() or "") for page in pdf.pages)
    except Exception as err:
        raise ExtractorError(f"PDF layout parse error: {error_text(err)}") from err
    if not text.strip():
        # A PDF with no text layer, or none we can reach. Returning ""
        # sends the parser off to fail on a missing row, which points
        # the maintainer at the regex rather than at the document.
        raise ExtractorError("PDF carried no extractable text layer")
    return text


# A memo of fetched texts, keyed by URL for a page and by ``layout\0<url>``
# for a rendered PDF, that a caller can install around a block: the card
# archiver and the live check read every utility in one walk, and the
# archiver's replay serves a stored month's texts from it with no network.
# Off by default; the coordinator wants a live read on every tick.
_TEXT_MEMO: ContextVar[dict[str, str] | None] = ContextVar("_TEXT_MEMO", default=None)


@contextmanager
def memoise_text_fetches(store: dict[str, str]) -> Iterator[None]:
    """Serve repeat reads of one URL from ``store`` inside this block."""
    token = _TEXT_MEMO.set(store)
    try:
        yield
    finally:
        _TEXT_MEMO.reset(token)


async def memoised_text(key: str, fetch: Callable[[], Awaitable[str]]) -> str:
    """``fetch`` once per ``key`` inside memoise_text_fetches, every time
    outside it. The key is the URL for a page and ``layout\0<url>`` for a
    rendered PDF; a provider that asks one endpoint for several answers (a
    commune in a cookie, or in a form field) puts what it asked for in the
    key, since the URL alone would serve the first commune's answer to
    every other."""
    memo = _TEXT_MEMO.get()
    if memo is not None and key in memo:
        return memo[key]
    text = await fetch()
    if memo is not None:
        memo[key] = text
    return text


# How downloaded PDF bytes become text, when someone other than the reader
# wants a say. The card archiver keys the render on the bytes' hash, so a
# card that has not changed since it was stored is neither rendered nor
# parsed again, and it keeps the bytes it has not seen before. None, the
# default everywhere in Home Assistant, renders in a worker thread.
RenderHook = Callable[[str, str, bytes, Callable[[bytes], str]], Awaitable[str]]
_RENDER_HOOK: ContextVar[RenderHook | None] = ContextVar("_RENDER_HOOK", default=None)


@contextmanager
def render_through(hook: RenderHook) -> Iterator[None]:
    """Route every PDF render inside this block through ``hook``."""
    token = _RENDER_HOOK.set(hook)
    try:
        yield
    finally:
        _RENDER_HOOK.reset(token)


async def render_pdf(variant: str, url: str, payload: bytes, render: Callable[[bytes], str]) -> str:
    """Turn validated PDF bytes into text, through the render hook when one
    is installed and in a worker thread otherwise. A provider that receives
    a card some other way than through the reader must call this too, or
    the archiver never sees the bytes."""
    hook = _RENDER_HOOK.get()
    if hook is None:
        return await asyncio.to_thread(render, payload)
    return await hook(variant, url, payload, render)


async def fetch_pdf_text_layout(session: aiohttp.ClientSession, url: str) -> str:
    """Download ``url`` and return its text with the table layout kept."""

    async def read() -> str:
        try:
            async with session.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if not 200 <= resp.status < 300:
                    raise _http_error(url, resp.status)
                _guard_redirect(url, resp)
                content_type = resp.content_type
                payload = await _read_capped(resp, url)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise TransientFetchError(f"network error fetching {url}: {error_text(err)}") from err
        if not _is_pdf_payload(payload):
            # The content type, not the first bytes: whatever answered is not
            # the tariff card, and quoting it put a stranger's page into a
            # sensor attribute and the diagnostics dump.
            raise ExtractorError(f"the answer from {url} ({content_type}) has no PDF signature")
        return await render_pdf("layout", url, payload, extract_pdf_text_layout)

    return await memoised_text(f"layout\0{url}", read)


async def fetch_text(
    session: aiohttp.ClientSession,
    url: str,
    *,
    timeout: int = 20,
    verify_ssl: bool = True,
) -> str:
    """GET ``url`` and return the response body as text.

    ``verify_ssl=False`` skips TLS certificate verification for this
    request only; reserve it for utility servers whose hosts genuinely
    misconfigure their chain (e.g. inBW, where the GoDaddy intermediate
    is not sent by the server). The risk is bounded -- worst case is
    a MitM serving stale tariff numbers, no credentials are involved.
    """

    async def read() -> str:
        try:
            kwargs: dict[str, object] = {
                "headers": {"User-Agent": USER_AGENT},
                "timeout": aiohttp.ClientTimeout(total=timeout),
            }
            if not verify_ssl:
                kwargs["ssl"] = False
            async with session.get(url, **kwargs) as resp:  # type: ignore[arg-type]
                if not 200 <= resp.status < 300:
                    raise _http_error(url, resp.status)
                _guard_redirect(url, resp)
                return await _read_text_capped(resp, url)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise TransientFetchError(f"network error fetching {url}: {error_text(err)}") from err

    return await memoised_text(url, read)


_NUMERIC_SEPARATORS = (
    " ",
    " ",  # NBSP
    " ",  # THIN SPACE
    " ",  # NARROW NO-BREAK SPACE
    " ",  # LINE SEPARATOR
)


def fold_accents(text: str) -> str:
    """Lowercase and strip Latin diacritics."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c)
    )


# What a Dutch tariff card says it applies from: "Geldig vanaf 1 januari
# 2026" on Water-link's, "Overzicht tarieven per 1 januari 2026" on
# Aquaduin's. Both used to be dated from the file name or the page URL
# alone, so a link left pointing at an older card was served as this
# year's and never looked stale.
_CARD_YEAR_RE = re.compile(
    r"(?:geldig\s+vanaf|tarieven\s+per)\s+1\s+januari\s+(20\d\d)",
    re.IGNORECASE,
)


def stated_card_year(text: str) -> int | None:
    """The year a Dutch card states it applies from, if it states one."""
    match = _CARD_YEAR_RE.search(text)
    return int(match.group(1)) if match is not None else None


def to_float(text: str) -> float:
    """Parse a Belgian / French decimal number ('15,93' or '0.102').

    Strips every Unicode space variant Belgian publications use as a
    thousands separator or unit padder before swapping the comma for a
    decimal point.
    """
    cleaned = text.strip()
    for sep in _NUMERIC_SEPARATORS:
        cleaned = cleaned.replace(sep, "")
    value = float(cleaned.replace(",", "."))
    if not math.isfinite(value):
        # A run of a few hundred digits parses to infinity, which then
        # passes every ratio check (inf / inf is nan, and nan compares
        # false) and reaches sensors that refuse to publish it.
        raise ExtractorError(f"{text.strip()!r} is not a finite number")
    return value
