"""Diagnostics. Users paste these into issues, so the key never appears."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

if TYPE_CHECKING:
    from . import JevConfigEntry

# async_redact_data matches keys exactly, so every spelling that can appear is listed.
TO_REDACT = {
    CONF_API_KEY,
    "api_key",
    "apikey",
    "authorization",
    "key",
    "token",
    "access_token",
}
# What a person said to the house, and where the house is. The state builder already
# keeps these attributes out of what it sends, so this covers a template that renders
# them anyway.
PRIVATE = {"text", "entity_picture", "latitude", "longitude", "gps_accuracy"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: JevConfigEntry
) -> dict[str, Any]:
    runtime = entry.runtime_data
    usage = runtime.usage
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "model_version": runtime.model_version,
        "usage_today": {
            "day": usage.day.isoformat(),
            "calls": usage.calls,
            "input_tokens": usage.input_tokens,
            "budget": usage.budget,
            "budget_exceeded": usage.budget_exceeded,
            "estimated_cost_usd": round(usage.estimated_cost, 6),
        },
        # What the conversation agent made of each sentence. The sentence itself is
        # redacted, because users paste this file into public issues.
        "conversation_traces": [
            async_redact_data(trace, PRIVATE) for trace in runtime.conversation_traces
        ],
        "contexts": [
            {
                "name": coordinator.context_config.name,
                "scan_interval_seconds": coordinator.context_config.scan_interval,
                "trigger_entities": coordinator.context_config.trigger_entities,
                "last_update_success": coordinator.last_update_success,
                "last_latency_ms": coordinator.last_latency_ms,
                # The rendered state is the first thing to look at when an answer
                # surprises someone, so it belongs here rather than in an attribute.
                "last_evaluated_state": async_redact_data(
                    coordinator.last_state_text, TO_REDACT | PRIVATE
                ),
                "questions": [
                    {
                        "key": question.key,
                        "name": question.name,
                        "type": question.kind,
                        "threshold": question.threshold,
                    }
                    for question in coordinator.context_config.questions
                ],
            }
            for coordinator in runtime.coordinators.values()
        ],
    }
