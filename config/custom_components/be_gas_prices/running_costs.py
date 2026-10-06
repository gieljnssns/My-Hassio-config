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

"""The running costs and projections, from the meter's days.

Pure over the inputs the coordinator gathers: the meter's consumption per
local day, the kWh one of its units is worth in each month, the card each
month is billed on, the index values and the household. Kept apart from the
coordinator so every figure the cost sensors publish can be checked without
Home Assistant.
"""

from __future__ import annotations

import calendar
import contextlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from .bill import MonthBill, bill_month, month_key
from .const import MEASURED_FULL_YEAR_DAYS, MEASURED_YEAR_GAP_DAYS
from .pricing import PricingError
from .providers._rates import EnergyRates
from .providers.base import IndexTable, SupplierSnapshot


@dataclass(frozen=True)
class Household:
    """What the bill needs to know about the connection."""

    dso: str
    caliber: str
    annual_kwh: float


@dataclass(frozen=True)
class RunningCosts:
    """The figures the cost and volume sensors publish."""

    months: tuple[MonthBill, ...]
    months_on_current_card: tuple[str, ...]
    ytd_kwh: float
    rolling_year_kwh: float | None
    projected_year_kwh: float | None
    projected_year_end_cost: float | None

    @property
    def current_year_cost(self) -> float:
        return sum(bill.total for bill in self.months)

    def month_cost(self, month: str) -> float | None:
        for bill in self.months:
            if bill.month == month:
                return bill.total
        return None


def days_in_year(year: int) -> int:
    return 366 if calendar.isleap(year) else 365


def to_kwh(
    days: Mapping[date, float], factor_for: Callable[[str], float | None], billed_from: date
) -> dict[date, float] | None:
    """The meter's days in kWh, converting each by its month's factor.

    ``factor_for`` returns the kWh one meter unit is worth in a month: 1.0
    for a meter that counts kWh already. None when a month from
    ``billed_from`` on that holds consumption has no factor at all, since a
    bill missing a month's gas is worse than no bill. A day before it only
    feeds the rolling year and the year-end projection, which take a
    missing day for what it is: one without a factor is left out, as a
    reception station Atrias lists only since a later month leaves it.
    """
    out: dict[date, float] = {}
    for day, value in days.items():
        if value == 0.0:
            out[day] = 0.0
            continue
        factor = factor_for(month_key(day))
        if factor is None:
            if day < billed_from:
                continue
            return None
        out[day] = value * factor
    return out


def meter_start(today: date) -> date:
    """The first day the costs read off the meter: today's date last year,
    before this year's 1 January, the rolling year and the days the year-end
    projection reads last year. A day before it has no use, so it is not
    read."""
    try:
        return today.replace(year=today.year - 1)
    except ValueError:  # 29 February has no twin
        return date(today.year - 1, 2, 28)


def rolling_year_kwh(days: Mapping[date, float], today: date) -> float | None:
    """What the meter recorded over the last 365 days, today included.

    Up to MEASURED_YEAR_GAP_DAYS missing days are scaled across; with more
    missing the window is not a year and the answer is None. Gas is too
    seasonal for a shorter window to be scaled to a year at all.
    """
    start = today - timedelta(days=MEASURED_FULL_YEAR_DAYS - 1)
    window = [value for day, value in days.items() if start <= day <= today]
    if len(window) < MEASURED_FULL_YEAR_DAYS - MEASURED_YEAR_GAP_DAYS:
        return None
    return sum(window) * MEASURED_FULL_YEAR_DAYS / len(window)


def months_between(start: date, end: date) -> list[str]:
    """Every month from ``start``'s to ``end``'s, as "YYYY-MM"."""
    months: list[str] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append(f"{year}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def _days_of(month: str, start: date, end: date) -> tuple[date, date]:
    year, number = (int(part) for part in month.split("-"))
    first = max(start, date(year, number, 1))
    last = min(end, date(year, number, calendar.monthrange(year, number)[1]))
    return first, last


def running_costs(
    *,
    kwh_days: Mapping[date, float],
    today: date,
    window_start: date,
    household: Household,
    current_card: SupplierSnapshot,
    month_card: Callable[[str], SupplierSnapshot | None],
    energy_for: Callable[[SupplierSnapshot], EnergyRates],
    table: IndexTable | None,
) -> RunningCosts:
    """Bill every month from ``window_start`` to ``today`` on its own card.

    ``month_card`` returns a closed month's card, or None where none could be
    read; that month is then billed on ``current_card`` and named in
    ``months_on_current_card``. ``energy_for`` picks the energy leg a card
    bills this household on: its own, or the signing card's.
    """
    year_days = days_in_year(today.year)
    bills: list[MonthBill] = []
    on_current: list[str] = []
    current_month = month_key(today)
    for month in months_between(window_start, today):
        first, last = _days_of(month, window_start, today)
        card = current_card if month == current_month else month_card(month)
        kwh = sum(value for day, value in kwh_days.items() if first <= day <= last)

        days = (last - first).days + 1

        def _bill(
            card: SupplierSnapshot, month: str = month, kwh: float = kwh, days: int = days
        ) -> MonthBill:
            return bill_month(
                month=month,
                card=card,
                energy=energy_for(card),
                table=table,
                dso=household.dso,
                annual_kwh=household.annual_kwh,
                caliber=household.caliber,
                kwh=kwh,
                days=days,
                days_in_year=year_days,
            )

        bill: MonthBill | None = None
        if card is not None:
            # A month's own card that cannot price this household (an archived
            # card missing its DSO row or tier) is no better than none.
            with contextlib.suppress(PricingError):
                bill = _bill(card)
        if bill is None:
            on_current.append(month)
            bill = _bill(current_card)
        bills.append(bill)
    ytd_kwh = sum(bill.kwh for bill in bills)
    remaining = _remaining_days_last_year(kwh_days, today)
    projected_kwh = None if remaining is None else ytd_kwh + remaining
    year_end = None
    if remaining is not None and bills:
        end_of_year = date(today.year, 12, 31)
        rest = bill_month(
            month=current_month,
            card=current_card,
            energy=energy_for(current_card),
            table=table,
            dso=household.dso,
            annual_kwh=household.annual_kwh,
            caliber=household.caliber,
            kwh=remaining,
            days=(end_of_year - today).days,
            days_in_year=year_days,
        )
        year_end = sum(bill.total for bill in bills) + rest.total
    return RunningCosts(
        months=tuple(bills),
        months_on_current_card=tuple(on_current),
        ytd_kwh=ytd_kwh,
        rolling_year_kwh=rolling_year_kwh(kwh_days, today),
        projected_year_kwh=projected_kwh,
        projected_year_end_cost=year_end,
    )


def _remaining_days_last_year(kwh_days: Mapping[date, float], today: date) -> float | None:
    """What the meter recorded last year from tomorrow's date to 31 December,
    the stand-in for what the rest of this year will use. None unless every
    one of those days is on record: a year-end figure built on a gap would
    read as a forecast it is not."""
    total = 0.0
    day = today + timedelta(days=1)
    end = date(today.year, 12, 31)
    while day <= end:
        try:
            last_year = day.replace(year=day.year - 1)
        except ValueError:  # 29 February has no twin
            day += timedelta(days=1)
            continue
        value = kwh_days.get(last_year)
        if value is None:
            return None
        total += value
        day += timedelta(days=1)
    return total
