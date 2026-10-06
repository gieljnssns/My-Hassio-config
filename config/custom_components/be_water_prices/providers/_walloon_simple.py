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

"""Shared builder for the small Walloon intercommunales.

IEG, AIEM, AIEC, CIESAC and IDEN all follow the standard CWaPE
residential structure (same as SWDE / inBW / CILE / INASEP) but each
serves a tiny territory and publishes their CVD on a single web page
in plain prose like::

    CVD : Coût Vérité de Distribution : 2,3800€/m³
    Valeur actuelle du CVD : 2,87€ HTVA
    (CVD) : 2,460 €/m³

CVA and FSE are the SPGE flat-Wallonia constants and come from
:mod:`const`. The redevance is materialised at parse time from the
regulator-defined ``20·CVD + 30·CVA`` formula.

IEG, AIEM and IDEN expose their CVD on the operator's own site. AIEC
publishes its card as a picture, so :mod:`aiec` reads the picture's date
and serves the rate transcribed against it. CIESAC's site has answered
ERR_UPDATING_SERVER for months, which leaves Callmepower's public
aggregator listing as the only source for it, and an unverified one: two
of the three cards that aggregator used to supply here were found wrong
on 2026-09-08.
"""

from __future__ import annotations

import logging
import re
from datetime import date

import aiohttp
from bs4 import BeautifulSoup

from ..const import (
    DEFAULT_VAT_RATE,
    REGION_WALLONIA,
    WALLONIA_CVA_EUR_PER_M3,
    WALLONIA_FSE_EUR_PER_M3,
)
from ._html import fetch_and_parse
from ._pdf import to_float
from .base import ExtractorError, WaterExtractor, WaterTariff, belgian_today, carry_prior_year_card

_LOGGER = logging.getLogger(__name__)


# Match "CVD" followed (within ~120 chars, possibly across labels and
# colons) by the next ``N,NNN €`` amount. Tolerant of the three
# distinct phrasings observed across operator sites and Callmepower.
_CVD_RE = re.compile(
    r"CVD[^\d€]{0,120}?(\d+,\d{1,5})\s*€",
    re.IGNORECASE | re.DOTALL,
)
# Strong anchor that wins over the generic regex when present: AIEM's
# page introduces example formulas like "0,5 x CVD (soit 1,435€)"
# before the real value, so a first-match-wins approach picks the
# example and under-reports. "Valeur actuelle du CVD : 2,87€" gives
# us the right one.
_ACTUAL_CVD_RE = re.compile(
    r"actuelle\s+du\s+CVD[^\d]{0,40}(\d+,\d{1,5})\s*€?",
    re.IGNORECASE,
)
# Callmepower's mid-2026 redesign leads with a summary-card grid that
# renders each value BEFORE its label ("2,460 €/m³" then "CVD
# (distribution)"), with the CVA card immediately after. The generic
# forward-looking _CVD_RE reads the label "CVD (distribution)" and grabs
# the next card's number -- the CVA -- so for AIEC (CVD 2,46 < CVA 2,748)
# it silently returned the CVA. Anchor instead on the authoritative prose
# "Coût vérité distribution (CVD) : N €", where the value FOLLOWS the
# "distribution (CVD)" label; the reversed card text cannot match it.
# IEG and AIEM sit on operator sites without this phrasing, so they fall
# through to the anchors below unchanged.
_LABELED_DIST_CVD_RE = re.compile(
    r"distribution\s*\(\s*CVD\s*\)\s*:?\s*(\d+,\d{1,5})\s*€",
    re.IGNORECASE,
)
# Plausibility window for residential Walloon CVDs. As of 2026 the
# smallest distributor publishes ~2.30 EUR/m³ and the largest ~3.60
# EUR/m³. The lower bound MUST exclude AIEM's documented example
# value "0,5 x CVD (soit 1,435€)" -- the figure shown in that formula
# (1.435) is exactly the trap the example-context filter has to
# catch. 1.5 is the tightest floor that achieves that.
#
# Trade-off: a future regulatory cut to ~1.4 (CWaPE-mandated, a
# subsidised sub-region) would flip a correctly-published value into
# UpdateFailed until this bound is widened. That visible failure is
# preferable to silently emitting the example figure -- the Repairs
# UI surfaces it and a maintainer can adjust the bound for the
# affected utility once the new minimum is known.
_MIN_PLAUSIBLE_CVD = 1.5
_MAX_PLAUSIBLE_CVD = 6.0


def warn_constant_drift(
    *,
    published: float | None,
    constant: float,
    label: str,
    logger: logging.Logger,
    threshold: float = 0.005,
) -> None:
    """Refuse a CVA / FSE value that has moved away from the SPGE constant.

    The CVA and FSE are flat across Wallonia and carried here as
    constants, so when a page publishes a different figure every Walloon
    entry is being priced on a number that is no longer the tariff. A log
    line was the only signal, and nothing reads the log: the extractor
    still returned a tariff, so live_check passed, fixture_drift compared
    only fields we source from the page, and users were quietly
    mis-billed until somebody noticed.

    Raising instead puts it on the paths that are watched. The
    coordinator keeps serving the last good snapshot and raises the
    stale-snapshot Repair, and the daily live check fails and opens an
    issue -- which is what a regulated price change should look like.

    ``label`` should identify both the utility and the component, e.g.
    ``"SWDE CVA"`` or ``"CILE FSE"``. No-op when ``published`` is ``None``
    (the row was not present on the page; :func:`check_spge_constants`
    decides separately whether that absence is itself a failure).

    Failing closed has a cost worth stating plainly: CWaPE moves the CVA
    on 1 January, every Walloon page picks the new figure up at once, and
    all nine Walloon extractors then stop until a release carries the new
    constant. That is the trade, and the message says what clears it. The
    alternative is worse, because the constant is what the household is
    actually billed on, so failing open bills everyone on last year's
    figure with nothing to show for it.

    Every Walloon page prints the CVA and most print the FSE: the
    table-based extractors read them off their rows, the prose-based
    ones through :func:`parse_cva` and :func:`parse_fse`. A page that
    stops printing one simply stops being checked for it.
    """
    if published is None:
        return
    if abs(published - constant) > threshold:
        logger.warning(
            "%s published value %s differs from Wallonia constant %s",
            label,
            published,
            constant,
        )
        raise ExtractorError(
            f"{label} published value {published} differs from the flat-Wallonia "
            f"constant {constant}; the SPGE component has moved and every Walloon "
            f"tariff is priced on the old figure until the constant is updated. "
            f"Set it in const.py (WALLONIA_CVA_EUR_PER_M3 / WALLONIA_FSE_EUR_PER_M3) "
            f"and ship a release: until then every Walloon entry keeps its last good "
            f"snapshot and raises the stale-snapshot Repair"
        )


# Where the prose pages print the two SPGE components. Each pattern binds
# the amount to its own label, so Callmepower's summary cards, which put
# the value before the label and the CVD card right next to the CVA one,
# cannot answer for each other. Every gap is bounded.
_CVA_RES = (
    # AIEM: "Valeur actuelle du CVA : 2,748€"
    re.compile(r"actuelle\s+du\s+CVA[^\d€]{0,40}(\d+,\d{1,5})\s*€", re.IGNORECASE),
    # Callmepower prose and INASEP: "assainissement (CVA) : 2,748 €", "(CVA) = 2,748 €"
    re.compile(r"assainissement\s*\(\s*CVA\s*\)\s*[:=]?\s*(\d+,\d{1,5})\s*€", re.IGNORECASE),
    # IEG: "CVA : Coût Vérité d'Assainissement : 2,7480€"
    re.compile(
        r"CVA\s*:\s*Co[ûu]t\s+V[ée]rit[ée]\s+d.Assainissement\s*:\s*(\d+,\d{1,5})\s*€",
        re.IGNORECASE,
    ),
)
_FSE_RES = (
    # Callmepower and INASEP: "Fonds social de l'eau : 0,0339 €", "= 0,0339 €"
    re.compile(r"fonds\s+social\s+de\s+l.eau\s*[:=]\s*(\d+,\d{1,5})\s*€", re.IGNORECASE),
    # IEG: "fonds social de l'eau de 0,0339€"
    re.compile(r"fonds\s+social\s+de\s+l.eau\s+de\s+(\d+,\d{1,5})\s*€", re.IGNORECASE),
    # AIEM: "Fonds social de l'eau ... Nombre de m³ x 0,0339€"
    re.compile(r"fonds\s+social\s+de\s+l.eau[^€]{0,80}?x\s*(\d+,\d{1,5})\s*€", re.IGNORECASE),
)


def hold_to_constant(
    *,
    published: float | None,
    constant: float,
    label: str,
    logger: logging.Logger,
    threshold: float = 0.005,
) -> None:
    """:func:`warn_constant_drift`, with an absent value counting as a failure.

    A check that has quietly stopped running is worth nothing. The label
    it binds to moves, the value reads as absent, and the next SPGE step
    then rides through unseen on a constant nobody is comparing to
    anything. Every Walloon page these parsers read prints a CVA, so its
    absence is the page having changed shape, which is a parser problem
    and should be visible.
    """
    if published is None:
        raise ExtractorError(
            f"{label} is no longer printed on the page, so the constant "
            f"{constant} cannot be checked against it"
        )
    warn_constant_drift(
        published=published,
        constant=constant,
        label=label,
        logger=logger,
        threshold=threshold,
    )


def _first_amount(text: str, patterns: tuple[re.Pattern[str], ...]) -> float | None:
    for pattern in patterns:
        match = pattern.search(text)
        if match is not None:
            return to_float(match.group(1))
    return None


def parse_cva(text: str) -> float | None:
    """The CVA a prose page prints, or ``None`` when it prints none."""
    return _first_amount(text, _CVA_RES)


def parse_fse(text: str) -> float | None:
    """The Fonds social contribution a prose page prints, or ``None``."""
    return _first_amount(text, _FSE_RES)


def check_spge_constants(text: str, *, utility_id: str, logger: logging.Logger) -> None:
    """Hold the CVA and FSE a page prints to the SPGE constants.

    A page that has moved on from the constant is priced wrong for every
    entry on it; see :func:`warn_constant_drift` for why that fails the
    fetch rather than logging.

    A page that stops printing the CVA at all fails too. Every Walloon
    page these parsers read prints one, so its absence is the label
    having moved, and a check that has quietly stopped running is worth
    nothing. The FSE is not held to the same rule: CIESAC's page really
    does omit it.
    """
    hold_to_constant(
        published=parse_cva(text),
        constant=WALLONIA_CVA_EUR_PER_M3,
        label=f"{utility_id} CVA",
        logger=logger,
    )
    warn_constant_drift(
        published=parse_fse(text),
        constant=WALLONIA_FSE_EUR_PER_M3,
        label=f"{utility_id} FSE",
        logger=logger,
        threshold=0.001,
    )


def parse_cvd(html: str) -> float:
    """Return the CVD in EUR/m³ from a captured Walloon utility page.

    Tries in order:
      1. ``actuelle du CVD : N,NNN €`` (the AIEM "current value" phrasing).
      2. ``distribution (CVD) : N,NNN €`` -- the Callmepower prose label,
         where the value FOLLOWS the "distribution (CVD)" text. This wins
         on Callmepower's redesigned summary-card pages, whose cards place
         "CVD (distribution)" just before the CVA card's number and would
         otherwise mislead the forward scan below.
      3. The largest CVD reference whose value falls inside the
         plausibility window. Picking the largest rather than the first
         protects against pages that quote a historic value before the
         current one (CVDs only index up).

    Raises :class:`ExtractorError` when no ``CVD … N,NNN €`` string is
    found inside the rendered text.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)

    for pattern in (_ACTUAL_CVD_RE, _LABELED_DIST_CVD_RE):
        # Every plausible match the anchor finds, not the first. Taking
        # the first meant a page that prints a historic value under the
        # same label before the current one, or a neighbouring
        # distributor's, priced the household on whichever came earlier in
        # the markup: AIEC's 2,46 against 2,90 is 40 EUR a year. The
        # generic scan below already reasons this way, and for the same
        # reason: a CVD only indexes up, so the largest of the values a
        # page presents under a current-value label is the current one.
        #
        # The window gate stays: a labelled but out-of-window value falls
        # through to that scan rather than riding straight out.
        candidates = [
            value
            for value in (to_float(m) for m in pattern.findall(text))
            if _MIN_PLAUSIBLE_CVD <= value <= _MAX_PLAUSIBLE_CVD
        ]
        if candidates:
            return max(candidates)

    matches = [to_float(m) for m in _CVD_RE.findall(text)]
    if not matches:
        raise ExtractorError("could not find CVD on the published page")
    # Callmepower renders the CVA card right next to the CVD one, and the
    # CVA is flat across Wallonia and larger than several distributors'
    # CVD -- so it sits in the window and wins a max() every time. It is
    # a known number, so drop it rather than let it stand in for a rate
    # it is not. A distributor whose real CVD lands on the same figure
    # loses the fallback and raises, which is the visible failure.
    plausible = [
        v
        for v in matches
        if _MIN_PLAUSIBLE_CVD <= v <= _MAX_PLAUSIBLE_CVD and abs(v - WALLONIA_CVA_EUR_PER_M3) > 1e-9
    ]
    if plausible:
        return max(plausible)
    # Every match fell outside the plausibility window. Surface the
    # failure rather than silently emitting whichever value happened
    # to come first; a stale/cached/garbage page would otherwise let
    # an example-only figure ride into pricing and downstream sensors.
    raise ExtractorError(
        f"no plausible CVD on the page (matches outside [{_MIN_PLAUSIBLE_CVD}, "
        f"{_MAX_PLAUSIBLE_CVD}]: {matches!r})"
    )


# The phrasings these pages date themselves with. CILE heads its table
# "au 1er janvier YYYY", INASEP and the Callmepower pages use "Tarifs
# YYYY" / "en YYYY".
_PUBLISHED_YEAR_RES = (
    re.compile(r"tarifs?\s+(20\d\d)", re.IGNORECASE),
    re.compile(r"1\s*er\s+janvier\s+(20\d\d)", re.IGNORECASE),
    re.compile(r"\ben\s+(20\d\d)", re.IGNORECASE),
)


def detect_published_year(text: str, *, today: date | None = None) -> int | None:
    """The tariff year the page states, or ``None`` if it states none.

    Stamping the clock's year instead meant a page still publishing last
    year's rate was dated as current, so the snapshot never looked stale
    and nothing downstream could tell. Years far from today are ignored:
    these pages carry historic references and archive links, and only a
    year adjacent to now can be the one in force.
    """
    now = (today or belgian_today()).year
    # The patterns are tried in order of how much they say. "Tarifs YYYY"
    # names the card; "1er janvier YYYY" dates a rate on it, and the SPGE
    # lines an INASEP page keeps under a new "Tarifs" heading still carry
    # last year's date, so it counts only when no heading names the card.
    # A bare "en YYYY" is prose and counts only when nothing better is on
    # the page, otherwise a forward-looking sentence ("prochaine
    # indexation en 2027") would date the card a year ahead of the rate
    # it carries.
    for pattern in _PUBLISHED_YEAR_RES:
        found = {int(match.group(1)) for match in pattern.finditer(text)}
        plausible = [year for year in found if now - 1 <= year <= now + 1]
        if not plausible:
            continue
        # The year in force wins over one merely announced. Taking the
        # largest meant a page that names next year's card alongside the
        # one it is actually billing dated the rate a year ahead, so a
        # card that had gone stale never looked it. The current year is
        # the answer whenever the page names it; failing that the largest,
        # which is how a December page naming only next year is read.
        return now if now in plausible else max(plausible)
    return None


def build_tariff(
    *,
    utility_id: str,
    cvd: float,
    source_url: str,
    publication_label: str,
    year: int,
    valid_from: date | None = None,
) -> WaterTariff:
    """Build a Walloon :class:`WaterTariff` from the parsed CVD.

    Materialises the redevance as ``20·CVD + 30·CVA`` and pulls CVA /
    FSE from the SPGE flat-Wallonia constants. ``valid_from`` dates a
    rate that took effect inside ``year``; it defaults to 1 January,
    which is when the CWaPE cards normally turn over. A card dated last
    year, a page not yet updated in January, stands until 31 March like
    every other utility's, rather than counting as stale from the first
    day of the year.
    """
    if not _MIN_PLAUSIBLE_CVD <= cvd <= _MAX_PLAUSIBLE_CVD:
        # The shared page scan applies this window; the four extractors
        # that read the CVD off their own table did not, and a zero cell
        # went out as a card whose cost sensors then showed nothing.
        raise ExtractorError(
            f"{utility_id} CVD {cvd} is outside [{_MIN_PLAUSIBLE_CVD}, {_MAX_PLAUSIBLE_CVD}]"
        )
    cva = WALLONIA_CVA_EUR_PER_M3
    fse = WALLONIA_FSE_EUR_PER_M3
    redevance = 20.0 * cvd + 30.0 * cva
    tariff = WaterTariff(
        utility=utility_id,
        region=REGION_WALLONIA,
        valid_from=valid_from or date(year, 1, 1),
        valid_until=date(year, 12, 31),
        publication_label=publication_label,
        source_url=source_url,
        yearly_fixed_fee=redevance,
        cvd_eur_per_m3=cvd,
        cva_eur_per_m3=cva,
        fse_eur_per_m3=fse,
        vat_rate=DEFAULT_VAT_RATE,
    )
    return carry_prior_year_card(tariff, belgian_today().year)


def parse_tariff(
    html: str,
    *,
    utility_id: str,
    source_url: str,
    label_prefix: str,
    year: int | None = None,
) -> WaterTariff:
    """One-call parser for any of the small Walloon intercommunales."""
    cvd = parse_cvd(html)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    check_spge_constants(text, utility_id=utility_id, logger=_LOGGER)
    target = year or detect_published_year(text) or belgian_today().year
    return build_tariff(
        utility_id=utility_id,
        cvd=cvd,
        source_url=source_url,
        publication_label=f"{label_prefix} {target}",
        year=target,
        valid_from=effective_date(text, target),
    )


# AIEM prints the day its CVD took effect next to the value:
# "Valeur actuelle du CVD : 2,87€ HTVA 6% (à partir du 01/02/2025)".
_EFFECTIVE_FROM_RE = re.compile(
    r"actuelle\s+du\s+CVD[^()]{0,60}\(\s*à\s+partir\s+du\s+(\d{1,2})/(\d{1,2})/(20\d\d)\s*\)",
    re.IGNORECASE,
)


def effective_date(text: str, year: int) -> date | None:
    """The day the page says its CVD took effect, when that day is in ``year``.

    A date in an earlier year is the previous change and says nothing
    about this card; a date this year moves valid_from off 1 January,
    the way the INASEP parser already dates a mid-year revision.
    """
    match = _EFFECTIVE_FROM_RE.search(text)
    if match is None or int(match.group(3)) != year:
        return None
    try:
        return date(year, int(match.group(2)), int(match.group(1)))
    except ValueError:
        return None


async def fetch_tariff(
    session: aiohttp.ClientSession,
    *,
    utility_id: str,
    source_url: str,
    label_prefix: str,
) -> WaterTariff:
    """Async fetch + parse for a small-Walloon utility."""
    return await fetch_and_parse(
        session,
        source_url,
        parse_tariff,
        utility_id=utility_id,
        source_url=source_url,
        label_prefix=label_prefix,
    )


def build_extractor(
    *,
    utility_id: str,
    label: str,
    source_url: str,
    publication_label_prefix: str,
) -> WaterExtractor:
    """Return a fully-wired :class:`WaterExtractor` for a small-Walloon utility."""

    async def _fetch(session: aiohttp.ClientSession) -> WaterTariff:
        return await fetch_tariff(
            session,
            utility_id=utility_id,
            source_url=source_url,
            label_prefix=publication_label_prefix,
        )

    return WaterExtractor(
        id=utility_id,
        label=label,
        region=REGION_WALLONIA,
        fetch=_fetch,
    )
