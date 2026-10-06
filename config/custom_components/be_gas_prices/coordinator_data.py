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

"""The record every sensor reads, built once per coordinator tick."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from .bill import IndexValue, MonthBill
from .pricing import FixedCosts, PriceBreakdown
from .providers.base import SupplierSnapshot


@dataclass(frozen=True)
class Conversion:
    """What one cubic metre of this household's gas is worth in kWh.

    ``source`` is "station" (Atrias's calorific value of the chosen reception
    station), "manual" (the factor typed from the bill) or "none" when no
    factor is known. ``month`` is the month a station value was published
    for, which trails the running month.
    """

    factor: float | None
    source: str
    month: str | None = None


@dataclass(frozen=True)
class CoordinatorData:
    """Everything the entities publish, as of one tick."""

    snapshot: SupplierSnapshot | None
    # Where the card in hand came from: "live" (fetched from the supplier),
    # "cache" (restored from the entry's store), "archive" (a row of the card
    # archive, standing in while the supplier could not be read or reading a
    # card no reader here reads), "ocr" (the archive's OCR reading of a card
    # published as images).
    card_source: str
    breakdown: PriceBreakdown | None
    fixed: FixedCosts | None
    index: IndexValue | None
    price_provisional: bool
    conversion: Conversion
    tier: str | None
    annual_kwh: float
    annual_kwh_measured: bool
    snapshot_fetched_at: datetime | None
    snapshot_age_hours: float | None
    snapshot_stale: bool
    last_error: str
    # The day the record was built for. The cost sensors' last_reset follows
    # it, not the clock: a state written after midnight but before the next
    # tick still holds the day before's figures.
    day: date
    # Running costs, None until a gas meter is readable.
    current_year_cost: float | None = None
    current_month_cost: float | None = None
    ytd_kwh: float | None = None
    months: tuple[MonthBill, ...] = field(default_factory=tuple)
    # Months billed on the current card because their own could not be read.
    months_on_current_card: tuple[str, ...] = field(default_factory=tuple)
    rolling_year_kwh: float | None = None
    projected_year_cost: float | None = None
    projected_year_end_cost: float | None = None
    projected_year_kwh: float | None = None
    meter: str | None = None
    # Earlier contracts of the year that could not be priced, whose days are
    # missing from the running costs.
    unpriced_periods: tuple[str, ...] = field(default_factory=tuple)

    @property
    def price_m3(self) -> float | None:
        """The all-in price of one cubic metre, where a factor is known."""
        if self.breakdown is None or self.conversion.factor is None:
            return None
        return self.breakdown.all_in * self.conversion.factor
