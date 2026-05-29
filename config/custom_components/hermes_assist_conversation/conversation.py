"""Conversation platform for Hermes Assist."""

from __future__ import annotations

from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers import intent
from homeassistant.util import ulid as ulid_util

from .const import CONF_API_KEY, CONF_URL, DEFAULT_NAME, DOMAIN, REQUEST_TIMEOUT


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Hermes Assist conversation entity."""
    async_add_entities([HermesAssistConversationEntity(config_entry)])


class HermesAssistConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """Hermes-backed Home Assistant conversation agent."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__()
        self.config_entry = config_entry
        self._attr_name = config_entry.data.get(CONF_NAME, DEFAULT_NAME)
        self._attr_unique_id = f"{config_entry.entry_id}-conversation"

    async def async_added_to_hass(self) -> None:
        """Register as a conversation agent."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.config_entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister as a conversation agent."""
        conversation.async_unset_agent(self.hass, self.config_entry)
        await super().async_will_remove_from_hass()

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return MATCH_ALL

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process a sentence through the Home Assistant Assist conversation API."""
        conversation_id = user_input.conversation_id or ulid_util.ulid_now()

        url = self.config_entry.data[CONF_URL].rstrip("/")
        api_key = self.config_entry.data[CONF_API_KEY]
        payload = {
            "text": user_input.text,
            "conversation_id": conversation_id,
            "language": user_input.language,
            "device_id": user_input.device_id,
            "satellite_id": user_input.satellite_id,
            "extra_system_prompt": user_input.extra_system_prompt,
            "chat_log": chat_log.as_dict(),
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        session = async_get_clientsession(self.hass)

        try:
            async with session.post(
                f"{url}/api/chat", json=payload, headers=headers, timeout=REQUEST_TIMEOUT
            ) as resp:
                data = await resp.json(content_type=None)
                reply = data.get("reply") or data.get("error") or "Hermes returned no response."
                if resp.status >= 400:
                    intent_response = intent.IntentResponse(language=user_input.language)
                    intent_response.async_set_error(
                        intent.IntentResponseErrorCode.FAILED_TO_HANDLE, str(reply)
                    )
                    return conversation.ConversationResult(
                        response=intent_response, conversation_id=conversation_id
                    )
        except Exception as err:  # noqa: BLE001 - keep voice pipeline user-friendly
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
                f"Could not reach Hermes Assist bridge: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(
                agent_id=self.entity_id or DOMAIN,
                content=str(reply),
            )
        )
        return conversation.async_get_result_from_chat_log(user_input, chat_log)
