"""What tells one config entry apart from another."""

from __future__ import annotations

import hashlib


def entry_unique_id(base_url: str, api_key: str) -> str:
    """The unique id for an entry that talks to this endpoint with this key.

    Neither value is the id itself. A unique id lands in the entity registry, and
    the key is a credential.

    The endpoint is part of it for two reasons. A key means something only at the
    endpoint that issued it, so the same string at two endpoints is two different
    credentials. And an endpoint that needs no key leaves the key empty: hashing
    the key alone gave every keyless endpoint one id, so a second one could never
    be added.

    What that costs: the same key at two endpoints is now two entries, each with
    its own daily budget, so that key can spend twice what one budget allows.
    """
    return hashlib.sha256(f"{base_url}\n{api_key}".encode()).hexdigest()[:16]
