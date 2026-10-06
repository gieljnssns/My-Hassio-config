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

"""Pure cost-projection helpers (no Home Assistant imports).

Kept separate from :mod:`coordinator` so the math is unit-testable from
a plain venv. The coordinator imports both helpers and applies them to
the user's stored options:

  * :func:`compute_annual_cost` -- the full-year projection that powers
    ``sensor.<utility>_projected_annual_cost``. Pro-rates nothing.
  * :func:`compute_ytd_cost` -- the running year-to-date bill that
    powers ``sensor.<utility>_current_year_cost``. The volumetric branch is
    the same; only the annual fees (vastrecht / redevance) are
    pro-rated by the elapsed fraction of the calendar year so the
    sensor sits at ~0 on Jan 1 and grows to the full fee by Dec 31.
"""

from __future__ import annotations

from .providers.base import WaterTariff


def _compute_bill(
    tariff: WaterTariff,
    consumption_m3: float,
    persons: int,
    fee_factor: float,
    *,
    social_tariff: bool,
) -> float | None:
    """Internal: same regional bill math, with the annual fee scaled by
    ``fee_factor`` (1.0 for the full-year projection, 0..1 for YTD).

    Returns ``None`` when the tariff is shaped for a region whose math
    is not yet wired in.

    **Brussels** (linear): ``consumption × (linear + sanering) +
    fee_factor · redevance``, then VAT. ``persons`` unused.

    **Wallonia** (tier): the first 30 m³ pay ``0.5·CVD + 0·CVA + FSE``
    per m³ (CVA is exempt on the residential first block by CWaPE
    rule), 31 to 5000 m³ pay the full ``CVD + CVA + FSE``, and above
    5000 m³ the CVD falls to 90 %, plus ``fee_factor · redevance``.
    ``persons`` unused. The block allowances are annual (reset on
    Jan 1), so YTD consumption fills them up the same way an annual
    projection does. CILE publishes four further tranches above
    50 000 m³; nothing this integration meters comes near them.

    **Flanders** (block): basis volume = ``30 + 30·persons`` m³, which
    the decree does not cap. Inside the basis volume each m³
    pays ``basis + sanering_boven + sanering_gemeente``; above it each
    m³ pays the comforttarief which is exactly ``2 ×`` each of those
    components -- this 2× rule is mandated by VMM and applies
    uniformly, so the calc engine doubles the sanering values rather
    than the extractors carrying duplicate fields. The annual vastrecht
    is ``max(0, yearly_fixed_fee − persons · korting) · fee_factor``;
    that floor is also what caps the korting at five residents, since
    the uniform 20 EUR per resident cancels the uniform 100 EUR
    vastrecht exactly.
    ``social_tariff=True`` applies the VMM 80 % reduction on the
    post-calc total.
    """
    consumption_m3 = max(0.0, consumption_m3)
    if tariff.region == "brussels":
        if tariff.linear_eur_per_m3 is None:
            return None
        per_m3 = tariff.linear_eur_per_m3 + (
            tariff.sanering_bovengemeentelijk_eur_per_m3 + tariff.sanering_gemeentelijk_eur_per_m3
        )
        ex_vat = consumption_m3 * per_m3 + fee_factor * tariff.yearly_fixed_fee
        total = ex_vat * (1.0 + tariff.vat_rate)
        return round(total, 2)

    if tariff.region == "wallonia":
        cvd = tariff.cvd_eur_per_m3
        if cvd <= 0:
            return None
        cva = tariff.cva_eur_per_m3
        fse = tariff.fse_eur_per_m3
        first_block = min(consumption_m3, 30.0) * (0.5 * cvd + fse)
        middle = max(0.0, min(consumption_m3, 5000.0) - 30.0) * (cvd + cva + fse)
        # Above 5000 m3 the CVD falls to 90 %, which every Walloon page
        # prints and AIEC's card spells out as "(0,9 x CVD) + CVA". No
        # household reaches it, but the year-to-date bill is driven by the
        # meter rather than by the configured consumption, so a shared or
        # building-wide meter can, and billing it the tranche below is
        # 376.85 EUR out at 6000 m3 on CILE's rates.
        top = max(0.0, consumption_m3 - 5000.0) * (0.9 * cvd + cva + fse)
        ex_vat = first_block + middle + top + fee_factor * tariff.yearly_fixed_fee
        return round(ex_vat * (1.0 + tariff.vat_rate), 2)

    if tariff.region == "flanders":
        if tariff.basis_eur_per_m3 is None:
            return None
        comfort = (
            tariff.comfort_eur_per_m3
            if tariff.comfort_eur_per_m3 is not None
            else 2.0 * tariff.basis_eur_per_m3
        )
        san = tariff.sanering_bovengemeentelijk_eur_per_m3 + tariff.sanering_gemeentelijk_eur_per_m3
        basis_volume = 30.0 + 30.0 * persons
        consumed_basis = min(consumption_m3, basis_volume)
        consumed_comfort = max(0.0, consumption_m3 - basis_volume)
        per_m3_basis = tariff.basis_eur_per_m3 + san
        per_m3_comfort = comfort + 2.0 * san
        volumetric = consumed_basis * per_m3_basis + consumed_comfort * per_m3_comfort
        vastrecht = max(
            0.0,
            tariff.yearly_fixed_fee - persons * tariff.yearly_fixed_fee_per_resident_discount,
        )
        ex_vat = volumetric + fee_factor * vastrecht
        total = ex_vat * (1.0 + tariff.vat_rate)
        if social_tariff:
            total *= 0.20  # VMM social tariff = 80% reduction on the post-calc total.
        return round(total, 2)

    return None


def compute_annual_cost(
    tariff: WaterTariff,
    consumption_m3: float,
    persons: int,
    *,
    social_tariff: bool = False,
) -> float | None:
    """Return the full-year projected VAT-incl bill in EUR (annual fees at 100 %).

    See :func:`_compute_bill` for the per-region math.
    """
    return _compute_bill(tariff, consumption_m3, persons, 1.0, social_tariff=social_tariff)


def compute_ytd_cost(
    tariff: WaterTariff,
    consumption_m3_ytd: float,
    persons: int,
    year_elapsed_fraction: float,
    *,
    social_tariff: bool = False,
) -> float | None:
    """Return the running YTD VAT-incl bill in EUR.

    ``consumption_m3_ytd`` is the m³ consumed since Jan 1 of the
    current year (read from HA's recorder by the coordinator).
    ``year_elapsed_fraction`` is in ``[0.0, 1.0]`` and pro-rates the
    annual vastrecht / redevance so the sensor grows day by day instead
    of jumping to the full annual fee on Jan 1. The volumetric branch
    is identical to :func:`compute_annual_cost`: block / tier
    allowances are annual and reset on Jan 1, so YTD consumption fills
    them up exactly as a full-year projection would.
    """
    fee_factor = max(0.0, min(1.0, year_elapsed_fraction))
    return _compute_bill(
        tariff, consumption_m3_ytd, persons, fee_factor, social_tariff=social_tariff
    )
