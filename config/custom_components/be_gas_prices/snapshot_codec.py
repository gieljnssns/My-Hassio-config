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

"""A snapshot as JSON and back.

One format serves three stores: the entry's own ``.storage`` blob, the
per-month card cache, and the card archive the ``archive_cards`` workflow
writes to be_price_cards. A blob written under another schema version is
refused rather than migrated: everything in it is re-derivable from a card,
except the archive's rows of contracts the supplier withdrew, which its
replay keeps as they are. A schema bump must rewrite those by hand.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .providers._rates import EnergyRates, FixedRates, IndexedRates, VariableRates
from .providers.base import DsoOverlay, DsoTier, SupplierSnapshot, TaxOverlay

# Bumped whenever a field is added, removed or changes meaning, so a blob an
# older release wrote is dropped instead of being read with a wrong shape;
# and by a release that refuses a card an older one misread, since a stored
# card no one serves any more is otherwise kept.
SNAPSHOT_SCHEMA_VERSION = 1


class SnapshotDecodeError(ValueError):
    """The blob is not a snapshot this release can read."""


def _energy_to_json(energy: EnergyRates) -> dict[str, Any]:
    if isinstance(energy, FixedRates):
        return {"kind": "fixed", "price": energy.price, "fee": energy.yearly_fixed_fee}
    if isinstance(energy, VariableRates):
        return {
            "kind": "variable",
            "price": energy.price,
            "fee": energy.yearly_fixed_fee,
            "formula": energy.formula,
        }
    return {
        "kind": "indexed",
        "factor": energy.factor,
        "base": energy.base,
        "index": energy.index,
        "price": energy.price,
        "fee": energy.yearly_fixed_fee,
        "formula": energy.formula,
        "settled": energy.settled,
        "period": energy.period,
    }


def _energy_from_json(blob: dict[str, Any]) -> EnergyRates:
    kind = blob["kind"]
    if kind == "fixed":
        return FixedRates(price=float(blob["price"]), yearly_fixed_fee=float(blob["fee"]))
    if kind == "variable":
        return VariableRates(
            price=float(blob["price"]),
            yearly_fixed_fee=float(blob["fee"]),
            formula=blob.get("formula"),
        )
    if kind == "indexed":
        period = blob["period"]
        if period not in ("month", "quarter"):
            raise SnapshotDecodeError(f"unknown index period {period!r}")
        return IndexedRates(
            factor=float(blob["factor"]),
            base=float(blob["base"]),
            index=str(blob["index"]),
            price=float(blob["price"]),
            yearly_fixed_fee=float(blob["fee"]),
            formula=blob.get("formula"),
            settled=bool(blob["settled"]),
            period=period,
        )
    raise SnapshotDecodeError(f"unknown energy kind {kind!r}")


def _dso_to_json(overlay: DsoOverlay) -> dict[str, Any]:
    return {
        "tiers": {
            tier: [values.fixed_per_year, values.proportional]
            for tier, values in overlay.tiers.items()
        },
        "transport": overlay.transport,
        "metering": overlay.metering_per_year,
    }


def _dso_from_json(blob: dict[str, Any]) -> DsoOverlay:
    return DsoOverlay(
        tiers={
            tier: DsoTier(fixed_per_year=float(pair[0]), proportional=float(pair[1]))
            for tier, pair in blob["tiers"].items()
        },
        transport=float(blob["transport"]),
        metering_per_year=float(blob["metering"]),
    )


def _taxes_to_json(taxes: TaxOverlay) -> dict[str, Any]:
    return {
        "excise": [[upper, rate] for upper, rate in taxes.excise_bands],
        "contribution": taxes.energy_contribution,
        "connection_fee": taxes.connection_fee,
        "osp": taxes.osp_by_caliber,
        "vat_rate": taxes.vat_rate,
        "card_vat_rate": taxes.card_vat_rate,
    }


def _taxes_from_json(blob: dict[str, Any]) -> TaxOverlay:
    osp = blob.get("osp")
    card_vat = blob.get("card_vat_rate")
    return TaxOverlay(
        excise_bands=tuple(
            (None if upper is None else float(upper), float(rate)) for upper, rate in blob["excise"]
        ),
        energy_contribution=float(blob["contribution"]),
        connection_fee=float(blob["connection_fee"]),
        osp_by_caliber=None if osp is None else {k: float(v) for k, v in osp.items()},
        vat_rate=float(blob["vat_rate"]),
        card_vat_rate=None if card_vat is None else float(card_vat),
    )


def snapshot_to_json(snapshot: SupplierSnapshot) -> dict[str, Any]:
    """A JSON-safe dict for ``snapshot``, stamped with the schema version."""
    return {
        "schema": SNAPSHOT_SCHEMA_VERSION,
        "supplier": snapshot.supplier,
        "contract": snapshot.contract,
        "energy": _energy_to_json(snapshot.energy),
        "dsos": {key: _dso_to_json(overlay) for key, overlay in snapshot.dsos.items()},
        "taxes": _taxes_to_json(snapshot.taxes),
        "source_url": snapshot.source_url,
        "publication_label": snapshot.publication_label,
        "valid_until": None if snapshot.valid_until is None else snapshot.valid_until.isoformat(),
    }


def snapshot_from_json(blob: Any) -> SupplierSnapshot:
    """The snapshot ``blob`` holds, or :class:`SnapshotDecodeError`."""
    if not isinstance(blob, dict) or blob.get("schema") != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotDecodeError("not a snapshot of this schema version")
    try:
        valid_until = blob.get("valid_until")
        return SupplierSnapshot(
            supplier=str(blob["supplier"]),
            contract=str(blob["contract"]),
            energy=_energy_from_json(blob["energy"]),
            dsos={str(key): _dso_from_json(value) for key, value in blob["dsos"].items()},
            taxes=_taxes_from_json(blob["taxes"]),
            source_url=str(blob["source_url"]),
            publication_label=str(blob.get("publication_label", "")),
            valid_until=None if valid_until is None else date.fromisoformat(valid_until),
        )
    except (KeyError, IndexError, TypeError, ValueError, AttributeError) as err:
        raise SnapshotDecodeError(f"malformed snapshot: {err}") from err
