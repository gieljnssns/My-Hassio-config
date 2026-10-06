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

"""The expert custom supplier: a card typed in by the household.

No card is fetched. The household types its price, its fixed fee and the
regulated figures of its DSO as its own card or bill prints them (c EUR/kWh
and EUR a year, VAT inclusive), and :func:`build_snapshot` turns them into
the snapshot the coordinator prices on. There is no drift check and no
archive: the figures are what the household keeps current.
"""

from __future__ import annotations

from typing import Any

import aiohttp

from ..const import (
    CALIBERS,
    CONF_CALIBER,
    CONF_CUSTOM_CONNECTION_FEE,
    CONF_CUSTOM_CONTRIBUTION,
    CONF_CUSTOM_EXCISE_HIGH,
    CONF_CUSTOM_EXCISE_LOW,
    CONF_CUSTOM_FEE,
    CONF_CUSTOM_LEVY,
    CONF_CUSTOM_METERING,
    CONF_CUSTOM_PRICE,
    CONF_CUSTOM_T1_FIXED,
    CONF_CUSTOM_T1_PROP,
    CONF_CUSTOM_T2_FIXED,
    CONF_CUSTOM_T2_PROP,
    CONF_CUSTOM_TRANSPORT,
    CONF_DSO,
    CUSTOM_CONTRACT,
    DEFAULT_CALIBER,
    OSP_Q10_HIGH,
    OSP_Q10_LOW,
    SUPPLIER_CUSTOM,
    TIER_T1,
    TIER_T2,
)
from ._network import excise_bands
from ._rates import Contract, FixedRates
from .base import (
    DsoOverlay,
    DsoTier,
    ExtractorError,
    SupplierExtractor,
    SupplierSnapshot,
    TaxOverlay,
)


def _number(data: dict[str, Any], key: str) -> float:
    return float(data.get(key) or 0.0)


def build_snapshot(data: dict[str, Any]) -> SupplierSnapshot:
    """The household's typed card, in the snapshot's EUR units."""
    dso = str(data[CONF_DSO])
    caliber = str(data.get(CONF_CALIBER, DEFAULT_CALIBER))
    levy = _number(data, CONF_CUSTOM_LEVY)
    # The levy is typed for the household's own caliber: both halves of the
    # smallest one carry it, so whichever side of 5 000 kWh the year lands
    # on bills what the household typed.
    osp = None
    if levy:
        keys = (OSP_Q10_LOW, OSP_Q10_HIGH) if caliber == CALIBERS[0] else (caliber,)
        osp = dict.fromkeys(keys, levy)
    high = data.get(CONF_CUSTOM_EXCISE_HIGH)
    return SupplierSnapshot(
        supplier=SUPPLIER_CUSTOM,
        contract=CUSTOM_CONTRACT,
        energy=FixedRates(
            price=_number(data, CONF_CUSTOM_PRICE) / 100.0,
            yearly_fixed_fee=_number(data, CONF_CUSTOM_FEE),
        ),
        dsos={
            dso: DsoOverlay(
                tiers={
                    TIER_T1: DsoTier(
                        fixed_per_year=_number(data, CONF_CUSTOM_T1_FIXED),
                        proportional=_number(data, CONF_CUSTOM_T1_PROP) / 100.0,
                    ),
                    TIER_T2: DsoTier(
                        fixed_per_year=_number(data, CONF_CUSTOM_T2_FIXED),
                        proportional=_number(data, CONF_CUSTOM_T2_PROP) / 100.0,
                    ),
                },
                transport=_number(data, CONF_CUSTOM_TRANSPORT) / 100.0,
                metering_per_year=_number(data, CONF_CUSTOM_METERING),
            )
        },
        taxes=TaxOverlay(
            excise_bands=excise_bands(
                _number(data, CONF_CUSTOM_EXCISE_LOW) / 100.0,
                None if high in (None, "") else float(high) / 100.0,
            ),
            energy_contribution=_number(data, CONF_CUSTOM_CONTRIBUTION) / 100.0,
            connection_fee=_number(data, CONF_CUSTOM_CONNECTION_FEE) / 100.0,
            osp_by_caliber=osp,
        ),
        source_url="",
        publication_label="custom",
    )


async def _no_card(
    session: aiohttp.ClientSession, contract_id: str, region: str
) -> SupplierSnapshot:
    raise ExtractorError("the custom supplier has no card to fetch")


EXTRACTOR = SupplierExtractor(
    id=SUPPLIER_CUSTOM,
    label="Expert: custom figures",
    contracts=(Contract(id=CUSTOM_CONTRACT, label="Custom fixed price", kind="fixed"),),
    fetch=_no_card,
    sweep_cost_s=0.0,
)
