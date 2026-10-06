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

"""The all-in gas price given a snapshot, a DSO and a household.

Pure functions, no Home Assistant imports, so every figure the sensors show
can be checked in a plain unit test.

A Belgian gas bill has two parts. Per kWh: the supplier's energy price, the
distribution tier's proportional term, transport, the federal special excise
and energy contribution, and in Wallonia the connection fee. Per year: the
supplier's fixed fee, the tier's fixed term, the metering fee and in Brussels
the per-meter levy. VAT applies to all of it except the Walloon connection fee.
"""

from __future__ import annotations

from dataclasses import dataclass

from .providers._rates import EnergyRates, IndexedRates
from .providers._resolve import brussels_levy, effective_excise, tier_for
from .providers.base import DsoOverlay, DsoTier, SupplierSnapshot, TaxOverlay


@dataclass(frozen=True)
class PriceBreakdown:
    """All-in EUR/kWh and its three parts, each VAT inclusive."""

    energy: float
    network: float
    taxes: float
    all_in: float


@dataclass(frozen=True)
class FixedCosts:
    """The yearly fixed part of the bill in EUR, VAT inclusive."""

    supplier: float
    distribution: float
    metering: float
    levy: float

    @property
    def total(self) -> float:
        return self.supplier + self.distribution + self.metering + self.levy


class PricingError(Exception):
    """The snapshot cannot price this household: its DSO or tier is missing."""


def energy_price(energy: EnergyRates, index_value: float | None) -> float:
    """The energy price in EUR/kWh on the card's VAT basis.

    An indexed leg is priced at ``index_value`` when one is known for the
    delivery period, and at the card's own figure otherwise. A fixed or
    variable leg ignores the index.
    """
    if isinstance(energy, IndexedRates) and index_value is not None:
        return energy.at(index_value)
    return energy.price


def _overlay(snapshot: SupplierSnapshot, dso: str) -> DsoOverlay:
    try:
        return snapshot.dsos[dso]
    except KeyError:
        raise PricingError(
            f"{snapshot.supplier} card has no {dso} tariff "
            f"(it lists {', '.join(sorted(snapshot.dsos)) or 'none'})"
        ) from None


def _tier(overlay: DsoOverlay, annual_kwh: float, dso: str) -> DsoTier:
    tier = tier_for(annual_kwh)
    try:
        return overlay.tiers[tier]
    except KeyError:
        raise PricingError(f"{dso} tariff has no {tier.upper()} on this card") from None


def _vat(taxes: TaxOverlay) -> float:
    return 1.0 + taxes.vat_rate


def compute_breakdown(
    snapshot: SupplierSnapshot,
    dso: str,
    annual_kwh: float,
    energy_eur_per_kwh: float,
) -> PriceBreakdown:
    """The all-in price of one kWh for a household.

    ``energy_eur_per_kwh`` is the supplier's price for the delivery period
    on the card's VAT basis, resolved by :func:`energy_price`. The tier and
    the excise blend follow ``annual_kwh``. Each part is VAT inclusive, so
    ``energy + network + taxes == all_in``; the Walloon connection fee is
    added at face value, since it carries no VAT.
    """
    overlay = _overlay(snapshot, dso)
    tier = _tier(overlay, annual_kwh, dso)
    taxes = snapshot.taxes
    vat = _vat(taxes)
    energy = energy_eur_per_kwh * vat
    network = (tier.proportional + overlay.transport) * vat
    levies = (effective_excise(taxes.excise_bands, annual_kwh) + taxes.energy_contribution) * vat
    levies += taxes.connection_fee
    return PriceBreakdown(
        energy=energy,
        network=network,
        taxes=levies,
        all_in=energy + network + levies,
    )


def fixed_costs(
    snapshot: SupplierSnapshot,
    dso: str,
    annual_kwh: float,
    caliber: str,
) -> FixedCosts:
    """The yearly fixed costs for a household, in EUR VAT inclusive."""
    overlay = _overlay(snapshot, dso)
    tier = _tier(overlay, annual_kwh, dso)
    vat = _vat(snapshot.taxes)
    levy = brussels_levy(snapshot.taxes.osp_by_caliber, caliber, annual_kwh)
    if levy is None:
        raise PricingError(f"{snapshot.supplier} card has no Brussels levy for a {caliber} meter")
    return FixedCosts(
        supplier=snapshot.energy.yearly_fixed_fee * vat,
        distribution=tier.fixed_per_year * vat,
        metering=overlay.metering_per_year * vat,
        levy=levy * vat,
    )
