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

"""Reading the regulated blocks of a gas card: the DSO table and the levies.

Every card reprints the same regulated figures, laid out its own way. The
DSO table in particular comes in three column orders (fixed then
proportional within each tier, the reverse, or every proportional term before
every fixed one), so a reader never assumes one: the extractor names the
columns as its card's header does, and this module turns the cells into
:class:`DsoOverlay` values in EUR.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from itertools import pairwise

from ..const import (
    CALIBER_GT160,
    CALIBER_Q16,
    CALIBER_Q25,
    CALIBER_Q40,
    CALIBER_Q65,
    CALIBER_Q100,
    CALIBER_Q160,
    DSO_FLUVIUS_ANTWERPEN,
    DSO_FLUVIUS_HALLE_VILVOORDE,
    DSO_FLUVIUS_IMEWO,
    DSO_FLUVIUS_KEMPEN,
    DSO_FLUVIUS_LIMBURG,
    DSO_FLUVIUS_MIDDEN_VLAANDEREN,
    DSO_FLUVIUS_WEST,
    DSO_FLUVIUS_ZENNE_DIJLE,
    DSO_ORES,
    ENERGY_CONTRIBUTION_ZEROED_FROM,
    EXCISE_BAND_KWH,
    OSP_Q10_HIGH,
    OSP_Q10_LOW,
    REGION_DSO_KEYS,
    TIER_T1,
    TIER_T2,
    TIER_T3,
)
from ._parse import cell_value, table_row, to_float
from .base import DsoOverlay, DsoTier, ExtractorError

# Column roles a DSO table can carry. Proportional terms and transport are
# printed in c EUR/kWh on every card but one, which prints transport in
# EUR/MWh; fixed terms and metering in EUR/year. "skip" is a column the
# gas bill does not use (a monthly-reading fee, a levy printed inside the
# table and read elsewhere).
T1_FIXED = "t1_fixed"
T1_PROP = "t1_prop"
T2_FIXED = "t2_fixed"
T2_PROP = "t2_prop"
T3_FIXED = "t3_fixed"
T3_PROP = "t3_prop"
TRANSPORT = "transport"
TRANSPORT_MWH = "transport_mwh"
METERING = "metering"
SKIP = "skip"

_TIER_COLUMNS = (
    (TIER_T1, T1_FIXED, T1_PROP),
    (TIER_T2, T2_FIXED, T2_PROP),
    (TIER_T3, T3_FIXED, T3_PROP),
)

# The eight Fluvius areas as most cards print them. A card that spells them
# otherwise passes its own map; similarity matching absorbs padding and the
# odd typo, not a different name.
FLUVIUS_LABELS: dict[str, str] = {
    "Fluvius Antwerpen": DSO_FLUVIUS_ANTWERPEN,
    "Fluvius Halle-Vilvoorde": DSO_FLUVIUS_HALLE_VILVOORDE,
    "Fluvius Imewo": DSO_FLUVIUS_IMEWO,
    "Fluvius Kempen": DSO_FLUVIUS_KEMPEN,
    "Fluvius Limburg": DSO_FLUVIUS_LIMBURG,
    "Fluvius Midden-Vlaanderen": DSO_FLUVIUS_MIDDEN_VLAANDEREN,
    "Fluvius West": DSO_FLUVIUS_WEST,
    "Fluvius Zenne-Dijle": DSO_FLUVIUS_ZENNE_DIJLE,
}

# The five ORES sub-areas, all onto the one ORES key.
ORES_LABELS: dict[str, str] = {
    "ORES (Brabant Wallon)": DSO_ORES,
    "ORES (Hainaut Gaz)": DSO_ORES,
    "ORES (Luxembourg)": DSO_ORES,
    "ORES (Mouscron)": DSO_ORES,
    "ORES (Namur)": DSO_ORES,
}


def dso_overlay(
    cells: Sequence[str],
    columns: Sequence[str],
    *,
    supplier: str,
    label: str,
    transport: float | None = None,
    metering: float | None = None,
) -> DsoOverlay:
    """One DSO's overlay from its row's cells, named by ``columns``.

    T1 and T2 are mandatory: every residential card prints both, so a gap is
    a misread. T3 is kept when the card prints both of its terms. A tier
    that is not degressive is dropped with those above it. Transport comes
    from its column, or from ``transport`` when the card prints it once for
    every DSO; metering likewise, and a dash there means none.
    """
    if len(cells) != len(columns):
        raise ExtractorError(
            f"{supplier}: {label} row has {len(cells)} cells, expected {len(columns)}"
        )
    values: dict[str, float | None] = {}
    for role, cell in zip(columns, cells, strict=True):
        if role != SKIP:
            values[role] = cell_value(cell)

    tiers: dict[str, DsoTier] = {}
    for tier, fixed_role, prop_role in _TIER_COLUMNS:
        fixed = values.get(fixed_role)
        prop = values.get(prop_role)
        if fixed is None or prop is None:
            if tier != TIER_T3:
                raise ExtractorError(f"{supplier}: {label} has no {tier.upper()} tariff")
            continue
        if tiers and prop / 100.0 >= list(tiers.values())[-1].proportional:
            # Each tier's proportional term is below the one before it on
            # every row the regulators publish. A row that breaks this has a
            # figure in the wrong cell ("FLUVIUS LIMBURG 2,09 13,32 70,72
            # 70,72" on the 2025 Energy Together cards, Dots repeating a T1
            # term as T2), so the tiers from there up are dropped rather than
            # billed: a household on them gets a pricing error, not a wrong
            # bill, and every other row of the card still prices.
            break
        tiers[tier] = DsoTier(fixed_per_year=fixed, proportional=prop / 100.0)

    if TRANSPORT in values or TRANSPORT_MWH in values:
        printed = values.get(TRANSPORT)
        per_mwh = values.get(TRANSPORT_MWH)
        if printed is not None:
            transport = printed / 100.0
        elif per_mwh is not None:
            transport = per_mwh / 1000.0
    if transport is None:
        raise ExtractorError(f"{supplier}: {label} has no transport tariff")

    if METERING in values:
        metering = values[METERING]
    return DsoOverlay(tiers=tiers, transport=transport, metering_per_year=metering or 0.0)


def read_dsos(
    text: str,
    labels: Mapping[str, str],
    columns: Sequence[str],
    *,
    supplier: str,
    after: str | None = None,
    before: str | None = None,
    transport: float | None = None,
    metering: float | None = None,
) -> dict[str, DsoOverlay]:
    """Every DSO of ``labels`` the table carries, by DSO key.

    Several labels may name one key: the five ORES sub-areas do. Their rows
    must then agree, since one tariff covers them all; rows that do not say
    the table was misread, and a guess between them would bill the wrong
    figure. A label the table does not carry is left out, and the caller
    decides with :func:`require_region` whether that is a gap.
    """
    found: dict[str, DsoOverlay] = {}
    for label, key in labels.items():
        cells = table_row(text, label, len(columns), after=after, before=before)
        if cells is None:
            continue
        overlay = dso_overlay(
            cells,
            columns,
            supplier=supplier,
            label=label,
            transport=transport,
            metering=metering,
        )
        if key in found and found[key] != overlay:
            raise ExtractorError(f"{supplier}: the {key} rows disagree ({label})")
        found[key] = overlay
    return found


def require_region(dsos: Mapping[str, DsoOverlay], region: str, supplier: str) -> None:
    """Raise unless every DSO of ``region`` was read."""
    missing = sorted(REGION_DSO_KEYS[region] - dsos.keys())
    if missing:
        raise ExtractorError(f"{supplier}: DSO rows not found: {', '.join(missing)}")


def excise_bands(low: float, high: float | None) -> tuple[tuple[float | None, float], ...]:
    """The special excise as bands, from its two printed rates in EUR/kWh.

    ``high`` None is a card printing a single rate, which is kept as one open
    band rather than stretched over both slices.
    """
    if high is None:
        return ((None, low),)
    return ((EXCISE_BAND_KWH, low), (None, high))


def printed_contribution(figure: str | None, card_month: date, *, supplier: str) -> float:
    """The energy contribution a card prints in c EUR/kWh, in EUR/kWh.

    The law set the residential levy to zero from August 2026 and the cards
    dropped the row then, so only a card from before has to print it.
    """
    if figure is not None:
        return to_float(figure) / 100.0
    if (card_month.year, card_month.month) >= ENERGY_CONTRIBUTION_ZEROED_FROM:
        return 0.0
    raise ExtractorError(f"{supplier}: energy contribution row not found")


# The Brussels per-meter levy rows in the order every card prints them: the
# smallest caliber twice (up to 5 000 kWh, then above), then each larger
# caliber, the open-ended one last. Cards word and lay the rows out too
# differently for one reader ("6 of 10 m3/h 4" with the amount on the next
# line, "<= 10 m³/h 5 3,56", a bare "16 30.4"), so each extractor reads its
# amounts in order and this maps them.
_OSP_ORDER = (
    OSP_Q10_LOW,
    OSP_Q10_HIGH,
    CALIBER_Q16,
    CALIBER_Q25,
    CALIBER_Q40,
    CALIBER_Q65,
    CALIBER_Q100,
    CALIBER_Q160,
    CALIBER_GT160,
)


def osp_table(amounts: Sequence[float], *, supplier: str) -> dict[str, float]:
    """The Brussels per-meter levy, in EUR/year, from its amounts in row order.

    Eight amounts is a card that leaves out the open-ended caliber above
    160 m3/h. The amounts must rise with the caliber, which is what catches
    a footnote digit or a caliber read as an amount.
    """
    if len(amounts) not in (len(_OSP_ORDER) - 1, len(_OSP_ORDER)):
        raise ExtractorError(f"{supplier}: Brussels levy table has {len(amounts)} rows")
    if any(later <= earlier for earlier, later in pairwise(amounts)):
        raise ExtractorError(f"{supplier}: Brussels levy amounts do not rise with the caliber")
    return dict(zip(_OSP_ORDER, amounts, strict=False))
