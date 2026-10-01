"""How big a request is, before it is sent.

The pre-flight budget check has to know what a call will cost while there is still
time to refuse it, and the only honest input is the body jevclient is about to
post. This builds the same dict and measures it.

jevclient owns the real one. tests/test_payload.py posts through a real JevClient
against a fake session and asserts the two byte counts match, so a shape change in
the library fails a test instead of quietly biasing every estimate.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from jevclient import Question


def payload_bytes(state: Any, questions: Mapping[str, Question], model: str) -> int:
    """The size of the request body in bytes, as it goes on the wire.

    json.dumps escapes non-ASCII by default and aiohttp serialises the same way,
    so an accented character counts as the six bytes it is sent as rather than the
    two it takes in UTF-8.
    """
    body = {
        "state": state,
        "model": model,
        "questions": {key: question.as_payload() for key, question in questions.items()},
    }
    return len(json.dumps(body).encode())
