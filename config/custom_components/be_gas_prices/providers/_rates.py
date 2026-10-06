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

"""The shapes a gas tariff card can print.

One dataclass per kind of energy leg, and the union the rest of the
integration dispatches on. Data only: what a card says, converted to EUR/kWh.
Nothing here decides a price, applies a tax or reads a household's settings,
which is what keeps every extractor free to build one without pulling in the
pricing engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..const import REGIONS

# How the energy price of a contract is set:
#
#   fixed     one price for the whole contract term.
#   variable  the card states the price for its own month and no formula
#             this integration can re-price.
#   indexed   factor x index + base, where the index belongs to the delivery
#             period (a month, or a quarter) and is only published once that
#             period is known. The card's printed price is an estimate until
#             then, unless the index is set before delivery (``settled``).
TariffKind = Literal["fixed", "variable", "indexed"]

# The period an index value covers.
IndexPeriod = Literal["month", "quarter"]

ALL_REGIONS: frozenset[str] = frozenset(REGIONS)


@dataclass(frozen=True, kw_only=True)
class Contract:
    """One product sold by a supplier."""

    id: str
    label: str
    kind: TariffKind
    # Regions the product is actually published in. Defaults to all three;
    # extractors narrow it for products that are not sold everywhere.
    regions: frozenset[str] = field(default_factory=lambda: ALL_REGIONS)
    # True when the supplier sells this product to businesses: its card is
    # printed excluding VAT, so the comparisons leave it out. No contract
    # offered here is one.
    professional: bool = False


@dataclass(frozen=True, kw_only=True)
class FixedRates:
    """A fixed price: EUR/kWh for the contract term."""

    price: float
    yearly_fixed_fee: float = 0.0


@dataclass(frozen=True, kw_only=True)
class VariableRates:
    """The price the card states for its own month, with no formula to
    re-price it on. ``formula`` is the card's own wording, for diagnostics."""

    price: float
    yearly_fixed_fee: float = 0.0
    formula: str | None = None


@dataclass(frozen=True, kw_only=True)
class IndexedRates:
    """``factor x index + base`` in EUR/kWh, with the index in EUR/MWh.

    ``index`` is the name of the index as the supplier publishes it (Engie's
    "ZTPDAM", OCTA+'s "ZTP RLP M"), because two suppliers naming the same
    market rarely publish the same figure: ICIS Heren, EEX and Argus each
    assess it, and an RLP weighting moves it again. A price is only ever
    resolved against the values its own supplier publishes.

    ``price`` is what the card prints for its month. For an index known only
    after delivery that is an estimate, and the card's figure at the last
    known index is preferred over a forward forecast where it prints both,
    because it is a fact rather than a projection. ``settled`` is True where
    the index is fixed before the delivery month starts (a month-ahead
    average such as Engie's ZTP101), so the printed price is the billed one.
    """

    factor: float
    base: float
    index: str
    price: float
    yearly_fixed_fee: float = 0.0
    formula: str | None = None
    settled: bool = False
    period: IndexPeriod = "month"

    def at(self, index_value: float) -> float:
        """The price in EUR/kWh at ``index_value`` EUR/MWh."""
        return self.factor * index_value + self.base


EnergyRates = FixedRates | VariableRates | IndexedRates
