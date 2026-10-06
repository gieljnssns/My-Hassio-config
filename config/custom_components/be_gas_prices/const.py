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

"""Constants for the Belgian Gas Prices integration.

No supplier prices live here: every rate comes from a live tariff card. The
few regulated figures that do are set by law for the whole country, carry the
months they are known to cover, and expire into "read the card" past them.
"""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "be_gas_prices"

PLATFORMS: Final = ("sensor", "button")

REGION_FLANDERS: Final = "flanders"
REGION_WALLONIA: Final = "wallonia"
REGION_BRUSSELS: Final = "brussels"

REGIONS: Final = (REGION_FLANDERS, REGION_WALLONIA, REGION_BRUSSELS)

# Canonical gas DSO keys. Stable forever: stored verbatim in every entry's
# CONF_DSO and used as the keys of SupplierSnapshot.dsos, so renaming one
# would silently break every entry on it. The eight Fluvius areas are the ones
# that exist since the 1 January 2025 merger; the names they replaced
# (Gaselwest, Iveka, Iverlek, Sibelgas, Intergem) carry no tariff any more.
DSO_FLUVIUS_ANTWERPEN: Final = "fluvius_antwerpen"
DSO_FLUVIUS_HALLE_VILVOORDE: Final = "fluvius_halle_vilvoorde"
DSO_FLUVIUS_IMEWO: Final = "fluvius_imewo"
DSO_FLUVIUS_KEMPEN: Final = "fluvius_kempen"
DSO_FLUVIUS_LIMBURG: Final = "fluvius_limburg"
DSO_FLUVIUS_MIDDEN_VLAANDEREN: Final = "fluvius_midden_vlaanderen"
DSO_FLUVIUS_WEST: Final = "fluvius_west"
DSO_FLUVIUS_ZENNE_DIJLE: Final = "fluvius_zenne_dijle"

# One key for ORES. Its five gas sub-areas (Brabant wallon, Hainaut, Luxembourg,
# Mouscron, Namur) are billed one tariff: "Les differents tarifs sont uniformes
# sur le territoire du gestionnaire de reseau de distribution" (CWaPE decision
# CD-24k29-CWaPE-1008). The cards still print a row per sub-area, and the
# readers require those rows to agree before they collapse them.
DSO_ORES: Final = "ores"
DSO_RESA: Final = "resa"

DSO_SIBELGA: Final = "sibelga"

FLUVIUS_KEYS: Final[frozenset[str]] = frozenset(
    {
        DSO_FLUVIUS_ANTWERPEN,
        DSO_FLUVIUS_HALLE_VILVOORDE,
        DSO_FLUVIUS_IMEWO,
        DSO_FLUVIUS_KEMPEN,
        DSO_FLUVIUS_LIMBURG,
        DSO_FLUVIUS_MIDDEN_VLAANDEREN,
        DSO_FLUVIUS_WEST,
        DSO_FLUVIUS_ZENNE_DIJLE,
    }
)
WALLONIA_DSO_KEYS: Final[frozenset[str]] = frozenset({DSO_ORES, DSO_RESA})
BRUSSELS_DSO_KEYS: Final[frozenset[str]] = frozenset({DSO_SIBELGA})

REGION_DSO_KEYS: Final[dict[str, frozenset[str]]] = {
    REGION_FLANDERS: FLUVIUS_KEYS,
    REGION_WALLONIA: WALLONIA_DSO_KEYS,
    REGION_BRUSSELS: BRUSSELS_DSO_KEYS,
}

# DSO selection per region, in the order the setup flow lists them.
DSO_CHOICES: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    REGION_FLANDERS: (
        (DSO_FLUVIUS_ANTWERPEN, "Fluvius Antwerpen"),
        (DSO_FLUVIUS_HALLE_VILVOORDE, "Fluvius Halle-Vilvoorde"),
        (DSO_FLUVIUS_IMEWO, "Fluvius Imewo"),
        (DSO_FLUVIUS_KEMPEN, "Fluvius Kempen"),
        (DSO_FLUVIUS_LIMBURG, "Fluvius Limburg"),
        (DSO_FLUVIUS_MIDDEN_VLAANDEREN, "Fluvius Midden-Vlaanderen"),
        (DSO_FLUVIUS_WEST, "Fluvius West"),
        (DSO_FLUVIUS_ZENNE_DIJLE, "Fluvius Zenne-Dijle"),
    ),
    REGION_WALLONIA: (
        (DSO_ORES, "ORES"),
        (DSO_RESA, "RESA"),
    ),
    REGION_BRUSSELS: ((DSO_SIBELGA, "Sibelga"),),
}

# The distribution tariff's consumption tiers, in kWh a year, upper bounds
# inclusive. Set by the regulators alike in all three regions and applied
# NON-cumulatively: the tier the annual volume falls in prices every kWh of
# it ("de maniere non-cumulative, a l'ensemble des kWh", CWaPE). A structure,
# not a price, which is why it lives here. T4 and above are remotely read
# industrial connections no residential card prices.
TIER_T1: Final = "t1"
TIER_T2: Final = "t2"
TIER_T3: Final = "t3"
TIER_BOUNDS_KWH: Final[tuple[tuple[str, float], ...]] = (
    (TIER_T1, 5_000.0),
    (TIER_T2, 150_000.0),
    (TIER_T3, 1_000_000.0),
)

# The federal special excise on residential gas is billed per consumption
# slice on the annual volume ("tarief per verbruiksschijf, berekend op
# jaarbasis", art. 419 g) of the programme law of 27 December 2004): the first
# 12 000 kWh at one rate, the rest at the other.
EXCISE_BAND_KWH: Final = 12_000.0

# The residential special excise the programme law of 30 May 2026 set from
# 1 August 2026, in EUR/kWh EXCLUDING VAT (10,31 and 11,16 EUR/MWh), and the
# months it is known to cover. A federal levy: one rate for the whole country,
# so a card printing another one for a delivery month in this window is stale
# rather than different. Ecofix, Sparki, Belvus and the six Energy Together
# brands still printed the pre-August figures in September 2026.
#
# Only a rate IN EFFECT belongs here. The same law steps the rate up again on
# 1 January 2027, 2028 and 2029, and the quarterly adjustment of art. 420
# still applies on top, so encoding the schedule ahead would bill a
# prediction. Past the end of the window the card is read as before.
GAS_EXCISE_RESIDENTIAL_HTVA: Final[tuple[float, float]] = (0.01031, 0.01116)
GAS_EXCISE_KNOWN_FROM: Final = (2026, 8)
GAS_EXCISE_KNOWN_UNTIL: Final = (2027, 1)  # exclusive

# The Fluvius data management fee for a yearly-read gas meter ("Jaaropname
# (o.a. digitale gasmeter G4 en G6)"), in EUR/year EXCLUDING VAT: one figure
# for all eight areas in the 2026 tariff lists (valid 1 January to 31 December
# 2026), which every Flemish card prints as 18,92 including VAT but Luminus's,
# which prints none. The DSO bills it for every connection whatever the
# supplier, so a Flemish card without it is short of it rather than exempt,
# and this stands in only there. Same discipline as the excise: the window is
# the tariff year, and past it the card is read as before.
FLUVIUS_DATA_MANAGEMENT_HTVA: Final = 17.85
FLUVIUS_DATA_MANAGEMENT_KNOWN_FROM: Final = (2026, 1)
FLUVIUS_DATA_MANAGEMENT_KNOWN_UNTIL: Final = (2027, 1)  # exclusive

# The Walloon connection fee on gas ("redevance de raccordement", art. 40 of
# the gas decree of 19 December 2002), in EUR/kWh and exempt from VAT. The
# Walloon government's order of 19 June 2003 (art. 2) sets 0,0075 EUR for the
# first 100 kWh of a year and 0,000075 EUR/kWh after that below 1 GWh a year,
# which is 0,000075 EUR/kWh throughout. The same article sets 0,00075 EUR/kWh
# for low-voltage electricity, the figure EnergyVision's September 2026
# Walloon gas cards print instead. In force since 15 July 2003, art. 2 never
# amended. The window ends where the other regulated figures are next checked,
# and past it the card is read as before.
WALLOON_CONNECTION_FEE: Final = 0.000075
WALLOON_CONNECTION_FEE_KNOWN_FROM: Final = (2003, 7)
WALLOON_CONNECTION_FEE_KNOWN_UNTIL: Final = (2027, 1)  # exclusive

# The month the federal energy contribution on residential gas stopped being
# levied: the same law set it to zero from 1 August 2026. Compared against the
# DELIVERY month, since the levy is law rather than a contract term.
ENERGY_CONTRIBUTION_ZEROED_FROM: Final = (2026, 8)

# Belgian VAT on residential gas (Royal Decree nr. 20, table A, XIV).
VAT_RATE_REDUCED: Final = 0.06

# Brussels per-meter levy (gas ordinance of 1 April 2004, art.
# 20septiesdecies): a yearly amount by meter caliber in m3/h, and for the
# smallest caliber by whether the standardised annual consumption is above
# 5 000 kWh. The keys are what an entry stores; the amounts come off the card.
CALIBER_Q10: Final = "q10"
CALIBER_Q16: Final = "q16"
CALIBER_Q25: Final = "q25"
CALIBER_Q40: Final = "q40"
CALIBER_Q65: Final = "q65"
CALIBER_Q100: Final = "q100"
CALIBER_Q160: Final = "q160"
CALIBER_GT160: Final = "gt160"
CALIBERS: Final = (
    CALIBER_Q10,
    CALIBER_Q16,
    CALIBER_Q25,
    CALIBER_Q40,
    CALIBER_Q65,
    CALIBER_Q100,
    CALIBER_Q160,
    CALIBER_GT160,
)
DEFAULT_CALIBER: Final = CALIBER_Q10
# The smallest caliber's split, as the levy table keys it.
OSP_Q10_LOW: Final = "q10_le5000"
OSP_Q10_HIGH: Final = "q10_gt5000"
OSP_Q10_SPLIT_KWH: Final = 5_000.0

CONF_POSTCODE: Final = "postcode"
CONF_REGION: Final = "region"
CONF_DSO: Final = "dso"
CONF_SUPPLIER: Final = "supplier"
CONF_CONTRACT: Final = "contract"
CONF_CALIBER: Final = "caliber"

# Estimated yearly consumption in kWh. It picks the distribution tier and
# the excise slices until the meter has measured a year, which then wins. The
# default is the 17 000 kWh household the CREG prices its reference offers on
# (note Z3308).
CONF_ANNUAL_CONSUMPTION_KWH: Final = "annual_consumption_kwh"
DEFAULT_ANNUAL_CONSUMPTION_KWH: Final = 17_000.0

# The household's gas meter: a cumulative sensor in m3 or in kWh.
CONF_GAS_METER: Final = "gas_meter"

# How a volume in m3 becomes energy in kWh. "manual" takes the factor printed
# on the household's bill, which carries the DSO's correction for the pressure
# and temperature at the meter, and comes first; "station" reads the monthly
# gross calorific value of one gas reception station from Atrias, per normal
# cubic metre, without that correction.
CONF_CONVERSION_MODE: Final = "conversion_mode"
CONVERSION_STATION: Final = "station"
CONVERSION_MANUAL: Final = "manual"
CONVERSION_MODES: Final = (CONVERSION_MANUAL, CONVERSION_STATION)
DEFAULT_CONVERSION_MODE: Final = CONVERSION_MANUAL
CONF_STATION: Final = "station"
CONF_CONVERSION_FACTOR: Final = "conversion_factor"

CONF_CONTRACT_START_DATE: Final = "contract_start_date"
CONF_CONTRACT_END_DATE: Final = "contract_end_date"
CONF_TARIFF_CARD_DATE: Final = "tariff_card_date"
CONF_YTD_FROM_CONTRACT_START: Final = "ytd_from_contract_start"

# The figures a household signed at, typed from its own contract, for when the
# signing month's card cannot be read or the offer had figures of its own. A
# fixed contract takes a price, an indexed one the factor and base of its
# formula; both may take the yearly fee. Price and base in c EUR/kWh, the
# factor in c EUR/kWh per EUR/MWh of index, all excluding VAT as formulas are
# printed; the fee in EUR a year including VAT, as cards print fees.
CONF_MANUAL_PRICE: Final = "manual_price"
CONF_MANUAL_FACTOR: Final = "manual_factor"
CONF_MANUAL_BASE: Final = "manual_base"
CONF_MANUAL_FEE: Final = "manual_fee"
MANUAL_RATE_KEYS: Final = (CONF_MANUAL_PRICE, CONF_MANUAL_FACTOR, CONF_MANUAL_BASE, CONF_MANUAL_FEE)
CONF_PREVIOUS_CONTRACTS: Final = "previous_contracts"
CONF_SWITCH_DATE: Final = "switch_date"

# Whether this entry may read the card archive (CARD_ARCHIVE_URL) for a past
# month its supplier no longer serves. Off keeps the integration from
# contacting GitHub at all.
CONF_CARD_ARCHIVE: Final = "card_archive"
DEFAULT_CARD_ARCHIVE: Final = True

CONF_DAILY_COMPARE: Final = "daily_compare"
DEFAULT_DAILY_COMPARE: Final = False

# The coordinator ticks hourly: a cheap probe decides whether a card is
# fetched again, and the running costs follow the meter.
UPDATE_INTERVAL_MINUTES: Final = 60

STORAGE_VERSION: Final = 1

# The card archive, in the shared be_price_cards repository beside the cards
# themselves: one small JSON per (supplier, contract, region, month), written
# daily by .github/workflows/archive_cards.yml.
CARD_ARCHIVE_URL: Final = (
    "https://raw.githubusercontent.com/renaudallard/be_price_cards/main/gas/cards"
)

# Atrias publishes the monthly gross calorific value of every gas reception
# station in Belgium. The API wants the public subscription key its own site
# carries in runtime-config.js, read at run time rather than copied here.
ATRIAS_CONFIG_URL: Final = "https://www.atrias.be/runtime-config.js"
ATRIAS_API_URL: Final = "https://api.atrias.be/roots"

# A metered window stands as a yearly volume when it covers a year, up to
# MEASURED_YEAR_GAP_DAYS missing days scaled across; a shorter one does not.
MEASURED_FULL_YEAR_DAYS: Final = 365
MEASURED_YEAR_GAP_DAYS: Final = 15

# --- Expert custom supplier ----------------------------------------------------
# For a product with no public card (a group purchase, a supplier this
# integration does not read): the household types its own price and the
# regulated figures of its DSO, VAT inclusive as cards print them, and the
# snapshot is built from the entry instead of fetched. Listed last among the
# suppliers and never ranked, since there is no card to compare.
SUPPLIER_CUSTOM: Final = "custom"
CUSTOM_CONTRACT: Final = "custom_fixed"
CONF_CUSTOM_PRICE: Final = "custom_price"
CONF_CUSTOM_FEE: Final = "custom_fee"
CONF_CUSTOM_T1_FIXED: Final = "custom_t1_fixed"
CONF_CUSTOM_T1_PROP: Final = "custom_t1_prop"
CONF_CUSTOM_T2_FIXED: Final = "custom_t2_fixed"
CONF_CUSTOM_T2_PROP: Final = "custom_t2_prop"
CONF_CUSTOM_TRANSPORT: Final = "custom_transport"
CONF_CUSTOM_METERING: Final = "custom_metering"
CONF_CUSTOM_EXCISE_LOW: Final = "custom_excise_low"
CONF_CUSTOM_EXCISE_HIGH: Final = "custom_excise_high"
CONF_CUSTOM_CONTRIBUTION: Final = "custom_contribution"
CONF_CUSTOM_CONNECTION_FEE: Final = "custom_connection_fee"
CONF_CUSTOM_LEVY: Final = "custom_levy"
CUSTOM_KEYS: Final = (
    CONF_CUSTOM_PRICE,
    CONF_CUSTOM_FEE,
    CONF_CUSTOM_T1_FIXED,
    CONF_CUSTOM_T1_PROP,
    CONF_CUSTOM_T2_FIXED,
    CONF_CUSTOM_T2_PROP,
    CONF_CUSTOM_TRANSPORT,
    CONF_CUSTOM_METERING,
    CONF_CUSTOM_EXCISE_LOW,
    CONF_CUSTOM_EXCISE_HIGH,
    CONF_CUSTOM_CONTRIBUTION,
    CONF_CUSTOM_CONNECTION_FEE,
    CONF_CUSTOM_LEVY,
)
