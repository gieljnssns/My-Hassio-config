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

"""A month of gas billed the way a Belgian supplier bills it.

Pure functions over what the coordinator has gathered: which card prices the
month, which energy leg the household is on, the index value the month
settles at, the volume used and the days the month contributes. The running
costs, the projections and the price history are all sums of these.

The rules this encodes:

- The network and the levies of a month come from that month's own card
  where one is known, and the federal levies from the law for that delivery
  month (``_resolve.resolve_federal_levies``).
- The energy leg is the card of the month, or the card the household signed
  (the signing cohort) when the entry says so and the contract is fixed or
  indexed. A variable price is the supplier's for each month, so the card
  of the month sets it whatever the signing date. An indexed leg is priced
  at the index value of the delivery month once the supplier has published
  it, at the latest value it has published before then, and, where it
  publishes none, at the index the card of the month prices its own figure
  at.
- The distribution tier and the excise slices follow the household's annual
  volume, and the yearly fixed costs accrue by the day.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from .const import CONF_SUPPLIER, SUPPLIER_CUSTOM
from .manual_rate import manual_leg
from .pricing import PriceBreakdown, compute_breakdown, energy_price, fixed_costs
from .providers._rates import EnergyRates, IndexedRates, VariableRates
from .providers._resolve import resolve_for_delivery
from .providers.base import IndexTable, SupplierSnapshot


@dataclass(frozen=True)
class IndexValue:
    """The index value a month is priced at, and the month it belongs to.

    ``month`` differs from the month priced while the supplier has not yet
    published that month's value, which makes the price provisional.
    """

    value: float
    month: str


def month_key(day: date) -> str:
    return f"{day.year}-{day.month:02d}"


def index_for(table: IndexTable | None, index: str, month: str) -> IndexValue | None:
    """The value ``index`` settles at for ``month``, or the latest published
    before it, or None when the supplier has published none up to then."""
    values = (table or {}).get(index)
    if not values:
        return None
    if month in values:
        return IndexValue(values[month], month)
    earlier = [key for key in values if key < month]
    if not earlier:
        return None
    latest = max(earlier)
    return IndexValue(values[latest], latest)


def contract_leg(
    own: EnergyRates,
    signed: EnergyRates | None,
    table: IndexTable | None,
    data: dict[str, Any],
) -> EnergyRates:
    """The energy leg a month is billed on, from the card of the month
    (``own``), the signing card's leg where one is known and the figures
    the household typed (``data``).

    Where the supplier publishes no value of the index, a card prints only
    its own month's price. The index that price was set at is read back off
    the card of the month, and a signed or typed formula is priced at it,
    so the month moves with the market rather than holding the signing
    month's figure.

    The custom supplier's typed card is the contract itself: nothing is laid
    over it, not even signing figures an earlier version of the flow asked
    a custom entry for.
    """
    if data.get(CONF_SUPPLIER) == SUPPLIER_CUSTOM:
        return own
    leg = own if signed is None or isinstance(signed, VariableRates) else signed
    leg = manual_leg(leg, data)
    if (
        leg is not own
        and isinstance(leg, IndexedRates)
        and isinstance(own, IndexedRates)
        and own.index == leg.index
        and own.factor
        and not (table or {}).get(leg.index)
    ):
        # Priced off the card of the month, and settled only as that card is.
        leg = replace(leg, price=leg.at((own.price - own.base) / own.factor), settled=own.settled)
    return leg


def resolve_energy_price(
    energy: EnergyRates, table: IndexTable | None, month: str
) -> tuple[float, IndexValue | None]:
    """The energy price of ``month`` in EUR/kWh on the card's VAT basis, and
    the index value it was priced at (None for a price the card fixed)."""
    if not isinstance(energy, IndexedRates):
        return energy.price, None
    value = index_for(table, energy.index, month)
    return energy_price(energy, None if value is None else value.value), value


@dataclass(frozen=True)
class MonthBill:
    """One month's share of the bill, in EUR VAT inclusive."""

    month: str
    kwh: float
    days: int
    breakdown: PriceBreakdown
    energy_cost: float
    network_cost: float
    taxes_cost: float
    fixed_cost: float
    index: IndexValue | None
    # True while the energy price is not yet the one the month settles at:
    # an indexed leg priced at another month's value, settled or not, or at
    # the card's own estimate because the supplier publishes no value at all.
    provisional: bool

    @property
    def total(self) -> float:
        return self.energy_cost + self.network_cost + self.taxes_cost + self.fixed_cost


def bill_month(
    *,
    month: str,
    card: SupplierSnapshot,
    energy: EnergyRates,
    table: IndexTable | None,
    dso: str,
    annual_kwh: float,
    caliber: str,
    kwh: float,
    days: int,
    days_in_year: int,
) -> MonthBill:
    """Bill ``kwh`` used over ``days`` days of ``month``.

    ``card`` prices the network and the levies; ``energy`` is the leg the
    household is billed on, which is the card's own or the signing card's.
    The supplier's fixed fee follows the energy leg, since it is part of the
    offer the household signed.
    """
    year, number = (int(part) for part in month.split("-"))
    priced = replace(resolve_for_delivery(card, date(year, number, 1)), energy=energy)
    price, index = resolve_energy_price(energy, table, month)
    breakdown = compute_breakdown(priced, dso, annual_kwh, price)
    fixed = fixed_costs(priced, dso, annual_kwh, caliber).total * days / days_in_year
    return MonthBill(
        month=month,
        kwh=kwh,
        days=days,
        breakdown=breakdown,
        energy_cost=kwh * breakdown.energy,
        network_cost=kwh * breakdown.network,
        taxes_cost=kwh * breakdown.taxes,
        fixed_cost=fixed,
        index=index,
        provisional=isinstance(energy, IndexedRates)
        and (index.month != month if index is not None else not _settled_for(card, energy, month)),
    )


def _settled_for(card: SupplierSnapshot, energy: IndexedRates, month: str) -> bool:
    """Whether a leg priced with no index value at all is priced at what
    ``month`` settles at. Its price is then the card's, or a signed or typed
    formula read back off it (``contract_leg``): final only where the card
    is settled, on that index, and for its own month."""
    own = card.energy
    card_month = None if card.valid_until is None else f"{card.valid_until:%Y-%m}"
    return (
        isinstance(own, IndexedRates)
        and own.settled
        and own.index == energy.index
        and card_month == month
    )
