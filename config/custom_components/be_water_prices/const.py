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

"""Constants for be_water_prices."""

from __future__ import annotations

import json
from pathlib import Path

DOMAIN = "be_water_prices"


def _read_version() -> str:
    """This release's version, straight from the manifest.

    Read here rather than in each place that wants it: the User-Agent
    every fetch sends and the key the running bill's floor is measured
    under are both this number, and two readers would drift.
    """
    manifest = Path(__file__).resolve().parent / "manifest.json"
    try:
        return str(json.loads(manifest.read_text(encoding="utf-8")).get("version", "0"))
    except (OSError, ValueError):
        return "0"


INTEGRATION_VERSION = _read_version()

REGION_FLANDERS = "flanders"
REGION_WALLONIA = "wallonia"
REGION_BRUSSELS = "brussels"
REGIONS: tuple[str, ...] = (REGION_FLANDERS, REGION_WALLONIA, REGION_BRUSSELS)

# Daily refresh; tariffs change once a year so anything tighter is wasted work.
UPDATE_INTERVAL_HOURS = 24

# The project's own daily capture of every utility's card, one JSON per
# utility, commune and month on the archive branch (scripts/archive_cards.py
# writes it). Read when a refresh fails with nothing to serve, a restart
# while the utility is down, and again once what is held has gone stale, so
# the entry loads on the last card the archive saw instead of retrying setup
# until the utility is back, and keeps up with the archive while it stays
# away.
CARD_ARCHIVE_URL = (
    "https://raw.githubusercontent.com/renaudallard/homeassistant_be_water_prices/archive"
)

# Treat the snapshot as stale once it has not been refreshed for this many days
# OR the parsed valid_until is in the past. Surfaced as a sensor attribute and
# logged; persistent failure is caught by the daily live_check workflow.
SNAPSHOT_STALE_AFTER_DAYS = 35

# Wallonia uses two flat-Wallonia volumetric components on top of each
# distributor's CVD. Both come from SPGE / CWaPE, not from the distributor's
# own publication, so they live here. Source: SPGE / CWaPE annual rate
# decision, mirrored on each Walloon distributor's tariff page.
WALLONIA_CVA_EUR_PER_M3 = 2.748
WALLONIA_FSE_EUR_PER_M3 = 0.0339

# Standard Belgian residential VAT rate on water.
DEFAULT_VAT_RATE = 0.06

# Standard VMM "integrale waterprijs" vastrecht structure for Flanders.
# Mandated by the Vlaamse regering since 2016 and uniform across operators
# (De Watergroep, Pidpa, Farys, Water-link, Aquaduin, AGSO Knokke). Each
# component is split into its own line on the bill but the operator-side
# numbers are identical, so we keep one source of truth here.
FLANDERS_VASTRECHT_DRINKWATER = 50.0
FLANDERS_VASTRECHT_GEMEENTELIJK = 30.0
FLANDERS_VASTRECHT_BOVENGEMEENTELIJK = 20.0
FLANDERS_VASTRECHT_TOTAL = (
    FLANDERS_VASTRECHT_DRINKWATER
    + FLANDERS_VASTRECHT_GEMEENTELIJK
    + FLANDERS_VASTRECHT_BOVENGEMEENTELIJK
)
FLANDERS_KORTING_DRINKWATER_PER_PERSON = 10.0
FLANDERS_KORTING_GEMEENTELIJK_PER_PERSON = 6.0
FLANDERS_KORTING_BOVENGEMEENTELIJK_PER_PERSON = 4.0
FLANDERS_KORTING_TOTAL_PER_PERSON = (
    FLANDERS_KORTING_DRINKWATER_PER_PERSON
    + FLANDERS_KORTING_GEMEENTELIJK_PER_PERSON
    + FLANDERS_KORTING_BOVENGEMEENTELIJK_PER_PERSON
)

# Config / option keys.
CONF_UTILITY = "utility"
CONF_POSTCODE = "postcode"
CONF_CONSUMPTION_M3_PER_YEAR = "consumption_m3_per_year"
CONF_PERSONS = "gedomicilieerd_persons"
CONF_SOCIAL_TARIFF = "social_tariff"
CONF_WATER_METER_SENSOR = "water_meter_sensor"
CONF_COMMUNE = "commune"
CONF_COMMUNE_LABEL = "commune_label"
# Whether that archive may be asked at all. The request names the utility
# and the commune id, so it is a switch, on by default.
CONF_CARD_ARCHIVE = "card_archive"
DEFAULT_CARD_ARCHIVE = True

DEFAULT_CONSUMPTION_M3 = 80
MIN_CONSUMPTION_M3 = 1
MAX_CONSUMPTION_M3 = 2000
DEFAULT_PERSONS = 1
# Registered residents drive two separate things, and only one of them
# is capped. The basisvolume is 30 m3 per wooneenheid plus 30 m3 per
# gedomicilieerde with no maximum, so a bound of 5 understated the free
# block for a larger household and overstated its bill. The korting on
# the vastrecht IS capped at 5, but the decree phrases that cap as "the
# total korting can never exceed the vastrecht charged", which the
# max(0.0, ...) in pricing.py already enforces: at the decreed uniform
# 100 EUR vastrecht and 20 EUR per resident, the fifth person zeroes it.
#
# So these two only bound what a person can sensibly type. Zero is a
# real answer -- a second home, or a rental between tenants.
MIN_PERSONS = 0
MAX_PERSONS = 20

# How far the configured yearly consumption has to sit from a whole year
# the meter actually measured before we offer to replace it. A household
# varies from year to year without the projection being wrong, so the
# prompt is for a figure that was never right rather than for weather.
PROJECTION_DRIFT_RATIO = 0.10
