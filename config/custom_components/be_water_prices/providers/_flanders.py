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

"""Shared builder for Flemish operators publishing the integrale waterprijs.

Flanders has a uniform tariff layout: VMM-mandated 50/30/20 vastrecht and
10/6/4 per-resident korting (totals carried as
:data:`const.FLANDERS_VASTRECHT_TOTAL` /
:data:`const.FLANDERS_KORTING_TOTAL_PER_PERSON`), a basis + comfort water
rate, and per-commune saneringsbijdragen (gemeentelijk + bovengemeentelijk).

Operators that publish only an integrated drinkwater rate (Aquaduin)
leave the sanering arguments at their default of ``0.0``.

De Watergroep's news-article fallback path uses a different vastrecht
constant (drinkwater-leg only) and is not built through this helper.
"""

from __future__ import annotations

from datetime import date

from ..const import (
    DEFAULT_VAT_RATE,
    FLANDERS_KORTING_TOTAL_PER_PERSON,
    FLANDERS_VASTRECHT_TOTAL,
    REGION_FLANDERS,
)
from .base import ExtractorError, WaterTariff

# What a Flemish drinkwater rate can plausibly be, in EUR/m3 ex-VAT. The
# seven operators sit between 1.67 (Water-link) and 5.99 (Aquaduin, which
# folds its sanering into the basis), so this is wide enough to hold a
# decade of indexation and narrow enough to catch a decimal that moved or
# a cell read from the wrong column. The same window already existed for
# the Walloon CVD, and in scripts/live_check.py for every region, but the
# live check runs in CI once a day and this runs in the user's own Home
# Assistant on every fetch.
_MIN_PLAUSIBLE_RATE = 0.5
_MAX_PLAUSIBLE_RATE = 20.0


def build_flanders_tariff(
    *,
    utility_id: str,
    year: int,
    publication_label: str,
    source_url: str,
    basis: float,
    comfort: float,
    sanering_gemeentelijk: float = 0.0,
    sanering_bovengemeentelijk: float = 0.0,
) -> WaterTariff:
    """Build a Flemish :class:`WaterTariff` with the standard VMM totals.

    A rate of zero or less is not a rate: the 2x check passed 0 against
    0 and a card of nothing went to the sensors. Nor is a rate outside
    the plausibility window: a comfort rate that is exactly twice its
    basis satisfies the VMM identity whether both are right or both are
    a decimal place out. A sanering component of zero is legitimate
    (Aquaduin folds it into the basis, and a commune can levy none), a
    negative one is not.
    """
    if basis <= 0 or comfort <= 0:
        raise ExtractorError(
            f"{utility_id} {year}: drinkwater rate {basis} / {comfort} is not a price"
        )
    for rate, label in ((basis, "basis"), (comfort, "comfort")):
        if not _MIN_PLAUSIBLE_RATE <= rate <= _MAX_PLAUSIBLE_RATE:
            raise ExtractorError(
                f"{utility_id} {year}: {label} rate {rate} is outside "
                f"[{_MIN_PLAUSIBLE_RATE}, {_MAX_PLAUSIBLE_RATE}] EUR/m3"
            )
    if sanering_gemeentelijk < 0 or sanering_bovengemeentelijk < 0:
        raise ExtractorError(
            f"{utility_id} {year}: negative sanering {sanering_gemeentelijk} / "
            f"{sanering_bovengemeentelijk}"
        )
    return WaterTariff(
        utility=utility_id,
        region=REGION_FLANDERS,
        valid_from=date(year, 1, 1),
        valid_until=date(year, 12, 31),
        publication_label=publication_label,
        source_url=source_url,
        yearly_fixed_fee=FLANDERS_VASTRECHT_TOTAL,
        yearly_fixed_fee_per_resident_discount=FLANDERS_KORTING_TOTAL_PER_PERSON,
        basis_eur_per_m3=basis,
        comfort_eur_per_m3=comfort,
        sanering_gemeentelijk_eur_per_m3=sanering_gemeentelijk,
        sanering_bovengemeentelijk_eur_per_m3=sanering_bovengemeentelijk,
        vat_rate=DEFAULT_VAT_RATE,
    )
