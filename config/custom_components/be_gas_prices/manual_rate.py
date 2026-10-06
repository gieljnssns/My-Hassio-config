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

"""The figures a household typed from its own contract.

A signing card is read from the supplier's or the project's archive, and when
neither reaches the month, or the offer had figures of its own, the household
can type them. They are laid over the energy leg the card gives, each on its
own: a fixed contract's price, an indexed contract's factor and base, and the
yearly fee. Typed excluding VAT the way formulas are printed, they are put on
the card's VAT-inclusive basis here.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .const import (
    CONF_MANUAL_BASE,
    CONF_MANUAL_FACTOR,
    CONF_MANUAL_FEE,
    CONF_MANUAL_PRICE,
    VAT_RATE_REDUCED,
)
from .providers._rates import EnergyRates, FixedRates, IndexedRates


def _number(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    return None if value is None or value == "" else float(value)


def manual_leg(leg: EnergyRates, data: dict[str, Any]) -> EnergyRates:
    """``leg`` with the typed figures of ``data`` in place of the card's."""
    vat = 1.0 + VAT_RATE_REDUCED
    price = _number(data, CONF_MANUAL_PRICE)
    factor = _number(data, CONF_MANUAL_FACTOR)
    base = _number(data, CONF_MANUAL_BASE)
    fee = _number(data, CONF_MANUAL_FEE)
    if isinstance(leg, FixedRates) and price is not None:
        leg = replace(leg, price=price / 100.0 * vat)
    elif isinstance(leg, IndexedRates):
        # Each figure on its own: a contract may differ from its card by its
        # base alone, and every field of the form is optional.
        if factor is not None:
            leg = replace(leg, factor=factor / 100.0 * vat)
        if base is not None:
            leg = replace(leg, base=base / 100.0 * vat)
    if fee is not None:
        leg = replace(leg, yearly_fixed_fee=fee)
    return leg
