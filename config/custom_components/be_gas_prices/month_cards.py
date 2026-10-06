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

"""The card a past month was billed on.

A month is priced on the card published for it: the supplier's own archive
where it keeps one, then the project's card archive (be_price_cards, written
daily by the archive workflow), then nothing, which leaves the caller to
stand in the current card and say so. A closed month's answer never changes,
so it is kept for good, absent answers included for a day; a failure that
may recover is not kept at all.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Any, Literal

import aiohttp
from homeassistant.util import dt as dt_util

from .const import CARD_ARCHIVE_URL
from .providers._pdf import USER_AGENT, error_text, is_transient_fetch_error
from .providers.base import (
    CardNotReadableError,
    ExtractorError,
    SupplierExtractor,
    SupplierSnapshot,
)
from .snapshot_codec import SnapshotDecodeError, snapshot_from_json, snapshot_to_json

_LOGGER = logging.getLogger(__name__)

# How long a month nobody holds is remembered as absent before it is asked
# again: the archive can capture a month late, and a supplier can reissue.
_ABSENT_TTL = timedelta(days=1)

CardSource = Literal["supplier", "archive"]


@dataclass(frozen=True)
class MonthCard:
    """A month's card and where it came from, or an absent month."""

    snapshot: SupplierSnapshot | None
    source: CardSource | None
    fetched_at: datetime
    # Stored by another release, which may have read the card worse: read
    # again once, and kept when no card is found any more.
    reread: bool = False


class ArchiveUnavailable(Exception):
    """GitHub did not answer; the month may well be there."""


async def fetch_archived_card(
    session: aiohttp.ClientSession,
    supplier: str,
    contract: str,
    region: str,
    month: str,
) -> SupplierSnapshot | None:
    """The card archive's row for one month, or None where it holds none."""
    row = await fetch_archived_row(session, supplier, contract, region, month)
    return None if row is None else row[0]


async def fetch_archived_row(
    session: aiohttp.ClientSession,
    supplier: str,
    contract: str,
    region: str,
    month: str,
) -> tuple[SupplierSnapshot, bool] | None:
    """The card archive's row for one month and whether the archive read that
    card with its OCR engine, or None where it holds none."""
    url = f"{CARD_ARCHIVE_URL}/{supplier}/{contract}/{region}/{month}.json"
    try:
        async with session.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            if resp.status == 404:
                return None
            if resp.status >= 400:
                raise ArchiveUnavailable(f"HTTP {resp.status} fetching {url}")
            blob = await resp.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError) as err:
        raise ArchiveUnavailable(f"network error fetching {url}: {error_text(err)}") from err
    except ValueError as err:
        _LOGGER.warning("card archive row %s is not JSON: %s", url, err)
        return None
    try:
        snapshot = snapshot_from_json(blob)
    except SnapshotDecodeError as err:
        _LOGGER.debug("card archive row %s unreadable: %s", url, err)
        return None
    if (snapshot.supplier, snapshot.contract) != (supplier, contract):
        return None
    sources = blob.get("_sources") if isinstance(blob, dict) else None
    read_by_ocr = isinstance(sources, list) and any(
        isinstance(source, dict) and source.get("ocr") for source in sources
    )
    return snapshot, read_by_ocr


CurrentSource = Literal["live", "ocr", "archive"]


async def current_card(
    session: aiohttp.ClientSession,
    extractor: SupplierExtractor,
    contract: str,
    region: str,
    month: str,
    *,
    use_archive: bool,
) -> tuple[SupplierSnapshot, CurrentSource]:
    """The card a contract is priced on for ``month``, the running one, and
    where it came from.

    The supplier's own card where it can be read. A card published as page
    images leaves no reader here anything to read, and then the card
    archive's row for the month stands in: the archive reads such a card
    with an OCR engine every day and files the reading as an ordinary row,
    leaving out every line on which the engine refused a mark, so a figure
    in the row was read whole. Raises the fetch's error where there is no
    such row, or the entry keeps the archive out.

    A card put up before its month began (OCTA+'s, on the last day of the
    month before) is not yet in force: the running month's own card, from
    the supplier's archive, stands in where it has one. An archive that
    fails to answer raises, so the card is asked for again, rather than the
    month being priced on the next one's.
    """
    try:
        snapshot = await extractor.fetch(session, contract, region)
    except CardNotReadableError as err:
        if not use_archive:
            raise
        try:
            row = await fetch_archived_row(session, extractor.id, contract, region, month)
        except ArchiveUnavailable as unavailable:
            _LOGGER.debug("card archive unavailable: %s", unavailable)
            row = None
        if row is None:
            raise err from None
        snapshot, read_by_ocr = row
        return snapshot, "ocr" if read_by_ocr else "archive"
    valid_until = snapshot.valid_until
    if (
        extractor.fetch_for_month is not None
        and valid_until is not None
        and f"{valid_until:%Y-%m}" > month
    ):
        year, number = (int(part) for part in month.split("-"))
        try:
            running = await extractor.fetch_for_month(
                session, contract, region, date(year, number, 1)
            )
        except ExtractorError as err:
            if is_transient_fetch_error(str(err)):
                raise
            _LOGGER.debug("%s card for %s not read: %s", extractor.label, month, err)
            running = None
        # Only the running month's own card: a supplier archive answering
        # with another month's is no better than the card online.
        if (
            running is not None
            and running.valid_until is not None
            and f"{running.valid_until:%Y-%m}" == month
        ):
            return running, "live"
    return snapshot, "live"


class MonthCardCache:
    """Past months' cards for one entry, in memory and in its store."""

    def __init__(self) -> None:
        self._rows: dict[str, MonthCard] = {}

    @staticmethod
    def _key(supplier: str, contract: str, region: str, month: str) -> str:
        return f"{supplier}/{contract}/{region}/{month}"

    def get(self, supplier: str, contract: str, region: str, month: str) -> MonthCard | None:
        return self._rows.get(self._key(supplier, contract, region, month))

    async def card(
        self,
        session: aiohttp.ClientSession,
        extractor: SupplierExtractor,
        contract: str,
        region: str,
        month: str,
        *,
        use_archive: bool,
    ) -> MonthCard:
        """The card of a closed ``month``, fetched once and then kept.

        Raises ExtractorError or ArchiveUnavailable on a failure that may
        recover, so the caller prices the month on the current card for now
        and asks again on a later tick.
        """
        key = self._key(extractor.id, contract, region, month)
        now = dt_util.utcnow()
        held = self._rows.get(key)
        if (
            held is not None
            and not held.reread
            and (held.snapshot is not None or now - held.fetched_at < _ABSENT_TTL)
        ):
            return held
        year, number = (int(part) for part in month.split("-"))
        snapshot: SupplierSnapshot | None = None
        source: CardSource | None = None
        # A supplier archive that is down says nothing about the month: the
        # card archive may still hold it, and if it does not, the month is
        # asked again next tick rather than remembered as absent.
        unavailable: ExtractorError | None = None
        if extractor.fetch_for_month is not None:
            try:
                snapshot = await extractor.fetch_for_month(
                    session, contract, region, date(year, number, 1)
                )
            except ExtractorError as err:
                unavailable = err
            if snapshot is not None:
                source = "supplier"
        if snapshot is None and use_archive:
            snapshot = await fetch_archived_card(session, extractor.id, contract, region, month)
            if snapshot is not None:
                source = "archive"
        if snapshot is None and unavailable is not None:
            raise unavailable
        row = MonthCard(snapshot=snapshot, source=source, fetched_at=now)
        if snapshot is None and held is not None and held.snapshot is not None:
            # No card of the month to be found, which says nothing of the
            # stored one (a signing card no one serves any more): it stays.
            # A release that refuses a card it once misread drops it by
            # bumping the snapshot schema.
            row = replace(held, reread=False)
        self._rows[key] = row
        return row

    def to_json(self) -> dict[str, Any]:
        """The held cards for the entry's store; absent months are not kept
        across a restart, since asking again costs one request."""
        return {
            key: {
                "snapshot": snapshot_to_json(row.snapshot),
                "source": row.source,
                "fetched_at": row.fetched_at.isoformat(),
                "reread": row.reread,
            }
            for key, row in self._rows.items()
            if row.snapshot is not None
        }

    def load_json(self, blob: Any, *, reread: bool = False) -> None:
        """Restore what :meth:`to_json` wrote, dropping any row it cannot read.
        With ``reread`` (another release wrote it) each card is read again
        the next time it is asked for."""
        if not isinstance(blob, dict):
            return
        for key, value in blob.items():
            try:
                snapshot = snapshot_from_json(value["snapshot"])
                fetched_at = datetime.fromisoformat(value["fetched_at"])
                source = value["source"]
            except (SnapshotDecodeError, KeyError, TypeError, ValueError):
                continue
            if source not in ("supplier", "archive"):
                continue
            self._rows[str(key)] = MonthCard(
                snapshot=snapshot,
                source=source,
                fetched_at=fetched_at,
                # Still to be read again, from an update before a restart.
                reread=reread or value.get("reread") is True,
            )
