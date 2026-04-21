"""AnythingLLM Conversation agent entity."""

from __future__ import annotations

import html
import logging
import re
from typing import Literal

from homeassistant.components import conversation
from homeassistant.components.conversation import (
    AssistantContent,
    ChatLog,
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
    async_get_chat_log,
)
from homeassistant.components.homeassistant.exposed_entities import async_should_expose
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import ATTR_NAME, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    intent,
    template,
)
from homeassistant.helpers.chat_session import async_get_chat_session
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AnythingLLMConfigEntry
from .const import (
    CONF_ATTACH_USERNAME,
    CONF_WORKSPACE_SLUG,
    CONF_FAILOVER_WORKSPACE_SLUG,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_THREAD_SLUG,
    CONF_FAILOVER_THREAD_SLUG,
    CONF_ENABLE_AGENT_PREFIX,
    CONF_AGENT_KEYWORDS,
    CONF_ENABLE_HEALTH_CHECK,
    DEFAULT_ATTACH_USERNAME,
    DEFAULT_WORKSPACE_SLUG,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_THREAD_SLUG,
    DEFAULT_FAILOVER_THREAD_SLUG,
    DEFAULT_FAILOVER_WORKSPACE_SLUG,
    DEFAULT_ENABLE_AGENT_PREFIX,
    DEFAULT_AGENT_KEYWORDS,
    DEFAULT_ENABLE_HEALTH_CHECK,
    DOMAIN,
    EVENT_CONVERSATION_FINISHED,
)
from .helpers import (
    detect_mode_switch,
    detect_suggested_modes,
    is_mode_query,
    get_mode_name,
    get_mode_prompt,
    get_workspace_prompt,
    get_workspace_prompt_config,
    should_apply_tts_cleaning_for_workspace,
)
from .response_processor import (
    clean_response_for_tts,
    should_continue_conversation,
    QueryResponse,
)

_LOGGER = logging.getLogger(__name__)

# Issue 19: cap conversation-keyed dicts so they don't grow unbounded over months.
_MAX_CONVERSATION_CACHE = 50


def _capped_set(d: dict, key: str, value) -> None:
    """Assign key→value, evicting the oldest entry when over capacity."""
    d[key] = value
    if len(d) > _MAX_CONVERSATION_CACHE:
        del d[next(iter(d))]


# L1: single regex scan for the configured affirmative replies to mode suggestions.
_RE_AFFIRMATIVE = re.compile(
    r'^\s*(?:yes|yeah|yep|sure|ok(?:ay)?|please|go\s+ahead|absolutely|of\s+course|do\s+it|sounds?\s+good)\s*[.!]?\s*$',
    re.IGNORECASE,
)

# L5: maps the lowercase display-name fragment to its mode key, used to detect
# when the LLM's response is asking the user to confirm a mode switch.
_RESPONSE_MODE_HINTS: dict[str, str] = {
    "analysis mode": "analysis",
    "research mode": "research",
    "code review mode": "code_review",
    "troubleshooting mode": "troubleshooting",
    "guest mode": "guest",
    "security mode": "security",
    "default mode": "default",
}
# H2: also strip { and } to prevent Jinja2 expression injection from entity names
# sourced from third-party integrations (Z-Wave, MQTT, cloud bridges).
# Commas are stripped because entity data is embedded in CSV context blocks;
# an unescaped comma in a device name would shift columns for the LLM.
_RE_UNSAFE_PROMPT = re.compile(r'[\r\n\t`|{},]')


def _sanitize_prompt_value(value: str) -> str:
    """Strip control/structural characters from a value before prompt insertion."""
    return _RE_UNSAFE_PROMPT.sub(' ', str(value)).strip()


WORKSPACE_SLUG_ALIASES = {
    "adventure": "adventure",
    "author": "adventure",
    "story": "adventure",
    "creative": "adventure",
    "analysis": "analysis",
    "analyze": "analysis",
    "analyzer": "analysis",
    "research": "research",
    "researcher": "research",
    "visual": "visual",
    "vision": "visual",
    "image": "visual",
    "multimodal": "visual",
    "investigation": "investigation",
    "investigate": "investigation",
    "forensics": "investigation",
    "root-cause": "investigation",
    "rootcause": "investigation",
    "security": "security",
    "secure": "security",
    "alarm": "security",
    "debug": "investigation",
    "troubleshooting": "investigation",
    "troubleshoot": "investigation",
    "code-review": "investigation",
    "code_review": "investigation",
    "code": "investigation",
    "default": "default",
    "normal": "default",
    "standard": "default",
    "jarvis": "default",
    "general": "default",
    "assistant": "default",
    "guest": "default",
    "simple": "default",
    "visitor": "default",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AnythingLLMConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the AnythingLLM Conversation entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "conversation":
            continue

        async_add_entities(
            [AnythingLLMAgentEntity(hass, config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class AnythingLLMAgentEntity(
    ConversationEntity, conversation.AbstractConversationAgent
):
    """AnythingLLM conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(
        self,
        hass: HomeAssistant,
        entry: AnythingLLMConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self.history: dict[str, list[dict]] = {}

        # Mode management - track mode per conversation
        self.conversation_modes: dict[str, str] = {}  # conversation_id -> mode_key

        # Workspace management - track workspace per conversation
        self.conversation_workspaces: dict[str, str] = {}  # conversation_id -> workspace_slug
        self.conversation_threads: dict[str, str | None] = {}  # conversation_id -> thread_slug override

        # Issue 7: restore state from hass.data so reloading the integration
        # doesn't silently reset every user's mode/workspace.
        _saved = hass.data.get(f"{DOMAIN}_state_{subentry.subentry_id}", {})
        if _saved:
            self.conversation_modes.update(_saved.get("modes", {}))
            self.conversation_workspaces.update(_saved.get("workspaces", {}))
            self.conversation_threads.update(_saved.get("threads", {}))
            _LOGGER.debug(
                "Restored conversation state for subentry %s: modes=%s workspaces=%s",
                subentry.subentry_id,
                self.conversation_modes,
                self.conversation_workspaces,
            )

        self.options = subentry.data
        self._attr_unique_id = subentry.subentry_id
        
        # Caching for performance optimization
        # NOTE: Only entity list is cached; system prompt is NOT cached because it
        # embeds live entity states and would return stale data after state changes.
        self._exposed_entities_cache: list[dict[str, any]] | None = None
        self._last_states_hash: int = 0

        # L1: cache compiled agent-keyword regex; invalidated when options change.
        self._agent_keywords_str: str | None = None
        self._agent_keywords_regex: re.Pattern | None = None

        # L5: pending mode suggestion per conversation (LLM asked; user hasn't confirmed yet).
        self._pending_mode_suggestions: dict[str, str] = {}

        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="AnythingLLM",
            model=self.options.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG),
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        self.client = entry.runtime_data
        # Register entity reference so reset_thread service can look it up by subentry_id.
        hass.data[f"{DOMAIN}_entity_{subentry.subentry_id}"] = self

    async def async_will_remove_from_hass(self) -> None:
        """Clean up entity reference when removed."""
        self.hass.data.pop(f"{DOMAIN}_entity_{self._attr_unique_id}", None)

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Process a sentence."""
        with (
            async_get_chat_session(self.hass, user_input.conversation_id) as session,
            async_get_chat_log(self.hass, session, user_input) as chat_log,
        ):
            return await self._async_handle_message(user_input, chat_log)

    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log: ChatLog,
    ) -> ConversationResult:
        """Call the API."""
        conversation_id = chat_log.conversation_id
        
        # Check for workspace switch command
        workspace_switch_result = self._check_workspace_switch(user_input.text, conversation_id, user_input.language)
        if workspace_switch_result:
            return workspace_switch_result

        current_workspace = self._get_active_workspace(conversation_id)
        
        # Check for mode query first
        if is_mode_query(user_input.text):
            mode_name = get_mode_name(current_workspace)
            _LOGGER.debug("Mode/workspace query detected, current workspace: %s", mode_name)
            
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(f"I'm currently in {mode_name}.")
            
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )
        
        # L5: if the previous response suggested a workspace switch and this reply
        # is affirmative, apply the pending switch without an extra API call.
        pending_mode = self._pending_mode_suggestions.pop(conversation_id, None)
        if pending_mode and _RE_AFFIRMATIVE.match(user_input.text):
            old_workspace = current_workspace
            _capped_set(self.conversation_workspaces, conversation_id, pending_mode)
            mode_name = get_mode_name(pending_mode)
            if conversation_id in self.history:
                del self.history[conversation_id]
            if conversation_id in self.conversation_threads:
                del self.conversation_threads[conversation_id]
            self._save_state()
            _LOGGER.info(
                "Workspace switched (via suggestion confirmation) from %s to %s for conversation %s",
                old_workspace,
                pending_mode,
                conversation_id,
            )
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(
                f"Switching to {mode_name}. How can I help you?"
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        # Determine workspace and thread BEFORE building the system message so we
        # can skip the (expensive) template render when a thread is active —
        # thread endpoints manage context server-side and ignore the system prompt.
        active_workspace = self.conversation_workspaces.get(conversation_id)
        default_workspace = self._default_workspace_slug()

        if active_workspace and active_workspace != default_workspace:
            active_thread = None
            _LOGGER.info(
                "Using custom workspace '%s' for conversation %s (built-in thread)",
                active_workspace,
                conversation_id,
            )
        else:
            active_workspace = default_workspace
            active_thread = self.options.get(CONF_THREAD_SLUG, DEFAULT_THREAD_SLUG)
            _LOGGER.info(
                "Using default workspace '%s' for conversation %s (thread: %s)",
                active_workspace,
                conversation_id,
                active_thread or "None",
            )

        exposed_entities = self.get_exposed_entities()
        apply_tts_cleaning = should_apply_tts_cleaning_for_workspace(active_workspace)

        if conversation_id in self.history:
            messages = self.history[conversation_id]
        else:
            if active_thread:
                # Thread mode: AnythingLLM manages history server-side; no system
                # prompt is sent, so there is nothing to render.
                messages = []
            else:
                user_input.conversation_id = conversation_id
                try:
                    system_message, apply_tts_cleaning = self._generate_system_message(
                        exposed_entities,
                        user_input,
                        "default",
                        active_workspace,
                    )
                except TemplateError as err:
                    _LOGGER.error("Error rendering prompt: %s", err)
                    intent_response = intent.IntentResponse(language=user_input.language)
                    intent_response.async_set_error(
                        intent.IntentResponseErrorCode.UNKNOWN,
                        f"Sorry, I had a problem with my template: {err}",
                    )
                    return conversation.ConversationResult(
                        response=intent_response, conversation_id=conversation_id
                    )
                messages = [system_message] if system_message is not None else []

        # Add @agent prefix if enabled and keywords detected
        user_content = user_input.text
        if self._should_use_agent_prefix(user_content):
            user_content = f"@agent {user_content}"
            _LOGGER.debug("Added @agent prefix to message: %s", user_content)

        user_message = {"role": "user", "content": user_content}
        if self.options.get(CONF_ATTACH_USERNAME, DEFAULT_ATTACH_USERNAME):
            uid = user_input.context.user_id
            if uid is not None:
                # H4: resolve UUID to display name; raw user_id is an opaque UUID
                # that is meaningless to AnythingLLM.
                ha_user = await self.hass.auth.async_get_user(uid)
                if ha_user is not None:
                    user_message[ATTR_NAME] = ha_user.name

        messages.append(user_message)

        try:
            query_response = await self.query(
                user_input, messages, active_workspace, active_thread, apply_tts_cleaning
            )
        except Exception as err:
            _LOGGER.error(err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I had a problem talking to the API: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        # When a thread slug is active, AnythingLLM manages conversation history
        # server-side. Accumulating a local copy wastes memory and is never used
        # (only messages[-1] is ever sent as the "message" field). Skip history
        # storage for thread-based conversations; only keep it for workspace-only
        # (no thread) mode where we pass the messages array ourselves.
        using_thread = bool(active_thread)
        if not using_thread:
            assistant_message = {"role": "assistant", "content": query_response.text}
            messages.append(assistant_message)
            self.history[conversation_id] = messages
        elif conversation_id in self.history:
            # Clean up any stale history if we've switched to thread mode
            del self.history[conversation_id]

        # L5: if response contains a mode-switch question, store the suggested mode
        # so the next affirmative reply can trigger the switch without an extra API call.
        if '?' in query_response.text:
            text_lower = query_response.text.lower()
            for _hint_name, _hint_key in _RESPONSE_MODE_HINTS.items():
                if _hint_name in text_lower and _hint_key != current_mode:
                    _capped_set(self._pending_mode_suggestions, conversation_id, _hint_key)
                    _LOGGER.debug(
                        "Pending mode suggestion stored: %s for conversation %s",
                        _hint_key,
                        conversation_id,
                    )
                    break

        self.hass.bus.async_fire(
            EVENT_CONVERSATION_FINISHED,
            {
                "response": query_response.response,
                "user_input": user_input,
                "agent_id": self.subentry.subentry_id,
            },
        )

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(query_response.text)

        # Issue 6: Write assistant response to HA ChatLog so conversation
        # history appears in the HA UI. The user turn is already logged
        # automatically by async_get_chat_log when user_input is provided.
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(agent_id=self.entity_id, content=query_response.text)
        )

        # Detect if LLM is asking a follow-up question to enable continued conversation
        should_continue = should_continue_conversation(query_response.text)

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=conversation_id,
            continue_conversation=should_continue,
        )

    def _check_workspace_switch(
        self, user_text: str, conversation_id: str, language: str
    ) -> conversation.ConversationResult | None:
        """Check if user is requesting a workspace switch.
        
        Supports commands like:
        - !workspace finance            → Switch to finance workspace
        - switch to finance workspace   → Switch to finance workspace
        - use technical workspace       → Switch to technical-support workspace
        - !workspace default            → Return to primary configured workspace
        - switch to default workspace   → Return to primary configured workspace
        - !workspace                    → Show current workspace
        - what workspace                → Show current workspace
        """
        text_lower = user_text.lower().strip()
        
        # Check for workspace query - support various natural language patterns
        workspace_query_patterns = [
            "!workspace",
            "what workspace",
            "current workspace", 
            "which workspace",
            "what workspace are you in",
            "what workspace am i in",
            "which workspace are you in",
            "which workspace am i in",
            "what workspace are you using",
            "what workspace am i using",
        ]
        
        # Also check if the text contains key phrases
        is_workspace_query = (
            text_lower in workspace_query_patterns or
            text_lower.startswith("what workspace") or
            text_lower.startswith("which workspace") or
            (text_lower.startswith("current") and "workspace" in text_lower)
        )
        
        if is_workspace_query and not any(
            text_lower.startswith(p) for p in ["switch to", "use ", "change workspace to", "switch workspace to"]
        ):
            current_workspace = self.conversation_workspaces.get(conversation_id)
            if current_workspace:
                response_text = f"Currently using workspace: {current_workspace}"
            else:
                # Get default workspace
                workspace_slug = self._default_workspace_slug()
                response_text = f"Using default workspace: {workspace_slug}"
            
            intent_response = intent.IntentResponse(language=language)
            intent_response.async_set_speech(response_text)
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )
        
        # Extract workspace name from various command patterns
        new_workspace = None
        
        # Pattern 1: "!workspace <name>"
        if text_lower.startswith("!workspace "):
            new_workspace = user_text.split(" ", 1)[1].strip()
        
        # Pattern 2: "switch to <name> workspace"
        elif text_lower.startswith("switch to ") and " workspace" in text_lower:
            # Extract workspace name between "switch to" and "workspace"
            parts = text_lower.replace("switch to ", "").replace(" workspace", "").strip()
            new_workspace = parts
        
        # Pattern 3: "use <name> workspace"
        elif text_lower.startswith("use ") and " workspace" in text_lower:
            # Extract workspace name between "use" and "workspace"
            parts = text_lower.replace("use ", "").replace(" workspace", "").strip()
            new_workspace = parts
        
        # Pattern 4: "change workspace to <name>"
        elif text_lower.startswith("change workspace to "):
            new_workspace = text_lower.replace("change workspace to ", "").strip()
        
        # Pattern 5: "switch workspace to <name>"
        elif text_lower.startswith("switch workspace to "):
            new_workspace = text_lower.replace("switch workspace to ", "").strip()

        # Pattern 6: "switch to <name> mode"
        elif text_lower.startswith("switch to ") and " mode" in text_lower:
            parts = text_lower.replace("switch to ", "").replace(" mode", "").strip()
            new_workspace = parts

        # Pattern 7: "use <name> mode"
        elif text_lower.startswith("use ") and " mode" in text_lower:
            parts = text_lower.replace("use ", "").replace(" mode", "").strip()
            new_workspace = parts

        # Pattern 8: "change mode to <name>"
        elif text_lower.startswith("change mode to "):
            new_workspace = text_lower.replace("change mode to ", "").strip()

        # Pattern 9: "switch mode to <name>"
        elif text_lower.startswith("switch mode to "):
            new_workspace = text_lower.replace("switch mode to ", "").strip()

        # Backwards-compatible mode detection ("analysis mode", "research mode", etc.)
        elif text_lower.endswith("mode"):
            inferred_workspace = detect_mode_switch(text_lower)
            if inferred_workspace:
                new_workspace = inferred_workspace
        
        # If we found a workspace switch request
        if new_workspace:
            # Sanitize workspace name: strip surrounding whitespace/punctuation,
            # normalize spaces to hyphens, and lowercase. This prevents trailing
            # punctuation from voice input (e.g. "finance.") from becoming part
            # of the workspace slug used for API calls.
            new_workspace = new_workspace.strip().lower()
            # Replace ALL characters that are not letters, digits, underscore, or hyphen
            # with hyphens. Prevents path traversal via slug interpolated into the URL.
            new_workspace = re.sub(r'[^a-z0-9_-]', '-', new_workspace)
            # Collapse repeated hyphens and strip leading/trailing hyphens
            new_workspace = re.sub(r'-+', '-', new_workspace).strip('-')
            # Normalize common spoken aliases to canonical workspace slugs.
            # If exact match fails (e.g. "the-analysis" from "switch to the analysis workspace"),
            # scan for any known alias as a substring, longest first to avoid partial matches.
            if new_workspace in WORKSPACE_SLUG_ALIASES:
                new_workspace = WORKSPACE_SLUG_ALIASES[new_workspace]
            else:
                for alias in sorted(WORKSPACE_SLUG_ALIASES, key=len, reverse=True):
                    if alias in new_workspace:
                        new_workspace = WORKSPACE_SLUG_ALIASES[alias]
                        break
            new_workspace_lower = new_workspace
            
            # Handle "default" keyword to return to primary workspace
            if new_workspace_lower == "default":
                # Clear the workspace override to return to configured default
                if conversation_id in self.conversation_workspaces:
                    del self.conversation_workspaces[conversation_id]

                # Clear the thread override to restore configured thread
                if conversation_id in self.conversation_threads:
                    del self.conversation_threads[conversation_id]

                # Clear history when switching workspaces (different context)
                if conversation_id in self.history:
                    del self.history[conversation_id]

                self._save_state()

                # Get the actual default workspace name
                default_workspace = self._default_workspace_slug()

                _LOGGER.info(
                    "Workspace reset to default (%s) for conversation %s",
                    default_workspace,
                    conversation_id,
                )
                
                intent_response = intent.IntentResponse(language=language)
                intent_response.async_set_speech(
                    f"Switched to workspace {default_workspace}. How can I help you?"
                )
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=conversation_id
                )
            
            # Validate workspace slug format (basic validation)
            if not new_workspace or len(new_workspace) < 1:
                intent_response = intent.IntentResponse(language=language)
                intent_response.async_set_speech("Please provide a valid workspace slug.")
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=conversation_id
                )
            
            # Store the new workspace for this conversation
            old_workspace = self.conversation_workspaces.get(conversation_id, "default")
            _capped_set(self.conversation_workspaces, conversation_id, new_workspace)

            # Clear thread override - new workspace uses its configured default.
            if conversation_id in self.conversation_threads:
                del self.conversation_threads[conversation_id]

            # Clear history when switching workspaces (different context)
            if conversation_id in self.history:
                del self.history[conversation_id]

            self._save_state()
            _LOGGER.info(
                "Workspace switched from %s to %s for conversation %s (stored in conversation_workspaces dict)",
                old_workspace,
                new_workspace,
                conversation_id,
            )
            _LOGGER.debug("conversation_workspaces state: %s", self.conversation_workspaces)
            
            intent_response = intent.IntentResponse(language=language)
            intent_response.async_set_speech(
                f"Switched to workspace {new_workspace}. How can I help you?"
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )
        
        return None

    def _get_default_workspace(self) -> str:
        """Get the configured default workspace slug."""
        opt_workspace_slug = self.options.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
        data_workspace_slug = self.entry.data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
        return opt_workspace_slug if opt_workspace_slug != DEFAULT_WORKSPACE_SLUG else data_workspace_slug

    def _get_active_workspace(self, conversation_id: str) -> str:
        """Get currently active workspace slug for this conversation."""
        return self.conversation_workspaces.get(conversation_id, self._get_default_workspace())

    def _should_use_agent_prefix(self, user_text: str) -> bool:
        """Determine if @agent prefix should be added based on keywords."""
        if not self.options.get(CONF_ENABLE_AGENT_PREFIX, DEFAULT_ENABLE_AGENT_PREFIX):
            return False

        keywords_str = self.options.get(CONF_AGENT_KEYWORDS, DEFAULT_AGENT_KEYWORDS)
        # Recompile only when the keyword string changes (e.g. after options update).
        if keywords_str != self._agent_keywords_str:
            keywords = [kw.strip().lower() for kw in keywords_str.split(",") if kw.strip()]
            if keywords:
                self._agent_keywords_regex = re.compile(
                    r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b',
                    re.IGNORECASE,
                )
            else:
                self._agent_keywords_regex = None
            self._agent_keywords_str = keywords_str

        return bool(self._agent_keywords_regex and self._agent_keywords_regex.search(user_text))

    def _save_state(self) -> None:
        """Persist conversation state to hass.data.

        Survives integration reloads (hass.data is in-memory on the hass object
        and outlives individual config entries). Does not survive full HA restarts —
        use HA Store for that if needed in the future.
        """
        self.hass.data[f"{DOMAIN}_state_{self._attr_unique_id}"] = {
            "modes": dict(self.conversation_modes),
            "workspaces": dict(self.conversation_workspaces),
            "threads": dict(self.conversation_threads),
        }

    def reset_threads(self, conversation_id: str | None = None) -> None:
        """Clear thread slug overrides.

        If conversation_id is given, only that conversation's thread is cleared.
        Otherwise all thread overrides are removed.
        """
        if conversation_id:
            self.conversation_threads.pop(conversation_id, None)
            _LOGGER.info("Reset thread for conversation %s", conversation_id)
        else:
            self.conversation_threads.clear()
            _LOGGER.info("Reset all threads for subentry %s", self._attr_unique_id)
        self._save_state()

    def _default_workspace_slug(self) -> str:
        """Return the effective workspace slug for this agent.

        Prefers the subentry option value; falls back to the main entry data
        when the option is still set to the placeholder DEFAULT_WORKSPACE_SLUG.
        """
        opt = self.options.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)
        if opt != DEFAULT_WORKSPACE_SLUG:
            return opt
        return self.entry.data.get(CONF_WORKSPACE_SLUG, DEFAULT_WORKSPACE_SLUG)

    def _generate_system_message(
        self,
        exposed_entities,
        user_input: conversation.ConversationInput,
        mode_key: str = "default",
        workspace_slug: str | None = None,
    ):
        apply_tts_cleaning = should_apply_tts_cleaning_for_workspace(workspace_slug)
        workspace_config = get_workspace_prompt_config(workspace_slug)

        if workspace_config is not None:
            raw_prompt = workspace_config.get("system_prompt")
            if raw_prompt is None:
                # Known workspace with no context block — AnythingLLM owns the full prompt.
                # Do not send a prompt override; let the workspace system prompt apply natively.
                return None, apply_tts_cleaning
        else:
            # Unknown/unconfigured workspace — fall back to legacy mode system.
            user_prompt = self.options.get(CONF_PROMPT, DEFAULT_PROMPT)
            if user_prompt != DEFAULT_PROMPT:
                raw_prompt = get_mode_prompt(mode_key, custom_base_persona=user_prompt)
            else:
                raw_prompt = get_mode_prompt(mode_key)
        
        # Render the Jinja2 template first, then append any mode-suggestion hint
        # AFTER rendering so display names can't accidentally contain Jinja2 syntax.
        prompt = self._async_generate_prompt(raw_prompt, exposed_entities, user_input, mode_key, workspace_slug)
        
        # Detect if query patterns suggest a different workspace might be helpful
        suggestion_context = workspace_slug or mode_key
        suggested_modes = detect_suggested_modes(user_input.text, suggestion_context)
        if suggested_modes:
            mode_names = ", ".join([get_mode_name(m) for m in suggested_modes[:2]])
            prompt = prompt + f"\n\n[SYSTEM HINT: User query patterns suggest {mode_names} might be relevant for this question. Consider offering to switch workspace if appropriate.]"
            _LOGGER.debug("Pattern match detected - suggesting modes: %s", mode_names)
        
        return {"role": "system", "content": prompt}, apply_tts_cleaning

    def _async_generate_prompt(
        self,
        raw_prompt: str,
        exposed_entities,
        user_input: conversation.ConversationInput,
        mode_key: str = "default",
        workspace_slug: str | None = None,
    ) -> str:
        """Generate a prompt for the user."""
        # Prompt is rendered fresh every call — it embeds live entity states so
        # caching it would return stale device states to the LLM.
        return template.Template(raw_prompt, self.hass).async_render(
            {
                "ha_name": self.hass.config.location_name,
                "exposed_entities": exposed_entities,
                "current_device_id": user_input.device_id,
            },
            parse_result=False,
        )

    def get_exposed_entities(self) -> list[dict[str, any]]:
        # Compute exposed states once — used for both cache invalidation and building
        states = [
            state
            for state in self.hass.states.async_all()
            if async_should_expose(self.hass, conversation.DOMAIN, state.entity_id)
        ]

        # Invalidate cache when any exposed entity's state VALUE changes (not just count).
        # The old count-only check missed state changes (e.g. a light turning on/off)
        # which caused the LLM to report stale device states.
        current_hash = hash(tuple((s.entity_id, s.state) for s in states))
        if current_hash != self._last_states_hash:
            self._exposed_entities_cache = None
            self._last_states_hash = current_hash
            _LOGGER.debug("Entity cache invalidated due to state change")

        # Return cached entities if available
        if self._exposed_entities_cache is not None:
            return self._exposed_entities_cache

        # Build fresh entity list
        # Issue 20: fetch the backing dict once and do O(1) dict lookups per entity
        # instead of calling async_get() (a method with lookup overhead) N times.
        reg_entries = er.async_get(self.hass).entities
        exposed_entities = []
        for state in states:
            entity_id = state.entity_id
            entity = reg_entries.get(entity_id)
            # Issue 12: sanitize name/state/aliases before they're embedded in the
            # system prompt CSV. A device named with newlines or backtick characters
            # could escape the CSV context and inject prompt instructions.
            raw_aliases = entity.aliases if entity and entity.aliases else []
            exposed_entities.append(
                {
                    "entity_id": _sanitize_prompt_value(entity_id),
                    "name": _sanitize_prompt_value(state.name),
                    "state": _sanitize_prompt_value(state.state),
                    "aliases": [_sanitize_prompt_value(a) for a in raw_aliases],
                }
            )

        self._exposed_entities_cache = exposed_entities
        _LOGGER.debug("Cached %d exposed entities", len(exposed_entities))
        return exposed_entities

    async def query(
        self,
        user_input: conversation.ConversationInput,
        messages: list[dict],
        workspace_override: str | None = None,
        thread_override: str | None | bool = False,
        apply_tts_cleaning: bool = True,
    ) -> QueryResponse:
        """Process a sentence."""
        # Use workspace override if provided (from conversation-specific workspace)
        if workspace_override:
            workspace_slug = workspace_override
            _LOGGER.info("Using workspace override: %s", workspace_override)
        else:
            # Prefer subentry options values; if default placeholders are present, fall back to main entry data
            workspace_slug = self._default_workspace_slug()
            _LOGGER.debug("Using default workspace (no override): %s", workspace_slug)
        
        max_tokens = self.options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)
        temperature = self.options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        
        # Handle thread override: False = use configured, None = use workspace default, string = use that thread
        if thread_override is False:
            # No override specified - use configured thread
            thread_slug = self.options.get(CONF_THREAD_SLUG, DEFAULT_THREAD_SLUG)
        elif thread_override is None:
            # Explicit None - don't use any thread (workspace default)
            thread_slug = None
        else:
            # String value - use that specific thread
            thread_slug = thread_override
        
        failover_thread_slug = self.options.get(CONF_FAILOVER_THREAD_SLUG, DEFAULT_FAILOVER_THREAD_SLUG)
        opt_failover_workspace_slug = self.options.get(CONF_FAILOVER_WORKSPACE_SLUG, DEFAULT_FAILOVER_WORKSPACE_SLUG)
        data_failover_workspace_slug = self.entry.data.get(CONF_FAILOVER_WORKSPACE_SLUG, DEFAULT_FAILOVER_WORKSPACE_SLUG)
        failover_workspace_slug = opt_failover_workspace_slug or data_failover_workspace_slug

        _LOGGER.info("Sending request to AnythingLLM workspace '%s' with %d messages", workspace_slug, len(messages))

        # Call AnythingLLM API
        try:
            response = await self.client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                workspace_slug=workspace_slug if workspace_slug else None,
                thread_slug=thread_slug if thread_slug else None,
                failover_thread_slug=failover_thread_slug if failover_thread_slug else None,
                failover_workspace_slug=failover_workspace_slug if failover_workspace_slug else None,
            )
        except Exception as err:
            _LOGGER.error("Error from AnythingLLM: %s", err)
            raise

        _LOGGER.debug("Received response from AnythingLLM (type: %s)", response.get("type", "unknown"))

        # Extract the text response from AnythingLLM
        # AnythingLLM returns: {"textResponse": "...", "type": "chat", ...}
        # Some versions/agent modes return "text" instead of "textResponse"
        text_response = response.get("textResponse") or response.get("text", "")

        if not text_response:
            _LOGGER.error(
                "Empty response from AnythingLLM. Full response payload: %s", response
            )
            raise HomeAssistantError("Empty response from AnythingLLM")

        # Only apply strict TTS cleanup in the default/JARVIS workspace.
        if apply_tts_cleaning:
            text_response = clean_response_for_tts(text_response)

        return QueryResponse(response=response, text=text_response)
