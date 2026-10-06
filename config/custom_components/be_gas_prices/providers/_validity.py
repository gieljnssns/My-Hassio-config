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

"""Which month a card is for.

Getting this wrong bills a month at another month's rates, so an archived
card is only taken for a month when it names that month itself.
"""

from __future__ import annotations

import calendar
from collections.abc import Awaitable
from datetime import date

from homeassistant.util import dt as dt_util

from ._pdf import is_transient_fetch_error
from .base import ExtractorError, SupplierSnapshot


def end_of_month(year: int, month: int) -> date:
    """The last calendar day of ``year``-``month`` as a :class:`date`."""
    return date(year, month, calendar.monthrange(year, month)[1])


def future_month(year_month: date) -> bool:
    """Whether ``year_month`` is ahead of today in Home Assistant's zone.

    On a UTC host the OS clock is still on the previous month for the first
    hours of the 1st in Brussels, so an archive keyed by calendar month asks
    Home Assistant, not the OS.
    """
    today = dt_util.now().date()
    return (year_month.year, year_month.month) > (today.year, today.month)


async def month_card(
    load: Awaitable[SupplierSnapshot | None], year_month: date
) -> SupplierSnapshot | None:
    """The card ``load`` fetches, when it is the card for ``year_month``.

    A transient failure raises so the month cache retries it; any other
    failure is a month with no card, and so is a card naming another month.
    """
    try:
        snapshot = await load
    except ExtractorError as err:
        if is_transient_fetch_error(str(err)):
            raise
        return None
    if snapshot is None or snapshot.valid_until != end_of_month(year_month.year, year_month.month):
        return None
    return snapshot
