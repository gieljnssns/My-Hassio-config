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

"""Per-operator phantom-entry blocklists (data-only, no heavy imports).

This module is intentionally stdlib-only so ``scripts/refresh_postcodes.py``
can import it from a fresh maintainer venv without pulling in
``aiohttp`` / ``bs4`` (which the parent ``providers`` package does at
import time). The runtime modules (``farys.py``, ``pidpa.py``)
re-export these constants under their existing names so existing
callers stay stable.
"""

from __future__ import annotations

# Farys: option labels that the dropdown carries but the AJAX endpoint
# returns no tariff data for (split postcodes where DWG is the actual
# operator). Key shape: "<postcode> - <commune> (<gemeente>)".
FARYS_UNSERVABLE_LABELS: frozenset[str] = frozenset(
    {
        "1500 - Halle (Halle)",
        "1700 - Dilbeek (Dilbeek)",
        "1701 - Itterbeek (Dilbeek)",
        "1702 - Groot-Bijgaarden (Dilbeek)",
        "1703 - Schepdaal (Dilbeek)",
        "1740 - Ternat (Ternat)",
        "1741 - Wambeek (Ternat)",
        "8020 - Hertsberge (Oostkamp)",
        "8020 - Ruddervoorde (Oostkamp)",
        "8020 - Waardamme (Oostkamp)",
        "8432 - Leffinge (Middelkerke)",
        "8450 - Bredene (Bredene)",
        "8490 - Snellegem (Jabbeke)",
        "8490 - Zerkegem (Jabbeke)",
        "9080 - Beervelde (Lochristi)",
        "9080 - Zaffelare (Lochristi)",
        "9080 - Zeveneken (Lochristi)",
        "9550 - Sint-Antelinks (Herzele)",
        "9550 - Sint-Lievens-Esse (Herzele)",
        "9550 - Steenhuize-Wijnhuize (Herzele)",
        "9550 - Woubrechtegem (Herzele)",
        "9570 - Deftinge (Lierde)",
        "9571 - Hemelveerdegem (Lierde)",
    }
)


# Same set as ``FARYS_UNSERVABLE_LABELS`` but keyed by the numeric
# option id Farys assigned at the time of the v0.5.x install. Used by
# ``async_migrate_entry`` to recognise and drop already-saved phantom
# commune ids from existing config entries when the user upgrades.
FARYS_UNSERVABLE_IDS: frozenset[str] = frozenset(
    {
        "25126",  # 1500 - Halle (Halle)
        "24956",  # 1700 - Dilbeek (Dilbeek)
        "24966",  # 1701 - Itterbeek (Dilbeek)
        "24961",  # 1702 - Groot-Bijgaarden (Dilbeek)
        "24971",  # 1703 - Schepdaal (Dilbeek)
        "25661",  # 1740 - Ternat (Ternat)
        "25666",  # 1741 - Wambeek (Ternat)
        "25521",  # 8020 - Hertsberge (Oostkamp)
        "25531",  # 8020 - Ruddervoorde (Oostkamp)
        "25536",  # 8020 - Waardamme (Oostkamp)
        "25411",  # 8432 - Leffinge (Middelkerke)
        "27251",  # 8450 - Bredene (Bredene)
        "25201",  # 8490 - Snellegem (Jabbeke)
        "25216",  # 8490 - Zerkegem (Jabbeke)
        "25316",  # 9080 - Beervelde (Lochristi)
        "25326",  # 9080 - Zaffelare (Lochristi)
        "25331",  # 9080 - Zeveneken (Lochristi)
        "25161",  # 9550 - Sint-Antelinks (Herzele)
        "25166",  # 9550 - Sint-Lievens-Esse (Herzele)
        "25171",  # 9550 - Steenhuize-Wijnhuize (Herzele)
        "25176",  # 9550 - Woubrechtegem (Herzele)
        "25291",  # 9570 - Deftinge (Lierde)
        "25301",  # 9571 - Hemelveerdegem (Lierde)
    }
)


# Pidpa: slugs that the sitemap lists but for which no huishoudelijk
# tariff table exists (Antwerpen is Water-link territory; Pidpa lists
# it for marketing reach).
PIDPA_UNSERVABLE_SLUGS: frozenset[str] = frozenset({"antwerpen"})
