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

"""AIEC -- Association Intercommunale des Eaux du Condroz.

Tiny operator covering parts of the Condroz region. AIEC publishes its
card only as a picture: ``Prix.htm`` embeds a JPEG whose name carries
the day the card took effect (``Tarif-2026-04-1-<cms hash>.jpg``). The
rate inside it cannot be read without OCR, so the CVD still comes from
the Callmepower aggregator.

An aggregator can be wrong, and a drift check cannot tell: it compares
the parser against its own source, so a source that is itself wrong
reads as green. On 1 April 2026 AIEC moved its CVD to 3,050 and
Callmepower stayed on 2,460, under-stating an 80 m3 bill by 53 EUR a
year with nothing to show for it.

The picture's contents cannot be read by a machine, but they can be read
by a person, and its file name carries the day the card took effect. So
the rate on each card is transcribed here against that date. While
AIEC's page still shows the card we transcribed, that is what is served,
and the aggregator is not consulted at all.

A card we have not transcribed, or an unreadable operator page, falls
back to the aggregator dated from the picture. That is the only thing
that can be done with a number nobody has read yet, and it says so in
the log. Refusing instead does not work: it was tried, and it took every
AIEC entry dark while stopping a fresh one from finishing setup.

Transcribing a rate is the one place in this integration where a
per-distributor number is not fetched. It earns the exception because
the alternative was measured: the aggregator sat on 2,460 for the five
months after AIEC moved to 3,050, which under-billed an 80 m3 household
by 53.16 EUR a year with nothing anywhere to show it.

Sources: https://callmepower.be/fr/eau/distributeurs/aiec
         http://www.eauxducondroz.be/Prix.htm
"""

from __future__ import annotations

import dataclasses
import logging
import re
from datetime import date

import aiohttp

from ..const import REGION_WALLONIA
from ._html import fetch_html
from ._walloon_simple import build_extractor, build_tariff
from ._walloon_simple import parse_tariff as _parse_tariff
from .base import ExtractorError, TransientFetchError, WaterExtractor, WaterTariff

_LOGGER = logging.getLogger(__name__)

UTILITY_ID = "aiec"
LABEL = "AIEC"
SOURCE_URL = "https://callmepower.be/fr/eau/distributeurs/aiec"
_LABEL_PREFIX = "AIEC tarifs (via Callmepower)"


def parse_tariff(html: str, year: int | None = None) -> WaterTariff:
    return _parse_tariff(
        html,
        utility_id=UTILITY_ID,
        source_url=SOURCE_URL,
        label_prefix=_LABEL_PREFIX,
        year=year,
    )


# The operator's own page, and the card picture it embeds. The trailing
# hash is the CMS dedupe suffix, as on the Water-link and Aquaduin links.
OPERATOR_URL = "http://www.eauxducondroz.be/Prix.htm"
_CARD_IMAGE_RE = re.compile(
    r"Tarif-(20\d\d)-(\d{1,2})-(\d{1,2})[^\"'>]*\.jpe?g",
    re.IGNORECASE,
)


# The rate each card prints, keyed by the day it took effect, which is
# the day its picture's file name carries. Read off the picture by hand;
# add a line when AIEC publishes a new one. A date that is not here is a
# card nobody has read, and the aggregator stands in for it.
_TRANSCRIBED_CVD: dict[date, float] = {
    # "STRUCTURE TARIFAIRE DE L'EAU AU 01/04/2026", CVD: 3,050 EUR. The
    # same card's own per-inhabitant table (233 / 449 / 665 / 882 / 1.098
    # / 1.314 / 1.531 EUR) is reproduced to within rounding by this
    # figure and by no other.
    date(2026, 4, 1): 3.050,
}


def card_from_operator_page(html: str) -> WaterTariff | None:
    """The card AIEC's page is showing, when its rate has been transcribed.

    ``None`` when the page shows a card that is not in the table above,
    which is the caller's cue to fall back to the aggregator.
    """
    published = published_card_date(html)
    if published is None:
        return None
    cvd = _TRANSCRIBED_CVD.get(published)
    if cvd is None:
        return None
    return build_tariff(
        utility_id=UTILITY_ID,
        cvd=cvd,
        source_url=OPERATOR_URL,
        publication_label=f"AIEC tarifs au {published.strftime('%d/%m/%Y')}",
        year=published.year,
        valid_from=published,
    )


def published_card_date(html: str) -> date | None:
    """The day the newest card picture on AIEC's page took effect.

    ``None`` when the page carries no card whose name states a date, which
    is not a reason to refuse the aggregator: it is the state the page was
    in before AIEC started dating its pictures.
    """
    dates = []
    for match in _CARD_IMAGE_RE.finditer(html):
        try:
            dates.append(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
        except ValueError:
            continue
    return max(dates) if dates else None


def date_against_operator(tariff: WaterTariff, html: str) -> WaterTariff:
    """Date the aggregator card from the operator's own card picture.

    The aggregator prints no effective date, so :func:`build_tariff` stamps
    every card 1 January. The operator's picture is dated, and when it is
    dated later in the same year that is the day the rate it carries took
    effect, so the card is re-dated to it.

    That is all this can do. Comparing the two dates and refusing the
    mismatch, which is what this did first, cannot work: the aggregator
    card is 1 January by construction, so the refusal could never be
    cleared by the aggregator catching up, only by the next 1 January.
    Every AIEC entry went dark, and a fresh one could not finish setup.

    Re-dating instead leaves the household with a working entry whose
    ``valid_from`` says which card it is on, and hands the staleness
    machinery something real to work with.
    """
    published = published_card_date(html)
    if published is None or published <= tariff.valid_from:
        return tariff
    if published.year != tariff.valid_from.year:
        # A picture from another year says nothing about this card.
        return tariff
    _LOGGER.info(
        "AIEC published a card effective %s; dating the %s card to it. The rate "
        "itself cannot be read from %s, which publishes it as a picture, so it "
        "is still the aggregator's",
        published.isoformat(),
        SOURCE_URL,
        OPERATOR_URL,
    )
    return dataclasses.replace(tariff, valid_from=published)


async def fetch(session: aiohttp.ClientSession) -> WaterTariff:
    try:
        html = await fetch_html(session, OPERATOR_URL)
    except TransientFetchError:
        # The rate lives on this page now, so a DNS blip or a 5xx must not
        # quietly swap it for the aggregator's, which was 53 EUR a year
        # short the last time the two disagreed. Let it through: an entry
        # that already has a card keeps serving it behind the ordinary
        # stale-snapshot machinery, and a fresh one retries.
        raise
    except ExtractorError as err:
        # Not a blip: the page has moved or stopped being a page. There is
        # then no way to tell which card is on screen, and the aggregator
        # standing in undated is better than nothing at all.
        _LOGGER.warning("could not read %s: %s; serving %s", OPERATOR_URL, err, SOURCE_URL)
        return await _fetch_aggregator(session)
    transcribed = card_from_operator_page(html)
    if transcribed is not None:
        return transcribed
    published = published_card_date(html)
    if published is not None:
        _LOGGER.warning(
            "AIEC published a card effective %s whose rate this release does not carry; "
            "serving %s until it does, which was 53.16 EUR a year short the last time "
            "the two disagreed",
            published.isoformat(),
            SOURCE_URL,
        )
    tariff = await _fetch_aggregator(session)
    return date_against_operator(tariff, html)


_fetch_aggregator = build_extractor(
    utility_id=UTILITY_ID,
    label=LABEL,
    source_url=SOURCE_URL,
    publication_label_prefix=_LABEL_PREFIX,
).fetch

EXTRACTOR = WaterExtractor(
    id=UTILITY_ID,
    label=LABEL,
    region=REGION_WALLONIA,
    fetch=fetch,
)
