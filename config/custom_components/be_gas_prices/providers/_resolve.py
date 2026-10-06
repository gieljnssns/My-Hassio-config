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

"""Turning a published card into what one household is billed on.

A card prints a table; a household sits in one row of it. The distribution
tier and the excise slices follow the annual volume, the Brussels levy the
meter caliber, and the levies the law sets the delivery month, whatever month
the card itself was printed for.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from ..const import (
    CALIBER_Q10,
    ENERGY_CONTRIBUTION_ZEROED_FROM,
    FLUVIUS_DATA_MANAGEMENT_HTVA,
    FLUVIUS_DATA_MANAGEMENT_KNOWN_FROM,
    FLUVIUS_DATA_MANAGEMENT_KNOWN_UNTIL,
    FLUVIUS_KEYS,
    GAS_EXCISE_KNOWN_FROM,
    GAS_EXCISE_KNOWN_UNTIL,
    GAS_EXCISE_RESIDENTIAL_HTVA,
    OSP_Q10_HIGH,
    OSP_Q10_LOW,
    OSP_Q10_SPLIT_KWH,
    TIER_BOUNDS_KWH,
    VAT_RATE_REDUCED,
    WALLONIA_DSO_KEYS,
    WALLOON_CONNECTION_FEE,
    WALLOON_CONNECTION_FEE_KNOWN_FROM,
    WALLOON_CONNECTION_FEE_KNOWN_UNTIL,
)
from ._network import excise_bands
from .base import DsoOverlay, SupplierSnapshot, TaxOverlay


def tier_for(annual_kwh: float) -> str:
    """The distribution tier an annual volume falls in.

    The tier prices every kWh of the year, not a slice of it. A volume above
    the last bound is kept in the last tier a card can price: a connection
    that large is remotely read and on a tariff no residential card prints,
    so it is out of scope rather than billable.
    """
    for tier, bound in TIER_BOUNDS_KWH:
        if annual_kwh <= bound:
            return tier
    return TIER_BOUNDS_KWH[-1][0]


def effective_excise(bands: tuple[tuple[float | None, float], ...], annual_kwh: float) -> float:
    """The excise per kWh a household pays over the year, in EUR/kWh.

    The special excise is billed per slice of the annual volume: the first
    12 000 kWh at the lower rate and only the rest at the higher one. The
    blend is what one kWh costs on average at that volume, which lets the
    pricing engine keep reading a single rate. A volume of zero or less has
    no slices to blend and pays the first band's rate.
    """
    if annual_kwh <= 0:
        return bands[0][1]
    total = 0.0
    lower = 0.0
    for upper, rate in bands:
        top = annual_kwh if upper is None else min(annual_kwh, upper)
        if top > lower:
            total += (top - lower) * rate
        if upper is None or annual_kwh <= upper:
            break
        lower = upper
    return total / annual_kwh


def _in_window(delivery: date, start: tuple[int, int], end: tuple[int, int] | None) -> bool:
    month = (delivery.year, delivery.month)
    return month >= start and (end is None or month < end)


def resolve_federal_levies(taxes: TaxOverlay, delivery: date) -> TaxOverlay:
    """``taxes`` with the federal levies the law sets for ``delivery``.

    The special excise and the energy contribution are set by federal law
    for the whole country, so the delivery month decides them, not the month
    the card was printed in. Ecofix, Sparki, Belvus and the Energy Together
    brands still printed the pre-August excise on their September 2026 cards,
    and OCTA+ and TotalEnergies a pre-August energy contribution. Within the months the law is known
    for, the law's rate replaces the card's; outside them the card is read as
    printed.

    Only a residential card is touched: its values are VAT inclusive
    (``vat_rate`` 0.0), which is the basis the law's rate is put on. A
    professional card prints excluding VAT and is taxed on other rates.
    """
    if taxes.vat_rate != 0.0:
        return taxes
    resolved = taxes
    if _in_window(delivery, GAS_EXCISE_KNOWN_FROM, GAS_EXCISE_KNOWN_UNTIL):
        low, high = GAS_EXCISE_RESIDENTIAL_HTVA
        resolved = replace(
            resolved,
            excise_bands=excise_bands(low * (1 + VAT_RATE_REDUCED), high * (1 + VAT_RATE_REDUCED)),
        )
    if _in_window(delivery, ENERGY_CONTRIBUTION_ZEROED_FROM, None):
        resolved = replace(resolved, energy_contribution=0.0)
    return resolved


def resolve_network(
    dsos: dict[str, DsoOverlay], taxes: TaxOverlay, delivery: date
) -> dict[str, DsoOverlay]:
    """``dsos`` with the Fluvius data management fee where a card omits it.

    Only within the tariff year the regulated figure is known for, and only
    on a residential card, whose figures are VAT inclusive.
    """
    if taxes.vat_rate != 0.0 or not _in_window(
        delivery, FLUVIUS_DATA_MANAGEMENT_KNOWN_FROM, FLUVIUS_DATA_MANAGEMENT_KNOWN_UNTIL
    ):
        return dsos
    fee = FLUVIUS_DATA_MANAGEMENT_HTVA * (1 + VAT_RATE_REDUCED)
    return {
        key: replace(overlay, metering_per_year=fee)
        if key in FLUVIUS_KEYS and overlay.metering_per_year == 0.0
        else overlay
        for key, overlay in dsos.items()
    }


def resolve_connection_fee(
    taxes: TaxOverlay, dsos: dict[str, DsoOverlay], delivery: date
) -> TaxOverlay:
    """``taxes`` with the Walloon connection fee the law sets for
    ``delivery``, on a residential card of the Walloon DSOs.

    EnergyVision's September 2026 Walloon cards print the electricity rate,
    ten times the gas one. Outside the months the law is known for, and on
    any other card, the card is read as printed.
    """
    if (
        taxes.vat_rate != 0.0
        or not WALLONIA_DSO_KEYS & dsos.keys()
        or not _in_window(
            delivery, WALLOON_CONNECTION_FEE_KNOWN_FROM, WALLOON_CONNECTION_FEE_KNOWN_UNTIL
        )
    ):
        return taxes
    return replace(taxes, connection_fee=WALLOON_CONNECTION_FEE)


def resolve_for_delivery(snapshot: SupplierSnapshot, delivery: date) -> SupplierSnapshot:
    """``snapshot`` as it bills a month delivered on ``delivery``: the levies
    the law sets for that month and the regulated network figures a card
    leaves out."""
    taxes = resolve_federal_levies(snapshot.taxes, delivery)
    return replace(
        snapshot,
        dsos=resolve_network(snapshot.dsos, snapshot.taxes, delivery),
        taxes=resolve_connection_fee(taxes, snapshot.dsos, delivery),
    )


def brussels_levy(osp: dict[str, float] | None, caliber: str, annual_kwh: float) -> float | None:
    """The Brussels per-meter levy for a meter caliber, in EUR/year.

    The smallest caliber pays one of two amounts by whether the standardised
    annual consumption is above 5 000 kWh. 0.0 outside Brussels, where the
    card carries no table; None for a caliber the card's table does not
    print, which the card cannot price rather than one that pays nothing.
    """
    if osp is None:
        return 0.0
    if caliber == CALIBER_Q10:
        key = OSP_Q10_LOW if annual_kwh <= OSP_Q10_SPLIT_KWH else OSP_Q10_HIGH
        return osp.get(key)
    return osp.get(caliber)
